from __future__ import annotations

import argparse
import calendar
import json
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Set


DATA_FILE = Path("preschool_data.json")


@dataclass
class Child:
    child_id: str
    child_name: str
    parent_name: str
    tuition_fee: float
    meal_fee_per_day: float
    arrears: float = 0.0


class PreschoolApp:
    def __init__(self, data_file: Path = DATA_FILE) -> None:
        self.data_file = data_file
        self.children: Dict[str, Child] = {}
        self.attendance: Dict[str, Set[str]] = {}
        self._load()

    def _load(self) -> None:
        if not self.data_file.exists():
            return
        raw = json.loads(self.data_file.read_text(encoding="utf-8"))
        self.children = {
            child_id: Child(**child_data)
            for child_id, child_data in raw.get("children", {}).items()
        }
        self.attendance = {
            child_id: set(days)
            for child_id, days in raw.get("attendance", {}).items()
        }

    def _save(self) -> None:
        payload = {
            "children": {
                child_id: asdict(child) for child_id, child in self.children.items()
            },
            "attendance": {
                child_id: sorted(list(days))
                for child_id, days in self.attendance.items()
            },
        }
        self.data_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add_child(
        self,
        child_id: str,
        child_name: str,
        parent_name: str,
        tuition_fee: float,
        meal_fee_per_day: float,
        arrears: float = 0.0,
    ) -> None:
        if child_id in self.children:
            raise ValueError(f"Dziecko o ID '{child_id}' już istnieje.")

        self.children[child_id] = Child(
            child_id=child_id,
            child_name=child_name,
            parent_name=parent_name,
            tuition_fee=tuition_fee,
            meal_fee_per_day=meal_fee_per_day,
            arrears=arrears,
        )
        self.attendance.setdefault(child_id, set())
        self._save()

    def mark_attendance(self, child_id: str, attendance_date: date) -> None:
        if child_id not in self.children:
            raise ValueError(f"Nie znaleziono dziecka o ID '{child_id}'.")

        self.attendance.setdefault(child_id, set()).add(attendance_date.isoformat())
        self._save()

    def monthly_attendance_count(self, child_id: str, year: int, month: int) -> int:
        if child_id not in self.children:
            raise ValueError(f"Nie znaleziono dziecka o ID '{child_id}'.")
        month_dates = self.attendance.get(child_id, set())
        return sum(
            1
            for value in month_dates
            if datetime.fromisoformat(value).year == year
            and datetime.fromisoformat(value).month == month
        )

    def calculate_monthly_due(self, child_id: str, year: int, month: int) -> Dict[str, float | int | str]:
        if child_id not in self.children:
            raise ValueError(f"Nie znaleziono dziecka o ID '{child_id}'.")

        child = self.children[child_id]
        attendance_count = self.monthly_attendance_count(child_id, year, month)
        meal_cost = attendance_count * child.meal_fee_per_day
        total_due = child.tuition_fee + meal_cost + child.arrears

        return {
            "child_id": child.child_id,
            "child_name": child.child_name,
            "parent_name": child.parent_name,
            "period": f"{year:04d}-{month:02d}",
            "attendance_days": attendance_count,
            "tuition_fee": round(child.tuition_fee, 2),
            "meal_cost": round(meal_cost, 2),
            "arrears": round(child.arrears, 2),
            "total_due": round(total_due, 2),
        }

    def list_children(self) -> List[Child]:
        return list(self.children.values())


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Niepoprawny format daty. Użyj YYYY-MM-DD."
        ) from exc


def parse_month(value: str) -> tuple[int, int]:
    try:
        parsed = datetime.strptime(value, "%Y-%m")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Niepoprawny format miesiąca. Użyj YYYY-MM."
        ) from exc

    return parsed.year, parsed.month


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Aplikacja do zarządzania przedszkolem: obecności i rozliczenia rodziców"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_child = subparsers.add_parser("add-child", help="Dodaj dziecko")
    add_child.add_argument("--id", required=True, help="ID dziecka")
    add_child.add_argument("--child-name", required=True, help="Imię i nazwisko dziecka")
    add_child.add_argument("--parent-name", required=True, help="Imię i nazwisko rodzica")
    add_child.add_argument("--tuition", required=True, type=float, help="Miesięczne czesne")
    add_child.add_argument("--meal-rate", required=True, type=float, help="Stawka wyżywienia za 1 dzień")
    add_child.add_argument("--arrears", type=float, default=0.0, help="Zaległość")

    mark = subparsers.add_parser("mark-attendance", help="Dodaj obecność")
    mark.add_argument("--id", required=True, help="ID dziecka")
    mark.add_argument("--date", required=True, type=parse_date, help="Data obecności YYYY-MM-DD")

    summary = subparsers.add_parser("monthly-summary", help="Podsumowanie należności miesięcznej")
    summary.add_argument("--id", required=True, help="ID dziecka")
    summary.add_argument("--month", required=True, type=parse_month, help="Miesiąc rozliczenia YYYY-MM")

    list_children = subparsers.add_parser("list-children", help="Lista dzieci")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    app = PreschoolApp()

    if args.command == "add-child":
        app.add_child(
            child_id=args.id,
            child_name=args.child_name,
            parent_name=args.parent_name,
            tuition_fee=args.tuition,
            meal_fee_per_day=args.meal_rate,
            arrears=args.arrears,
        )
        print("Dodano dziecko.")

    elif args.command == "mark-attendance":
        app.mark_attendance(args.id, args.date)
        print("Dodano obecność.")

    elif args.command == "monthly-summary":
        year, month = args.month
        result = app.calculate_monthly_due(args.id, year, month)
        month_name = calendar.month_name[month]
        print(f"Podsumowanie za {month_name} {year}:")
        print(f"Dziecko: {result['child_name']} ({result['child_id']})")
        print(f"Rodzic: {result['parent_name']}")
        print(f"Liczba dni obecności: {result['attendance_days']}")
        print(f"Czesne: {result['tuition_fee']:.2f} PLN")
        print(f"Wyżywienie: {result['meal_cost']:.2f} PLN")
        print(f"Zaległość: {result['arrears']:.2f} PLN")
        print(f"Łączna należność: {result['total_due']:.2f} PLN")

    elif args.command == "list-children":
        children = app.list_children()
        if not children:
            print("Brak dzieci w systemie.")
            return
        for child in children:
            print(
                f"{child.child_id}: {child.child_name}, rodzic: {child.parent_name}, "
                f"czesne: {child.tuition_fee:.2f} PLN, "
                f"stawka wyżywienia: {child.meal_fee_per_day:.2f} PLN, "
                f"zaległość: {child.arrears:.2f} PLN"
            )


if __name__ == "__main__":
    main()
