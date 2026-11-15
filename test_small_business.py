from decimal import Decimal
from pathlib import Path

from small_business import (
    INTRO,
    TAX_DISCLAIMER,
    load_books,
    main,
    quarterly,
    summarize,
)

DATA = Path(__file__).resolve().parent / "testdata" / "books.csv"


def test_intro_names_the_project_and_sponsor():
    assert "spin-small-business" in INTRO
    assert "Joshua Almeida" in INTRO
    assert "https://github.com/sponsors/fitzyracing1" in INTRO
    assert "not tax advice" in INTRO.lower()


def test_help_is_zero():
    assert main([]) == 0
    assert main(["--help"]) == 0


def test_summarize_sample_books():
    rows = load_books(DATA)
    summary = summarize(rows)
    assert summary["count"] == 10
    assert summary["income"]["consulting"] == Decimal("5400.00")
    assert summary["income"]["training"] == Decimal("2000.00")
    assert summary["income_total"] == Decimal("7400.00")
    assert summary["expense"]["rent"] == Decimal("2400.00")
    assert summary["expense"]["tools"] == Decimal("49.99")
    assert summary["expense"]["travel"] == Decimal("320.50")
    assert summary["expense_total"] == Decimal("2770.49")
    assert summary["net"] == Decimal("4629.51")


def test_quarterly_helper_uses_supplied_rate():
    rows = load_books(DATA)
    tax = quarterly(rows, "25%")
    assert tax["rate"] == Decimal("0.25")
    # Q1: income 2400 - expense 849.99 = 1550.01; 25% = 387.50
    q1 = tax["quarters"][0]
    assert q1["year"] == 2026 and q1["quarter"] == 1
    assert q1["net"] == Decimal("1550.01")
    assert q1["estimate"] == Decimal("387.50")
    # Yearly net 4629.51 * 0.25 = 1157.3775 -> 1157.38
    assert tax["year_net"] == Decimal("4629.51")
    assert tax["yearly_estimate"] == Decimal("1157.38")
    assert sum(tax["installments"], Decimal("0")) == tax["yearly_estimate"]


def test_negative_quarter_does_not_create_a_negative_tax():
    # A quarter with more expense than income should estimate 0 for that quarter.
    rows = [
        {"date": __import__("datetime").date(2026, 1, 1), "category": "sales", "amount": Decimal("10.00"), "type": "income", "description": "a"},
        {"date": __import__("datetime").date(2026, 2, 1), "category": "rent", "amount": Decimal("40.00"), "type": "expense", "description": "b"},
    ]
    tax = quarterly(rows, "0.25")
    assert tax["quarters"][0]["net"] == Decimal("-30.00")
    assert tax["quarters"][0]["estimate"] == Decimal("0.00")
    assert tax["yearly_estimate"] == Decimal("0.00")


def test_cli_summarize(capsys):
    assert main(["summarize", str(DATA)]) == 0
    out = capsys.readouterr().out
    assert "7400.00" in out
    assert "2770.49" in out
    assert "4629.51" in out
    assert "consulting" in out


def test_cli_tax_includes_disclaimer(capsys):
    assert main(["tax", str(DATA), "--rate", "25%"]) == 0
    out = capsys.readouterr().out
    assert "not tax advice" in out.lower()
    assert "1157.38" in out
    assert "Q1 2026" in out
    assert TAX_DISCLAIMER.split(",")[0] in out or "not tax advice" in out.lower()


def test_rejects_bad_type(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("date,description,category,amount,type\n2026-01-01,x,y,1.00,gift\n")
    assert main(["summarize", str(path)]) == 2


def test_rejects_signed_amount(tmp_path):
    path = tmp_path / "signed.csv"
    path.write_text("date,description,category,amount,type\n2026-01-01,x,y,-1.00,expense\n")
    assert main(["summarize", str(path)]) == 2


def test_rejects_missing_columns(tmp_path):
    path = tmp_path / "short.csv"
    path.write_text("date,amount\n2026-01-01,1.00\n")
    assert main(["summarize", str(path)]) == 2
