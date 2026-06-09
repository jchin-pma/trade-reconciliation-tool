"""
Fetches executed orders from the Robinhood MCP server and converts them
into the standard trade CSV format expected by reconcile.py.

Usage (via Claude with the robinhood-trading MCP server active):
  Claude will call the MCP tools on your behalf.

Standalone usage (requires ROBINHOOD_TOKEN env var):
  python robinhood_fetch.py --output data/broker_trades.csv
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any


MCP_SERVER_URL = "https://agent.robinhood.com/mcp/trading"
FIELDS = ["trade_id", "symbol", "side", "quantity", "price", "settlement_date"]


def _settlement_date(executed_at: str, days: int = 2) -> str:
    """T+2 settlement from execution timestamp."""
    from datetime import timedelta
    dt = datetime.fromisoformat(executed_at.replace("Z", "+00:00"))
    settled = dt + timedelta(days=days)
    return settled.strftime("%Y-%m-%d")


def normalize_order(order: dict[str, Any]) -> dict[str, Any] | None:
    """Convert a Robinhood MCP order object to reconciliation row format."""
    state = order.get("state", "")
    if state != "filled":
        return None

    executed_at = order.get("last_transaction_at") or order.get("updated_at", "")
    avg_price = order.get("average_price") or order.get("price")
    quantity = order.get("cumulative_quantity") or order.get("quantity")

    if not all([avg_price, quantity, executed_at]):
        return None

    return {
        "trade_id":        order["id"],
        "symbol":          order["symbol"],
        "side":            order["side"].upper(),
        "quantity":        float(quantity),
        "price":           float(avg_price),
        "settlement_date": _settlement_date(executed_at),
    }


def fetch_orders_via_requests(token: str, start_date: str | None = None) -> list[dict]:
    """
    Fallback: call the Robinhood MCP HTTP endpoint directly.
    The MCP server exposes a tool call interface over SSE; this hits
    the equivalent REST path when running outside of Claude.
    """
    try:
        import requests
    except ImportError:
        sys.exit("Install the 'requests' package: pip install requests")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "get_orders",
            "arguments": {"state": "filled", **({"after": start_date} if start_date else {})},
        },
    }
    resp = requests.post(MCP_SERVER_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("result", {}).get("orders", [])


def write_csv(rows: list[dict], output_path: str):
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} trades to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Fetch Robinhood trades via MCP")
    parser.add_argument("--output", default="data/broker_trades.csv",
                        help="Output CSV path (default: data/broker_trades.csv)")
    parser.add_argument("--after", default=None,
                        help="Only fetch trades after this date (YYYY-MM-DD)")
    parser.add_argument("--token", default=os.environ.get("ROBINHOOD_TOKEN"),
                        help="Robinhood OAuth token (or set ROBINHOOD_TOKEN env var)")
    args = parser.parse_args()

    if not args.token:
        sys.exit(
            "No auth token found. Set ROBINHOOD_TOKEN environment variable "
            "or pass --token. When running inside Claude, the MCP server "
            "handles authentication automatically."
        )

    print(f"Fetching filled orders from {MCP_SERVER_URL} ...")
    raw_orders = fetch_orders_via_requests(args.token, args.after)

    rows = [r for o in raw_orders if (r := normalize_order(o)) is not None]
    if not rows:
        print("No filled orders returned.")
        return

    write_csv(rows, args.output)


if __name__ == "__main__":
    main()
