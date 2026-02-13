from datetime import date
from pathlib import Path

from preschool_app import PreschoolApp


def test_monthly_due_calculation(tmp_path: Path) -> None:
    data_file = tmp_path / "data.json"
    app = PreschoolApp(data_file=data_file)

    app.add_child(
        child_id="C1",
        child_name="Jan Kowalski",
        parent_name="Anna Kowalska",
        tuition_fee=1200.0,
        meal_fee_per_day=15.5,
        arrears=80.0,
    )

    app.mark_attendance("C1", date(2026, 1, 5))
    app.mark_attendance("C1", date(2026, 1, 6))
    app.mark_attendance("C1", date(2026, 1, 8))

    summary = app.calculate_monthly_due("C1", 2026, 1)

    assert summary["attendance_days"] == 3
    assert summary["meal_cost"] == 46.5
    assert summary["total_due"] == 1326.5


def test_attendance_deduplication_for_same_day(tmp_path: Path) -> None:
    data_file = tmp_path / "data.json"
    app = PreschoolApp(data_file=data_file)

    app.add_child(
        child_id="C2",
        child_name="Ola Nowak",
        parent_name="Piotr Nowak",
        tuition_fee=900.0,
        meal_fee_per_day=12.0,
    )

    app.mark_attendance("C2", date(2026, 2, 1))
    app.mark_attendance("C2", date(2026, 2, 1))

    summary = app.calculate_monthly_due("C2", 2026, 2)

    assert summary["attendance_days"] == 1
    assert summary["meal_cost"] == 12.0
    assert summary["total_due"] == 912.0
