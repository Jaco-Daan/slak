"""Main chronological simulation loop and title-transition orchestration.

Implements:
  * Annual tick: aging, mortality, fertility (children), succession
  * Title transitions per chapter 7 (marriage, usurpation, extinction)
  * Cascade rule for high-tier dynasty sequences
"""

from __future__ import annotations
import random
import uuid
from typing import Callable, Optional

from .schemas import (
    Character,
    NegativeEvent,
    SimulationPayload,
    DynastySequence,
    LifeCycleModifiers,
)
from .genetics import inherit_traits, roll_birth_traits
from .mortality import annual_death_check, pick_hostile_death


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _new_id(prefix: str = "char") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _date(year: int, month: int = 1, day: int = 1) -> str:
    return f"{year}.{month}.{day}"


def _age(character: Character, year: int) -> int:
    return year - int(character.birth_date.split(".")[0])


def _pick_name(culture: str, is_female: bool, name_lists: dict, rng: random.Random) -> str:
    key_options = [
        f"{culture}_{'female' if is_female else 'male'}",
        culture,
        "default_female" if is_female else "default_male",
        "default",
    ]
    for k in key_options:
        if k in name_lists and name_lists[k]:
            return rng.choice(name_lists[k])
    return "Unnamed"


# ---------------------------------------------------------------------------
# WorldState
# ---------------------------------------------------------------------------

class WorldState:
    """Holds every character ever created plus the holder timelines for titles."""

    def __init__(self, payload: SimulationPayload, rng: random.Random,
                 logger: Callable[[str], None] = lambda _: None):
        self.payload = payload
        self.rng = rng
        self.log = logger
        self.characters: dict[str, Character] = {}
        # title_id -> list of (date_str, holder_char_id)
        self.title_holders: dict[str, list[tuple[str, str]]] = {}
        # title_id -> currently-active dynasty ID (house key)
        self.current_dynasty: dict[str, str] = {}

        # Parsed registries (populated from payload.parsed_files)
        self.traits_registry: list[dict] = []
        self.deaths_registry: list[dict] = []
        self.titles: dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Character creation
    # ------------------------------------------------------------------

    def make_character(
        self,
        *,
        dynasty: str,
        culture: str,
        religion: str,
        is_female: bool,
        birth_year: int,
        father_id: Optional[str] = None,
        mother_id: Optional[str] = None,
    ) -> Character:
        traits: list[str]
        if father_id and mother_id:
            father = self.characters[father_id]
            mother = self.characters[mother_id]
            traits = inherit_traits(
                mother.traits, father.traits, self.traits_registry, self.rng
            )
        else:
            traits = roll_birth_traits(self.traits_registry, self.rng)

        cid = _new_id()
        name = _pick_name(culture, is_female, self.payload.parsed_files.name_lists, self.rng)
        # Random birth month/day for variety
        char = Character(
            id=cid,
            name=name,
            dynasty_house=dynasty,
            culture=culture,
            religion=religion,
            is_female=is_female,
            father_id=father_id,
            mother_id=mother_id,
            traits=traits,
            birth_date=_date(birth_year, self.rng.randint(1, 12), self.rng.randint(1, 28)),
        )
        self.characters[cid] = char

        # Wire up parent.children
        if father_id:
            self.characters[father_id].child_ids.append(cid)
        if mother_id:
            self.characters[mother_id].child_ids.append(cid)
        return char

    def kill(self, character: Character, year: int, reason: str, killer_id: Optional[str] = None) -> None:
        if not character.is_alive:
            return
        character.is_alive = False
        character.death_date = _date(year, self.rng.randint(1, 12), self.rng.randint(1, 28))
        character.death_reason = reason
        character.killer_id = killer_id

    # ------------------------------------------------------------------
    # Marriage / fertility helpers
    # ------------------------------------------------------------------

    def marry(self, a: Character, b: Character) -> None:
        if b.id not in a.spouse_ids:
            a.spouse_ids.append(b.id)
        if a.id not in b.spouse_ids:
            b.spouse_ids.append(a.id)

    def find_eligible_spouse(
        self,
        for_character: Character,
        from_dynasty: Optional[str],
        year: int,
        modifiers: LifeCycleModifiers,
    ) -> Optional[Character]:
        candidates: list[Character] = []
        for c in self.characters.values():
            if not c.is_alive:
                continue
            if c.id == for_character.id:
                continue
            if c.is_female == for_character.is_female:
                continue
            if c.spouse_ids:
                continue
            age = _age(c, year)
            if age < 16 or age > 50:
                continue
            target_age = _age(for_character, year)
            if abs(age - target_age) > modifiers.max_age_difference_between_partners:
                continue
            if from_dynasty and c.dynasty_house != from_dynasty:
                continue
            candidates.append(c)
        if not candidates:
            return None
        return self.rng.choice(candidates)


# ---------------------------------------------------------------------------
# Title sequence cascade (spec ch. 7)
# ---------------------------------------------------------------------------

def cascade_sequences(
    titles: dict[str, dict],
    user_sequences: dict[str, list[DynastySequence]],
) -> dict[str, list[DynastySequence]]:
    """Propagate parent-tier sequences to children unless overridden.

    Walks the recursive title tree depth-first; any child without an explicit
    sequence inherits the nearest ancestor's.
    """
    resolved: dict[str, list[DynastySequence]] = {}

    def walk(node: dict, inherited: list[DynastySequence] | None) -> None:
        tid = node.get("id")
        if tid is None:
            for c in node.get("children", {}).values():
                walk(c, inherited)
            return

        if tid in user_sequences:
            current = user_sequences[tid]
        else:
            current = inherited

        if current:
            resolved[tid] = current

        for c in node.get("children", {}).values():
            walk(c, current)

    # `titles` is the dict of top-level titles produced by transform_titles()
    walk({"id": None, "children": titles}, None)
    return resolved


# ---------------------------------------------------------------------------
# Main simulation loop
# ---------------------------------------------------------------------------

def run_simulation(
    payload: SimulationPayload,
    traits_registry: list[dict],
    deaths_registry: list[dict],
    titles: dict[str, dict],
    seed: int = 1337,
    logger: Callable[[str], None] = lambda _: None,
) -> WorldState:
    rng = random.Random(seed)
    world = WorldState(payload, rng, logger)
    world.traits_registry = traits_registry
    world.deaths_registry = deaths_registry
    world.titles = titles

    settings = payload.global_settings
    modifiers = payload.life_cycle
    events = payload.negative_events

    sequences = cascade_sequences(titles, payload.title_sequences)
    if not sequences:
        logger("No title sequences configured — nothing to simulate.")
        return world

    # Per-title state: list of dynasties to walk through, current sequence index,
    # the date when the current sequence began, generation counter, and the
    # active ruler. We keep it as plain dicts keyed by title id.
    title_state: dict[str, dict] = {}
    for tid, seq_list in sequences.items():
        if not seq_list:
            continue
        title_state[tid] = {
            "sequences": list(seq_list),
            "index": 0,
            "started_year": settings.start_year,
            "generations": 0,
            "ruler_id": None,
        }

    # Bootstrap each title with a founder ruler from its first dynasty
    for tid, st in title_state.items():
        seq = st["sequences"][0]
        founder = world.make_character(
            dynasty=seq.dynasty_id,
            culture="default_culture",
            religion="default_faith",
            is_female=False,
            birth_year=settings.start_year - 30,
        )
        st["ruler_id"] = founder.id
        world.title_holders.setdefault(tid, []).append(
            (_date(settings.start_year, 1, 1), founder.id)
        )
        world.current_dynasty[tid] = seq.dynasty_id

    # ------------------------------------------------------------------
    # Year-by-year tick
    # ------------------------------------------------------------------
    for year in range(settings.start_year, settings.end_year + 1):
        if year % 50 == 0:
            logger(f"Simulating year {year}...")

        # 1. Mortality for everyone alive
        for char in list(world.characters.values()):
            if not char.is_alive:
                continue
            reason = annual_death_check(char, year, events, deaths_registry, rng)
            if reason:
                world.kill(char, year, reason)

        # 2. Fertility — generate children for living, married couples
        for char in list(world.characters.values()):
            if not char.is_alive or char.is_female:
                continue  # Iterate from the male side to avoid double-counting
            if not char.spouse_ids:
                continue
            spouse = world.characters.get(char.spouse_ids[-1])
            if not spouse or not spouse.is_alive:
                continue
            mom_age = _age(spouse, year)
            if mom_age < 16 or mom_age > 45:
                continue
            if len(char.child_ids) >= modifiers.max_children_per_couple:
                continue
            fertility = modifiers.base_fertility_rate * char.fertility_multiplier * spouse.fertility_multiplier
            if rng.random() < fertility:
                # Child takes the FATHER'S house by default — overridden during marriage transitions
                house = char.dynasty_house
                if hasattr(spouse, "_force_child_house"):
                    house = getattr(spouse, "_force_child_house")
                world.make_character(
                    dynasty=house,
                    culture=char.culture,
                    religion=char.religion,
                    is_female=rng.random() < 0.5,
                    birth_year=year,
                    father_id=char.id,
                    mother_id=spouse.id,
                )

        # 3. Succession + transition events for each title
        for tid, st in title_state.items():
            ruler = world.characters.get(st["ruler_id"])
            if ruler is None:
                continue

            # Check whether the current sequence has expired
            seq = st["sequences"][st["index"]]
            expired = False
            if seq.duration_type == "years":
                expired = (year - st["started_year"]) >= seq.duration_value
            else:  # generations
                expired = st["generations"] >= seq.duration_value

            # If ruler is dead, do an immediate succession to the heir within the same dynasty.
            # If no natural heir exists, fabricate a sibling/cousin in the same house so the
            # dynasty continues for its full configured duration (premature transitions would
            # break the user's timeline).
            if not ruler.is_alive:
                heir = _find_heir(world, ruler)
                if heir is None:
                    heir = world.make_character(
                        dynasty=ruler.dynasty_house,
                        culture=ruler.culture,
                        religion=ruler.religion,
                        is_female=False,
                        birth_year=year - 25,
                    )
                st["ruler_id"] = heir.id
                st["generations"] += 1
                death_year = int(ruler.death_date.split(".")[0])
                world.title_holders[tid].append(
                    (_date(death_year, 1, 1), heir.id)
                )
                ruler = heir

            if expired and st["index"] + 1 < len(st["sequences"]):
                next_seq = st["sequences"][st["index"] + 1]
                _execute_transition(
                    world, tid, ruler, seq, next_seq, year, modifiers, deaths_registry,
                )
                st["index"] += 1
                st["started_year"] = year
                st["generations"] = 0
                # Update active ruler from the holders list
                latest_holder_id = world.title_holders[tid][-1][1]
                st["ruler_id"] = latest_holder_id
                world.current_dynasty[tid] = next_seq.dynasty_id

    return world


# ---------------------------------------------------------------------------
# Heir / transition helpers
# ---------------------------------------------------------------------------

def _find_heir(world: WorldState, ruler: Character) -> Optional[Character]:
    """Return the eldest living son of `ruler` belonging to the same dynasty."""
    candidates = [
        world.characters[cid]
        for cid in ruler.child_ids
        if cid in world.characters
        and world.characters[cid].is_alive
        and not world.characters[cid].is_female
        and world.characters[cid].dynasty_house == ruler.dynasty_house
    ]
    if not candidates:
        # Fall back to any living child of correct dynasty (matrilineal)
        candidates = [
            world.characters[cid]
            for cid in ruler.child_ids
            if cid in world.characters
            and world.characters[cid].is_alive
            and world.characters[cid].dynasty_house == ruler.dynasty_house
        ]
    if not candidates:
        return None
    candidates.sort(key=lambda c: c.birth_date)
    return candidates[0]


def _execute_transition(
    world: WorldState,
    title_id: str,
    current_ruler: Character,
    current_seq: DynastySequence,
    next_seq: DynastySequence,
    year: int,
    modifiers: LifeCycleModifiers,
    deaths_registry: list[dict],
) -> None:
    # The transition method describes how the *current* sequence's rule ends —
    # so dispatch on current_seq, not next_seq.
    method = current_seq.transition_method
    if method == "marriage":
        _transition_marriage(world, title_id, current_ruler, next_seq, year, modifiers)
    elif method == "usurpation":
        _transition_usurpation(world, title_id, current_ruler, next_seq, year, deaths_registry)
    else:  # extinction
        _transition_extinction(world, title_id, current_ruler, next_seq, year)


def _transition_marriage(
    world: WorldState,
    title_id: str,
    ruler: Character,
    next_seq: DynastySequence,
    year: int,
    modifiers: LifeCycleModifiers,
) -> None:
    """Spec 7.1: force heir, marry into incoming house, child born into House B."""
    # Spawn an heir for the outgoing ruler if none exists yet
    heir = _find_heir(world, ruler)
    if heir is None:
        heir = world.make_character(
            dynasty=ruler.dynasty_house,
            culture=ruler.culture,
            religion=ruler.religion,
            is_female=False,
            birth_year=year - 25,
            father_id=ruler.id,
        )

    # Find or create a partner from House B
    partner = world.find_eligible_spouse(heir, next_seq.dynasty_id, year, modifiers)
    if partner is None:
        partner = world.make_character(
            dynasty=next_seq.dynasty_id,
            culture=ruler.culture,
            religion=ruler.religion,
            is_female=not heir.is_female,
            birth_year=year - 22,
        )

    world.marry(heir, partner)
    # Force the resulting child to be born into House B (spec override)
    setattr(heir, "_force_child_house", next_seq.dynasty_id)
    setattr(partner, "_force_child_house", next_seq.dynasty_id)

    # When the heir eventually dies the child inherits — for simplicity we
    # immediately register the marriage as a transition point so the title
    # history reflects the dynastic shift at marriage time.
    world.title_holders[title_id].append((f"{year}.6.15", heir.id))


def _transition_usurpation(
    world: WorldState,
    title_id: str,
    ruler: Character,
    next_seq: DynastySequence,
    year: int,
    deaths_registry: list[dict],
) -> None:
    """Spec 7.2: hostile mortality on outgoing ruler, claimant displacement."""
    # Create the antagonist — head of incoming dynasty
    antagonist = world.make_character(
        dynasty=next_seq.dynasty_id,
        culture=ruler.culture,
        religion=ruler.religion,
        is_female=False,
        birth_year=year - 35,
    )
    # Force a hostile death
    reason = pick_hostile_death(deaths_registry, world.rng)
    world.kill(ruler, year, reason, killer_id=antagonist.id)

    # Claimant/employer edge case — displace the ruler's immediate family
    family = [
        world.characters[cid]
        for cid in (ruler.child_ids + ruler.spouse_ids)
        if cid in world.characters and world.characters[cid].is_alive
    ]
    friendly_ruler = _find_friendly_ruler(world, ruler, antagonist.id)
    for member in family:
        if friendly_ruler:
            member.employer_id = friendly_ruler.id
            member.employer_date = f"{year}.6.15"

    world.title_holders[title_id].append((f"{year}.6.15", antagonist.id))


def _transition_extinction(
    world: WorldState,
    title_id: str,
    ruler: Character,
    next_seq: DynastySequence,
    year: int,
) -> None:
    """Spec 7.3: zero fertility for the final generation, then distant claim."""
    ruler.fertility_multiplier = 0.0
    for cid in ruler.child_ids:
        if cid in world.characters:
            world.characters[cid].fertility_multiplier = 0.0

    # On ruler's eventual death, distant claim transfers to House B head.
    # We synthesize an immediate transfer once the ruler is already gone, or
    # at the current `year` if still alive (the spec says "upon death", but
    # the engine has no future-callback so we register the event now).
    incoming = world.make_character(
        dynasty=next_seq.dynasty_id,
        culture=ruler.culture,
        religion=ruler.religion,
        is_female=False,
        birth_year=year - 35,
    )
    transfer_year = year
    if ruler.death_date:
        transfer_year = int(ruler.death_date.split(".")[0])
    world.title_holders[title_id].append((f"{transfer_year}.6.15", incoming.id))


def _find_friendly_ruler(
    world: WorldState,
    displaced: Character,
    exclude_id: str,
) -> Optional[Character]:
    """Find another active landed ruler matching culture or faith."""
    for tid, holders in world.title_holders.items():
        if not holders:
            continue
        latest_id = holders[-1][1]
        if latest_id == exclude_id:
            continue
        candidate = world.characters.get(latest_id)
        if not candidate or not candidate.is_alive:
            continue
        if (candidate.culture == displaced.culture
                or candidate.religion == displaced.religion):
            return candidate
    return None
