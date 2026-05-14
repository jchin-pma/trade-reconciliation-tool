"""
Generates two mock trade files (internal book vs broker confirms)
with deliberate mismatches for the reconciliation tool to find.
"""

import csv
import os

internal_trades = [
    {"trade_id": "T001", "symbol": "AAPL",  "side": "BUY",  "quantity": 100, "price": 182.50, "settlement_date": "2026-05-15"},
    {"trade_id": "T002", "symbol": "MSFT",  "side": "SELL", "quantity": 200, "price": 415.00, "settlement_date": "2026-05-15"},
    {"trade_id": "T003", "symbol": "GOOGL", "side": "BUY",  "quantity": 50,  "price": 175.30, "settlement_date": "2026-05-15"},
    {"trade_id": "T004", "symbol": "TSLA",  "side": "SELL", "quantity": 75,  "price": 248.00, "settlement_date": "2026-05-15"},
    {"trade_id": "T005", "symbol": "AMZN",  "side": "BUY",  "quantity": 30,  "price": 195.60, "settlement_date": "2026-05-15"},
    {"trade_id": "T006", "symbol": "NVDA",  "side": "BUY",  "quantity": 60,  "price": 950.00, "settlement_date": "2026-05-15"},
]

# Broker file has deliberate mismatches on T002, T004, and is missing T006
broker_trades = [
    {"trade_id": "T001", "symbol": "AAPL",  "side": "BUY",  "quantity": 100, "price": 182.50, "settlement_date": "2026-05-15"},
    {"trade_id": "T002", "symbol": "MSFT",  "side": "SELL", "quantity": 250, "price": 415.00, "settlement_date": "2026-05-15"},  # qty mismatch
    {"trade_id": "T003", "symbol": "GOOGL", "side": "BUY",  "quantity": 50,  "price": 175.30, "settlement_date": "2026-05-15"},
    {"trade_id": "T004", "symbol": "TSLA",  "side": "SELL", "quantity": 75,  "price": 250.00, "settlement_date": "2026-05-15"},  # price mismatch
    {"trade_id": "T005", "symbol": "AMZN",  "side": "BUY",  "quantity": 30,  "price": 195.60, "settlement_date": "2026-05-15"},
    # T006 missing from broker — unmatched trade
]

fields = ["trade_id", "symbol", "side", "quantity", "price", "settlement_date"]

os.makedirs("data", exist_ok=True)

with open("data/internal_trades.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(internal_trades)

with open("data/broker_trades.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(broker_trades)

print("Sample data files created in data/")
