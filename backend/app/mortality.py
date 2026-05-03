"""Mortality / death-reason logic (spec ch. 6.2)."""

import math
import random
from typing import Optional

from .schemas import Character, NegativeEvent


def base_mortality(age: int) -> float:
    """Exponential mortality curve.

    Roughly: ~0.2% at infancy, ~1% at 30, ~6% at 60, ~30% at 80, ~80%+ past 90.
    """
    if age < 1:
        return 0.05  # infant mortality bump
    # exp curve calibrated so exp(age/12) - 1 normalized
    p = (math.exp(age / 18.0) - 1.0) / 800.0
    return min(p, 0.99)


def mortality_multiplier_for(year: int, events: list[NegativeEvent]) -> float:
    """Apply spec 6.2.1 mortality spikes — multiply by every active event."""
    mult = 1.0
    for ev in events:
        if ev.start_year <= year <= ev.end_year:
            mult *= ev.mortality_multiplier
    return mult


def pick_natural_death(
    character: Character,
    death_reasons: list[dict],
    rng: random.Random,
) -> str:
    """Pick a natural death ID, heavily weighting trait-triggered ones (spec 6.2.2)."""
    natural = [d for d in death_reasons if d["is_natural"]]
    if not natural:
        return "natural_causes"

    weighted: list[tuple[dict, float]] = []
    char_traits = set(character.traits)
    for d in natural:
        if d["required_trait"]:
            if d["required_trait"] in char_traits:
                weighted.append((d, 10.0))
            # else: can't apply at all
        else:
            weighted.append((d, 1.0))

    if not weighted:
        return "natural_causes"

    total = sum(w for _, w in weighted)
    pick = rng.random() * total
    acc = 0.0
    for d, w in weighted:
        acc += w
        if pick <= acc:
            return d["id"]
    return weighted[-1][0]["id"]


def pick_hostile_death(
    death_reasons: list[dict],
    rng: random.Random,
) -> str:
    """Pick a non-natural death (execution, murder, battle) per spec 6.2.3."""
    hostile = [d for d in death_reasons if not d["is_natural"]]
    if hostile:
        return rng.choice(hostile)["id"]
    return "death_execution"


def annual_death_check(
    character: Character,
    year: int,
    events: list[NegativeEvent],
    death_reasons: list[dict],
    rng: random.Random,
) -> Optional[str]:
    """If the character dies this year, return the death reason ID; else None."""
    age = year - int(character.birth_date.split(".")[0])
    if age < 0:
        return None
    p = base_mortality(age) * mortality_multiplier_for(year, events)
    if rng.random() < p:
        return pick_natural_death(character, death_reasons, rng)
    return None
