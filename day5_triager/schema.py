from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Urgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TriageResult(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    equipment: str = Field(min_length=1, description="Name of the affected medical or facility equipment")
    urgency: Urgency
    hospital: str | None = Field(default=None, description="Hospital/clinic name, or null if not mentioned")
    next_action: str = Field(min_length=1, description="Concrete immediate action for the engineering team")

    @field_validator("urgency", mode="before")
    @classmethod
    def normalize_urgency(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("hospital", mode="before")
    @classmethod
    def normalize_missing_hospital(cls, value: object) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        if not cleaned or cleaned.lower() in {"null", "none", "n/a", "unknown", "not mentioned", "missing"}:
            return None
        return cleaned