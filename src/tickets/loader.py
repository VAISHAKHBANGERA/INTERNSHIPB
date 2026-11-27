import csv
import logging
from dataclasses import dataclass, field
from pathlib import Path
from pydantic import ValidationError
from tickets.models import Ticket

logger = logging.getLogger(__name__)


@dataclass
class LoadResult:
    valid: list[Ticket] = field(default_factory=list)
    invalid: list[dict[str, object]] = field(default_factory=list)


def load_tickets(csv_path: Path) -> LoadResult:
    result = LoadResult()

    if not csv_path.exists() or csv_path.stat().st_size == 0:
        logger.warning("CSV file is empty or missing: %s", csv_path)
        return result

    with csv_path.open(mode="r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            try:
                ticket = Ticket.model_validate(row)
                result.valid.append(ticket)
                logger.info("Row %d valid: ticket_id=%d", row_num, ticket.ticket_id)
            except ValidationError as exc:
                result.invalid.append({"row": row_num, "data": row, "errors": exc.errors()})
                logger.warning("Row %d invalid: %s", row_num, exc.errors()[0]["msg"])

    logger.info("Finished loading %s: %d valid, %d invalid", csv_path.name, len(result.valid), len(result.invalid))
    return result