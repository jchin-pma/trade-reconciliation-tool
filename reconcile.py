"""
Trade Reconciliation Tool
-------------------------
Compares an internal trade book against broker confirms.
Flags mismatches in quantity or price, and identifies trades
that appear in one file but not the other.

Output: printed summary + reports/reconciliation_report.csv
"""

import pandas as pd
import os
from datetime import datetime


def load_trades(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip().str.lower()
    return df


def reconcile(internal_path: str, broker_path: str) -> pd.DataFrame:
    internal = load_trades(internal_path)
    broker = load_trades(broker_path)

    # Merge on trade_id so we can compare side-by-side
    merged = pd.merge(
        internal,
        broker,
        on="trade_id",
        how="outer",
        suffixes=("_internal", "_broker"),
        indicator=True,
    )

    results = []

    for _, row in merged.iterrows():
        trade_id = row["trade_id"]
        source = row["_merge"]

        # Trade exists in internal but not broker
        if source == "left_only":
            results.append({
                "trade_id":  trade_id,
                "symbol":    row.get("symbol_internal", ""),
                "status":    "UNMATCHED — missing from broker",
                "field":     "-",
                "internal_value": "-",
                "broker_value":   "-",
            })
            continue

        # Trade exists in broker but not internal
        if source == "right_only":
            results.append({
                "trade_id":  trade_id,
                "symbol":    row.get("symbol_broker", ""),
                "status":    "UNMATCHED — missing from internal",
                "field":     "-",
                "internal_value": "-",
                "broker_value":   "-",
            })
            continue

        # Trade exists in both — check fields
        fields_to_check = ["quantity", "price", "side", "settlement_date"]
        trade_ok = True

        for field in fields_to_check:
            internal_val = row[f"{field}_internal"]
            broker_val   = row[f"{field}_broker"]

            # Use tolerance for float comparisons
            if field in ("quantity", "price"):
                mismatch = abs(float(internal_val) - float(broker_val)) > 0.001
            else:
                mismatch = str(internal_val).strip() != str(broker_val).strip()

            if mismatch:
                trade_ok = False
                results.append({
                    "trade_id":       trade_id,
                    "symbol":         row["symbol_internal"],
                    "status":         "MISMATCH",
                    "field":          field,
                    "internal_value": internal_val,
                    "broker_value":   broker_val,
                })

        if trade_ok:
            results.append({
                "trade_id":       trade_id,
                "symbol":         row["symbol_internal"],
                "status":         "OK",
                "field":          "-",
                "internal_value": "-",
                "broker_value":   "-",
            })

    return pd.DataFrame(results)


def print_summary(report: pd.DataFrame):
    total   = report["trade_id"].nunique()
    ok      = report[report["status"] == "OK"].shape[0]
    issues  = report[report["status"] != "OK"]

    print("\n" + "=" * 55)
    print("  TRADE RECONCILIATION REPORT")
    print(f"  Run date: {datetime.today().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 55)
    print(f"  Total trades evaluated : {total}")
    print(f"  Clean matches          : {ok}")
    print(f"  Issues found           : {len(issues)}")
    print("=" * 55)

    if issues.empty:
        print("  All trades reconciled successfully.")
    else:
        print("\n  ISSUES:\n")
        for _, row in issues.iterrows():
            print(f"  [{row['status']}] Trade {row['trade_id']} ({row['symbol']})")
            if row["field"] != "-":
                print(f"    Field    : {row['field']}")
                print(f"    Internal : {row['internal_value']}")
                print(f"    Broker   : {row['broker_value']}")
            print()
    print("=" * 55)


def save_report(report: pd.DataFrame, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    report.to_csv(output_path, index=False)
    print(f"\n  Full report saved to: {output_path}")


if __name__ == "__main__":
    INTERNAL = "data/internal_trades.csv"
    BROKER   = "data/broker_trades.csv"
    OUTPUT   = "reports/reconciliation_report.csv"

    report = reconcile(INTERNAL, BROKER)
    print_summary(report)
    save_report(report, OUTPUT)
