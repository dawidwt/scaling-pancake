# Aplikacja do zarządzania przedszkolem

Prosta aplikacja CLI w Pythonie do:
- dodawania dzieci,
- rejestrowania obecności,
- rozliczania kosztów wyżywienia na podstawie liczby obecności,
- podliczania łącznej należności rodzica: **czesne + wyżywienie + zaległość**.

## Wymagania
- Python 3.10+

## Uruchamianie

### 1. Dodanie dziecka
```bash
python preschool_app.py add-child \
  --id C1 \
  --child-name "Jan Kowalski" \
  --parent-name "Anna Kowalska" \
  --tuition 1200 \
  --meal-rate 15.5 \
  --arrears 80
```

### 2. Dodanie obecności
```bash
python preschool_app.py mark-attendance --id C1 --date 2026-01-05
python preschool_app.py mark-attendance --id C1 --date 2026-01-06
```

### 3. Podsumowanie miesięczne
```bash
python preschool_app.py monthly-summary --id C1 --month 2026-01
```

### 4. Lista dzieci
```bash
python preschool_app.py list-children
```

Dane zapisywane są automatycznie do pliku `preschool_data.json`.

## Testy
```bash
pytest -q
```
