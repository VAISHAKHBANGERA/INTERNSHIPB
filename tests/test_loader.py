from pathlib import Path
from tickets.loader import load_tickets
from tickets.models import TicketStatus

HEADER = "ticket_id,customer_name,equipment,status,created_date\n"


def write_csv(tmp_path: Path, content: str) -> Path:
    file_path = tmp_path / "tickets.csv"
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_valid_row(tmp_path: Path) -> None:
    csv_file = write_csv(tmp_path, HEADER + "101,Acme Corp,AC Unit,open,2026-11-24\n")
    result = load_tickets(csv_file)

    assert len(result.valid) == 1
    assert len(result.invalid) == 0
    assert result.valid[0].ticket_id == 101
    assert result.valid[0].status == TicketStatus.OPEN


def test_missing_field(tmp_path: Path) -> None:
    csv_file = write_csv(tmp_path, HEADER + "102,,Generator,open,2026-11-24\n")
    result = load_tickets(csv_file)

    assert len(result.valid) == 0
    assert len(result.invalid) == 1


def test_bad_date(tmp_path: Path) -> None:
    csv_file = write_csv(tmp_path, HEADER + "103,Acme Corp,Elevator,closed,24-11-2026\n")
    result = load_tickets(csv_file)

    assert len(result.valid) == 0
    assert len(result.invalid) == 1


def test_bad_enum(tmp_path: Path) -> None:
    csv_file = write_csv(tmp_path, HEADER + "104,Acme Corp,Chiller,pending,2026-11-24\n")
    result = load_tickets(csv_file)

    assert len(result.valid) == 0
    assert len(result.invalid) == 1


def test_empty_file(tmp_path: Path) -> None:
    csv_file = write_csv(tmp_path, "")
    result = load_tickets(csv_file)

    assert result.valid == []
    assert result.invalid == []
    