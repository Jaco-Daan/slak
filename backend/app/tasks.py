"""Celery tasks — long-running simulation work goes here (spec 1.2)."""

import base64
import os
import tempfile

from .celery_app import celery_app
from .schemas import SimulationPayload
from .parser import parse, transform_titles, extract_genetic_traits, extract_death_reasons
from .simulation import run_simulation
from .output import package_zip


# Where the worker writes the resulting ZIPs. In production this would be S3.
RESULTS_DIR = os.environ.get("RESULTS_DIR", tempfile.gettempdir())


@celery_app.task(bind=True, name="run_generation")
def run_generation(self, payload_json: dict) -> dict:
    """Parse → simulate → render → ZIP. Returns {zip_path, stats}."""
    payload = SimulationPayload(**payload_json)

    def log(msg: str) -> None:
        self.update_state(state="PROGRESS", meta={"message": msg})

    log("Parsing titles...")
    titles_ast = parse(payload.parsed_files.titles_txt or "")
    titles = transform_titles(titles_ast)

    log("Parsing traits...")
    traits_ast = parse(payload.parsed_files.traits_txt or "")
    traits = extract_genetic_traits(traits_ast)

    log("Parsing deaths...")
    deaths_ast = parse(payload.parsed_files.deaths_txt or "")
    deaths = extract_death_reasons(deaths_ast)

    log(f"Starting simulation ({payload.global_settings.start_year} → {payload.global_settings.end_year})...")
    world = run_simulation(
        payload, traits, deaths, titles, logger=log,
    )

    log("Packaging ZIP...")
    zip_bytes = package_zip(world)
    out_path = os.path.join(RESULTS_DIR, f"history_{self.request.id}.zip")
    with open(out_path, "wb") as f:
        f.write(zip_bytes)

    log("Done.")
    return {
        "zip_path": out_path,
        "characters": len(world.characters),
        "titles_with_history": len(world.title_holders),
        # Inline (small) — frontend can also fetch via /download/{task_id}
        "zip_b64": base64.b64encode(zip_bytes).decode("ascii"),
    }
