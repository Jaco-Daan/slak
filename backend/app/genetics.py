"""Genetics inheritance algorithm (spec ch. 6.1)."""

import random
from typing import Optional


def _build_indices(traits: list[dict]) -> tuple[dict, dict, dict]:
    """Return (by_id, by_group_level, group_max_level) lookups."""
    by_id = {t["id"]: t for t in traits}

    by_group_level: dict[str, dict[int, str]] = {}
    group_max: dict[str, int] = {}
    for t in traits:
        g = t["group"]
        lvl = t["level"]
        by_group_level.setdefault(g, {})[lvl] = t["id"]
        group_max[g] = max(group_max.get(g, 0), lvl)
    return by_id, by_group_level, group_max


def _trait_at(by_group_level: dict, group: str, level: int) -> Optional[str]:
    return by_group_level.get(group, {}).get(level)


def inherit_traits(
    mother_traits: list[str],
    father_traits: list[str],
    registry: list[dict],
    rng: random.Random,
) -> list[str]:
    """Compute the genetic trait list for a child given the parents'.

    Implements:
      1. Parent trait evaluation (cancel opposite pairs)
      2. Active inheritance (homogenous: same group)
      3. Passive inheritance (heterogenous: only one parent has it)
      4. Spontaneous mutation against random_creation
    """
    by_id, by_group_level, group_max = _build_indices(registry)

    # 1. Filter parental traits down to those present in the registry
    mom = [t for t in mother_traits if t in by_id]
    dad = [t for t in father_traits if t in by_id]

    # Cancel opposite pairs across parents (if mom has X and dad has anti-X)
    cancelled: set[str] = set()
    for mt in mom:
        opps = set(by_id[mt]["opposites"])
        for dt in dad:
            if dt in opps:
                cancelled.add(mt)
                cancelled.add(dt)
    mom = [t for t in mom if t not in cancelled]
    dad = [t for t in dad if t not in cancelled]

    inherited: set[str] = set()

    # 2/3. Walk every group present in either parent
    mom_by_group: dict[str, str] = {by_id[t]["group"]: t for t in mom}
    dad_by_group: dict[str, str] = {by_id[t]["group"]: t for t in dad}
    all_groups = set(mom_by_group) | set(dad_by_group)

    for group in all_groups:
        m = mom_by_group.get(group)
        d = dad_by_group.get(group)
        if m and d:
            # Homogenous — both parents share the group
            highest_level = max(by_id[m]["level"], by_id[d]["level"])
            roll = rng.random()
            if roll < 0.80:
                chosen = _trait_at(by_group_level, group, highest_level)
            elif roll < 1.00:
                target = min(highest_level + 1, group_max[group])
                chosen = _trait_at(by_group_level, group, target)
            else:
                chosen = None
            if chosen:
                inherited.add(chosen)
        else:
            # Heterogenous — only one parent has it
            parent_trait_id = m or d
            parent_level = by_id[parent_trait_id]["level"]
            roll = rng.random()
            if roll < 0.50:
                target = max(parent_level - 1, 1)
                chosen = _trait_at(by_group_level, group, target)
                if chosen:
                    inherited.add(chosen)
            elif roll < 0.60:
                inherited.add(parent_trait_id)
            # else: not inherited

    # 4. Spontaneous mutation — for groups neither parent has
    inherited_groups = {by_id[t]["group"] for t in inherited}
    for trait in registry:
        if trait["group"] in inherited_groups:
            continue
        if trait["random_creation"] <= 0:
            continue
        if rng.random() < trait["random_creation"]:
            # If multiple levels exist in this group, the lowest one wins by default
            if by_id[trait["id"]]["level"] == 1:
                inherited.add(trait["id"])
                inherited_groups.add(trait["group"])

    return sorted(inherited)


def roll_birth_traits(
    registry: list[dict],
    rng: random.Random,
) -> list[str]:
    """Roll traits for a founder character (no parents). Uses birth_chance."""
    chosen: dict[str, str] = {}  # group -> trait_id
    for trait in registry:
        if trait["birth_chance"] <= 0:
            continue
        if trait["level"] != 1:
            # Only roll the base level for founders
            continue
        if rng.random() < trait["birth_chance"]:
            chosen[trait["group"]] = trait["id"]
    return sorted(chosen.values())
