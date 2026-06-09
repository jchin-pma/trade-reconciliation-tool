# Trade Reconciliation Tool — Claude Instructions

## What this project does
This tool reconciles an internal trade book against broker confirms from Robinhood.
You also have live access to the user's Robinhood account via the **robinhood-trading** MCP server.

## MCP server: robinhood-trading
Connected at `https://agent.robinhood.com/mcp/trading`.
Use its tools to read account data and place orders on behalf of the user.

## Trading rules — follow these on every order

1. **Always confirm before executing.** Show the user the exact order details
   (symbol, side, quantity, order type, price or "market") and wait for explicit
   approval ("yes", "go ahead", "confirmed") before calling any place-order tool.

2. **Never exceed position size limits.** Default max per trade: 100 shares or
   $10,000 notional — whichever is smaller. Warn the user if a request exceeds this.

3. **Prefer limit orders over market orders** unless the user explicitly asks for
   market. Always surface the current bid/ask before suggesting a limit price.

4. **Read before you write.** Before placing any order, call the relevant
   read tools (portfolio, positions, open orders, buying power) so you have
   current state. Summarise what you find first.

5. **One order at a time.** Never batch-place multiple orders in a single turn
   without a separate confirmation for each.

6. **Report outcomes.** After an order is placed or cancelled, confirm the
   order ID, status, and filled price (if available) back to the user.

## Useful things the user can ask
- "What's my current portfolio / buying power?"
- "Show me my open orders"
- "Buy / sell N shares of TICKER [at PRICE]"
- "Cancel all open orders for TICKER"
- "Run a reconciliation against today's Robinhood trades"
- "What trades did I make this week?"

## Reconciliation
- CSV mode: `python reconcile.py`
- Live mode: `python reconcile.py --live [--after YYYY-MM-DD]`
- Reports are saved to `reports/reconciliation_report.csv`
