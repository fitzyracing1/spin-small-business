"""spin-small-business: bookkeeping CSV summary and quarterly tax helper."""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

INTRO = (
    "spin-small-business by Joshua Almeida.\n"
    "You supply the tax rate. This is a math helper, not tax advice.\n"
    "Sponsor: https://github.com/sponsors/fitzyracing1"
)

CENTS = Decimal("0.01")
ZERO = Decimal("0")
REQUIRED = ("date", "description", "category", "amount", "type")
TAX_DISCLAIMER = (
    "This is a math helper, not tax advice. You supply the rate. "
    "It does not apply deductions, credits, annualization, or filing rules."
)


def D(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    text = str(value).strip()
    if text.endswith("%"):
        return Decimal(text[:-1].strip()) / Decimal("100")
    return Decimal(text)


def money(value) -> Decimal:
    return D(value).quantize(CENTS, rounding=ROUND_HALF_UP)


def fmt(value: Decimal) -> str:
    return f"{money(value):.2f}"


def parse_date(text: str) -> date:
    return datetime.strptime(text.strip(), "%Y-%m-%d").date()


def parse_type(text: str) -> str:
    value = text.strip().lower()
    if value in ("income", "in", "revenue"):
        return "income"
    if value in ("expense", "exp", "cost"):
        return "expense"
    raise ValueError(f"type must be income or expense, got {text!r}")


def load_books(path) -> list[dict]:
    rows = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV has no header row.")
        fields = {name.strip().lower(): name for name in reader.fieldnames}
        missing = [name for name in REQUIRED if name not in fields]
        if missing:
            raise ValueError(f"CSV is missing columns: {', '.join(missing)}")
        for index, raw in enumerate(reader, start=2):
            try:
                amount = money(raw[fields["amount"]])
                if amount < ZERO:
                    raise ValueError("amount must be unsigned; use the type column")
                rows.append(
                    {
                        "date": parse_date(raw[fields["date"]]),
                        "description": raw[fields["description"]].strip(),
                        "category": raw[fields["category"]].strip() or "uncategorized",
                        "amount": amount,
                        "type": parse_type(raw[fields["type"]]),
                    }
                )
            except (ValueError, KeyError) as exc:
                raise ValueError(f"row {index}: {exc}") from exc
    return rows


def summarize(rows: list[dict]) -> dict:
    income = defaultdict(lambda: ZERO)
    expense = defaultdict(lambda: ZERO)
    for row in rows:
        if row["type"] == "income":
            income[row["category"]] += row["amount"]
        else:
            expense[row["category"]] += row["amount"]
    income_total = money(sum(income.values(), ZERO))
    expense_total = money(sum(expense.values(), ZERO))
    return {
        "income": {k: money(v) for k, v in sorted(income.items())},
        "expense": {k: money(v) for k, v in sorted(expense.items())},
        "income_total": income_total,
        "expense_total": expense_total,
        "net": money(income_total - expense_total),
        "count": len(rows),
    }


def quarter_of(day: date) -> tuple[int, int]:
    return day.year, (day.month - 1) // 3 + 1


def quarterly(rows: list[dict], rate) -> dict:
    rate = D(rate)
    if rate < ZERO:
        raise ValueError("Tax rate cannot be negative.")
    buckets: dict[tuple[int, int], dict] = {}
    for row in rows:
        key = quarter_of(row["date"])
        bucket = buckets.setdefault(key, {"income": ZERO, "expense": ZERO})
        bucket[row["type"]] += row["amount"]
    quarters = []
    for key in sorted(buckets):
        year, q = key
        inc = money(buckets[key]["income"])
        exp = money(buckets[key]["expense"])
        net = money(inc - exp)
        taxable = net if net > ZERO else ZERO
        estimate = money(taxable * rate)
        quarters.append(
            {
                "year": year,
                "quarter": q,
                "income": inc,
                "expense": exp,
                "net": net,
                "estimate": estimate,
            }
        )
    year_net = money(sum((item["net"] for item in quarters), ZERO))
    year_taxable = money(sum((item["net"] if item["net"] > ZERO else ZERO for item in quarters), ZERO))
    # Yearly helper uses overall net (losses offset gains across quarters).
    overall_taxable = year_net if year_net > ZERO else ZERO
    yearly_estimate = money(overall_taxable * rate)
    equal = money(yearly_estimate / Decimal("4")) if yearly_estimate else ZERO
    # Spread cents: first payments get the remainder so four equal-looking
    # installments still sum to the yearly estimate.
    installments = [equal] * 4
    if yearly_estimate:
        drift = money(yearly_estimate - equal * 4)
        installments[3] = money(equal + drift)
    return {
        "rate": rate,
        "quarters": quarters,
        "year_net": year_net,
        "yearly_estimate": yearly_estimate,
        "installments": installments,
    }


def _print_summary(summary: dict) -> None:
    print(INTRO)
    print()
    print(f"Income by category  ({summary['count']} rows)")
    for name, amount in summary["income"].items():
        print(f"  {name:<24} {fmt(amount)}")
    print(f"  {'total':<24} {fmt(summary['income_total'])}")
    print()
    print("Expense by category")
    for name, amount in summary["expense"].items():
        print(f"  {name:<24} {fmt(amount)}")
    print(f"  {'total':<24} {fmt(summary['expense_total'])}")
    print()
    print(f"Net income               {fmt(summary['net'])}")


def _print_tax(summary: dict, tax: dict) -> None:
    _print_summary(summary)
    print()
    print("Quarterly estimated tax helper")
    print(f"  {TAX_DISCLAIMER}")
    print(f"  Rate supplied by you: {tax['rate']}")
    print()
    print("  By calendar quarter, (income - expense) * rate  (no estimate if the quarter's net is negative):")
    print(f"  {'period':<10} {'income':>10} {'expense':>10} {'net':>10} {'estimate':>10}")
    for item in tax["quarters"]:
        label = f"Q{item['quarter']} {item['year']}"
        print(
            f"  {label:<10} {fmt(item['income']):>10} {fmt(item['expense']):>10}"
            f"  {fmt(item['net']):>10} {fmt(item['estimate']):>10}"
        )
    print(
        f"  {'year net':<10} {'':>10} {'':>10}  {fmt(tax['year_net']):>10} {fmt(tax['yearly_estimate']):>10}"
    )
    print()
    print("  Equal installments of the yearly estimate (yearly net * rate, losses offset gains):")
    for i, amount in enumerate(tax["installments"], start=1):
        print(f"    payment {i}  {fmt(amount)}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="small_business.py",
        description="Summarize a bookkeeping CSV and estimate quarterly tax from a rate you supply.",
    )
    sub = parser.add_subparsers(dest="cmd")
    summ = sub.add_parser("summarize", help="Income and expense totals by category.")
    summ.add_argument("csv")
    tax = sub.add_parser("tax", help="Quarterly estimated-tax helper. You supply the rate. Not tax advice.")
    tax.add_argument("csv")
    tax.add_argument("--rate", required=True, help="Rate you supply, such as 0.25 or 25%.")

    try:
        args = parser.parse_args([] if argv is None and len(sys.argv) == 1 else (sys.argv[1:] if argv is None else argv))
    except SystemExit as exc:
        code = exc.code
        return 0 if code in (0, None) else int(code)

    if not args.cmd:
        print(INTRO)
        print()
        print("Usage: python small_business.py summarize books.csv")
        print("       python small_business.py tax books.csv --rate 25%")
        print()
        print("CSV columns: date,description,category,amount,type")
        print("date is YYYY-MM-DD, amount is unsigned, type is income or expense.")
        print(TAX_DISCLAIMER)
        return 0
    try:
        rows = load_books(args.csv)
        summary = summarize(rows)
        if args.cmd == "summarize":
            _print_summary(summary)
            return 0
        _print_tax(summary, quarterly(rows, args.rate))
        return 0
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
