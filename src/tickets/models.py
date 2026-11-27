from datetime import date
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class Ticket(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    ticket_id: int
    customer_name: str = Field(min_length=1)
    equipment: str = Field(min_length=1)
    status: TicketStatus
    created_date: date

    @field_validator("created_date", mode="before")
    @classmethod
    def parse_iso_date(cls, value: str | date) -> date:
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value).strip())
        except ValueError as exc:
            raise ValueError("Invalid date format; expected YYYY-MM-DD") from exc