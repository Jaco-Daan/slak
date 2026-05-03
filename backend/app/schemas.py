"""Pydantic schemas for the simulation payload (spec ch. 4)."""

from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Frontend payload schemas
# ---------------------------------------------------------------------------

class GlobalSettings(BaseModel):
    start_year: int = 6800
    end_year: int = 7200
    maximum_generations: int = 30


class LifeCycleModifiers(BaseModel):
    max_age_difference_between_partners: int = 20
    max_children_per_couple: int = 6
    base_fertility_rate: float = 0.35
    male_bastard_chance: float = 0.05
    female_bastard_chance: float = 0.02


class NegativeEvent(BaseModel):
    id: str
    name: str
    start_year: int
    end_year: int
    mortality_multiplier: float = 1.0


class DynastySequence(BaseModel):
    dynasty_id: str
    duration_type: Literal["years", "generations"] = "years"
    duration_value: int = 50
    transition_method: Literal["marriage", "usurpation", "extinction"] = "marriage"


class ParsedFileData(BaseModel):
    """Backend receives raw .txt file contents and re-parses for safety."""
    titles_txt: Optional[str] = None
    traits_txt: Optional[str] = None
    deaths_txt: Optional[str] = None
    name_lists: dict[str, list[str]] = Field(default_factory=dict)


class SimulationPayload(BaseModel):
    """Full global state object serialized from the frontend."""
    global_settings: GlobalSettings
    life_cycle: LifeCycleModifiers
    negative_events: list[NegativeEvent] = Field(default_factory=list)
    parsed_files: ParsedFileData
    title_sequences: dict[str, list[DynastySequence]] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Internal entity schemas (spec 4.1)
# ---------------------------------------------------------------------------

class Character(BaseModel):
    id: str
    name: str
    dynasty_house: str
    religion: str = "default_faith"
    culture: str = "default_culture"
    is_female: bool = False

    father_id: Optional[str] = None
    mother_id: Optional[str] = None
    spouse_ids: list[str] = Field(default_factory=list)
    child_ids: list[str] = Field(default_factory=list)

    traits: list[str] = Field(default_factory=list)

    birth_date: str  # YYYY.M.D
    death_date: Optional[str] = None

    death_reason: Optional[str] = None
    killer_id: Optional[str] = None

    employer_id: Optional[str] = None
    employer_date: Optional[str] = None

    # Internal helpers (not in spec but useful)
    is_alive: bool = True
    fertility_multiplier: float = 1.0  # Set to 0.0 for extinction last gen
