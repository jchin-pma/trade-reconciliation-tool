# Trade Reconciliation Tool

A Python tool that compares an internal trade book against broker confirms, flags mismatches, and generates a reconciliation report.

## What it does

- Loads two CSV files: internal trades and broker confirms
- Matches trades by `trade_id`
- Flags mismatches in quantity, price, side, or settlement date
- Identifies trades missing from either side (breaks)
- Outputs a summary to the terminal and a full CSV report

## Skills demonstrated

- `pandas` for data loading, merging, and analysis
- CSV file I/O
- Outer joins to detect missing records
- Tolerance-based float comparison (avoids false positives from rounding)
- Clean separation of data generation, logic, and output

## How to run

```bash
# 1. Generate sample trade data (creates data/ folder)
python3 generate_sample_data.py

# 2. Run the reconciliation
python3 reconcile.py
```

## Sample output

```
=======================================================
  TRADE RECONCILIATION REPORT
  Run date: 2026-05-13 09:00
=======================================================
  Total trades evaluated : 6
  Clean matches          : 3
  Issues found           : 3
=======================================================

  ISSUES:

  [MISMATCH] Trade T002 (MSFT)
    Field    : quantity
    Internal : 200
    Broker   : 250

  [MISMATCH] Trade T004 (TSLA)
    Field    : price
    Internal : 248.0
    Broker   : 250.0

  [UNMATCHED — missing from broker] Trade T006 (NVDA)
```

## Files

```
project-1-trade-reconciliation/
├── generate_sample_data.py   # Creates mock trade CSVs
├── reconcile.py              # Main reconciliation logic
├── data/
│   ├── internal_trades.csv
│   └── broker_trades.csv
└── reports/
    └── reconciliation_report.csv
```
