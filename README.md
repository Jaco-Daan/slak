# CK3 Character History Generator

Procedural multi-generational character & title history generator for *Crusader
Kings III* total conversion mods. Implements spec **v7.0** (`Jis.pdf`) end-to-end.

## Architecture

| Layer    | Stack                                                      |
| -------- | ---------------------------------------------------------- |
| Frontend | React + Vite, Tailwind CSS (monochrome), Zustand state     |
| API      | FastAPI (file uploads, /generate, /status, /download)      |
| Worker   | Celery + Redis (long-running simulation off the request)   |
| Output   | Custom Paradox AST parser → simulation engine → ZIP bundle |

## Quick start

### Docker (recommended)

```bash
docker compose up --build
```

Open <http://localhost:5173>. Backend at <http://localhost:8000>.

### Local dev

Backend (Python 3.11+, Redis on `localhost:6379`):

```bash
cd backend
pip install -r requirements.txt
celery -A app.celery_app.celery_app worker --loglevel=info &
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Trying it out

The `samples/` directory has working CK3-format input files:

* `landed_titles.txt` — empire/kingdom/duchy hierarchy plus a titular hegemony
* `genetic_traits.txt` — courage/beauty/health groups w/ multiple tiers
* `death_reasons.txt` — natural + hostile + trait-triggered (`sickly` → plague)
* `name_lists.txt` — culture-specific name pools

Drop them into the four sidebar dropzones, drag dynasty blocks onto the Title
Histories Gantt chart, click **Generate Simulation**, and watch the worker log
stream in the right drawer. The download button delivers a ZIP with
`character_history.txt` and `title_history.txt` in exact CK3 syntax.

## Spec coverage

* **Ch. 1** — Cloud architecture: FastAPI dispatches to Celery worker via Redis
  broker; frontend polls `/status`; final ZIP at `/download/{task_id}`.
* **Ch. 2** — Three-column SPA: left sidebar (dropzones + nav + Generate),
  center contextual editor, right drawer with mock terminal log. Strict
  monochrome Tailwind palette.
* **Ch. 3** — Single Zustand store (`src/store.js`) with the exact categories
  from the spec; serialized to JSON at submission time. `onChange` drives state
  directly without per-field save buttons.
* **Ch. 4** — Pydantic schemas in `backend/app/schemas.py` (Character, etc.).
* **Ch. 5** — AST compiler (`backend/app/parser.py`):
  * Comment stripping, brace/equals padding, quote-preserving split.
  * Recursive parser with state stack.
  * Duplicate-key edge case → list collapse.
  * Title hierarchy classifier honoring `h_/e_/k_/d_/c_/b_` prefixes.
  * Hegemony titular-vs-landed dynamic classification.
  * `metadata` bundling for non-title keys.
  * Trait filter (`genetic = yes` only); `natural_death_trigger.has_trait`
    extraction.
* **Ch. 6** — Genetics engine: parent trait evaluation w/ opposites cancellation,
  active inheritance (80%/20%), passive (50%/10%), spontaneous mutation against
  `random_creation`. Mortality: exponential age curve + per-event multipliers.
* **Ch. 7** — Title transitions:
  * Marriage: forced heir + spouse from House B; child forced into House B.
  * Usurpation: hostile death w/ `killer_id`; family displacement via
    `employer_id` to a culture/faith-friendly ruler.
  * Extinction: fertility forced to 0; distant claim transfers on death.
  * **Cascading inheritance**: high-tier sequences propagate to children unless
    explicitly overridden (`cascade_sequences()`).
* **Ch. 8** — Interactive Gantt chart: y-axis title hierarchy with collapse,
  x-axis scrollable years, draggable resize handles on dynasty blocks, clickable
  transition-boundary nodes opening a transition-type popover.
* **Ch. 9** — Output formatter (`backend/app/output.py`) emits
  `character_history.txt` and `title_history.txt` matching the spec's exact
  syntax templates: conditional `female`/`killer`/`employer` blocks, sequential
  `YYYY.M.D = { holder = ... }` entries.

## Repo layout

```
backend/
  app/
    main.py          FastAPI endpoints
    celery_app.py    Celery config
    tasks.py         run_generation worker task
    parser.py        Paradox AST compiler (ch. 5)
    schemas.py       Pydantic models (ch. 4)
    genetics.py      Inheritance algorithm (ch. 6.1)
    mortality.py     Death-roll & reason picker (ch. 6.2)
    simulation.py    Year tick loop + transitions (ch. 7)
    output.py        Paradox-script writer (ch. 9)
frontend/
  src/
    App.jsx
    store.js                 Zustand single source of truth
    api.js                   Backend client
    components/
      LeftSidebar.jsx        Dropzones + nav + Generate button
      CenterWorkspace.jsx    View router
      RightDrawer.jsx        Polled task log + download
      Dropzone.jsx
      GanttChart.jsx         Interactive Gantt for title sequences
      views/
        GlobalSettings.jsx
        LifeCycleModifiers.jsx
        NegativeEvents.jsx
        TitleHistories.jsx
samples/
  landed_titles.txt  genetic_traits.txt  death_reasons.txt  name_lists.txt
docker-compose.yml
```

## Explicitly omitted (per spec mandate)

* Culling, cadet branches, dynamic nicknames, 3D DNA strings — left out to
  preserve project scope and server performance, as instructed in the
  Implementation Mandate on page 1 of the spec.
