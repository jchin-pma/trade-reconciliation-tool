"""
Trade Reconciliation Tool
-------------------------
Compares an internal trade book against broker confirms.
Flags mismatches in quantity or price, and identifies trades
that appear in one file but not the other.

Modes:
  python reconcile.py                        # compare two local CSVs
  python reconcile.py --live                 # fetch Robinhood trades via MCP, then reconcile
  python reconcile.py --live --after 2026-05-01

Output: printed summary + reports/reconciliation_report.csv
"""

import argparse
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
    parser = argparse.ArgumentParser(description="Trade Reconciliation Tool")
    parser.add_argument("--internal", default="data/internal_trades.csv",
                        help="Internal trade book CSV")
    parser.add_argument("--broker", default="data/broker_trades.csv",
                        help="Broker confirms CSV (ignored when --live is set)")
    parser.add_argument("--output", default="reports/reconciliation_report.csv",
                        help="Output report CSV path")
    parser.add_argument("--live", action="store_true",
                        help="Fetch broker data live from Robinhood MCP instead of a CSV")
    parser.add_argument("--after", default=None,
                        help="With --live: only fetch trades after this date (YYYY-MM-DD)")
    args = parser.parse_args()

    broker_path = args.broker

    if args.live:
        import os as _os
        from robinhood_fetch import fetch_orders_via_requests, normalize_order, write_csv

        token = _os.environ.get("ROBINHOOD_TOKEN")
        if not token:
            raise SystemExit(
                "Set the ROBINHOOD_TOKEN environment variable to use --live mode.\n"
                "When running inside Claude, the robinhood-trading MCP server "
                "handles authentication automatically."
            )

        print("Fetching live trades from Robinhood MCP ...")
        raw = fetch_orders_via_requests(token, args.after)
        rows = [r for o in raw if (r := normalize_order(o)) is not None]
        broker_path = "data/broker_trades_live.csv"
        write_csv(rows, broker_path)

    report = reconcile(args.internal, broker_path)
    print_summary(report)
    save_report(report, args.output)
