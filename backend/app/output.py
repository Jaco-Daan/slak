"""Paradox-script output formatter (spec ch. 9 — IMMUTABLE format)."""

import io
import zipfile

from .simulation import WorldState
from .schemas import Character


def _format_character(c: Character) -> str:
    """Format a single character per spec 9.1."""
    lines: list[str] = [f"{c.id} = {{"]
    lines.append(f"    name = {c.name}")
    lines.append(f"    dynasty_house = {c.dynasty_house}")
    lines.append(f"    religion = {c.religion}")
    lines.append(f"    culture = {c.culture}")
    lines.append("")

    # `female = yes` ONLY if female (omit entirely otherwise)
    if c.is_female:
        lines.append("    female = yes")
        lines.append("")

    if c.father_id:
        lines.append(f"    father = {c.father_id}")
    if c.mother_id:
        lines.append(f"    mother = {c.mother_id}")
    if c.father_id or c.mother_id:
        lines.append("")

    for trait in c.traits:
        lines.append(f"    trait = {trait}")
    if c.traits:
        lines.append("")

    # Birth block
    lines.append(f"    {c.birth_date} = {{")
    lines.append("        birth = yes")
    lines.append("    }")

    # Optional employment block (claimant displacement)
    if c.employer_id and c.employer_date:
        lines.append("")
        lines.append(f"    {c.employer_date} = {{")
        lines.append(f"        employer = {c.employer_id}")
        lines.append("    }")

    # Death block
    if c.death_date:
        lines.append("")
        lines.append(f"    {c.death_date} = {{")
        lines.append("        death = {")
        lines.append(f"            death_reason = {c.death_reason or 'natural_causes'}")
        # `killer = ...` ONLY if death is hostile (we have a killer_id)
        if c.killer_id:
            lines.append(f"            killer = {c.killer_id}")
        lines.append("        }")
        lines.append("    }")

    lines.append("}")
    return "\n".join(lines)


def render_character_history(world: WorldState) -> str:
    """All characters concatenated into one .txt file (spec 9.1)."""
    blocks = [_format_character(c) for c in world.characters.values()]
    return "\n\n".join(blocks) + "\n"


def render_title_history(world: WorldState) -> str:
    """One block per title id, each with chronologically sorted holders (spec 9.2)."""
    out: list[str] = []
    for title_id, holders in world.title_holders.items():
        if not holders:
            continue
        # Sort by the date string — works because YYYY.M.D pads numerically
        # only loosely, so sort by parsed tuple instead.
        def _key(entry):
            date, _ = entry
            parts = date.split(".")
            return tuple(int(p) for p in parts)

        sorted_holders = sorted(holders, key=_key)
        out.append(f"{title_id} = {{")
        for date, holder_id in sorted_holders:
            out.append(f"    {date} = {{")
            out.append(f"        holder = {holder_id}")
            out.append("    }")
        out.append("}")
    return "\n".join(out) + "\n"


def package_zip(world: WorldState) -> bytes:
    """Bundle character_history.txt + title_history.txt into a ZIP."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("character_history.txt", render_character_history(world))
        zf.writestr("title_history.txt", render_title_history(world))
    return buf.getvalue()
