# FlowCV — a futures-positioning strategy, and an honest account of its record

FlowCV is my second project. It is a systematic long/short strategy on single-stock futures on India's National Stock Exchange. I include it for its research discipline, not its returns. The backtest looked good, the first live months did not, and the gap between them is where most of what I know about validation comes from.

## How it works

Run every evening on the exchange's end-of-day files:

1. **Regime gate (direction).** A composite score built from 37 global ETF features sets the day's regime. A coarse band acts only as a freshness guard. A finer band (half the width) decides direction: long pool, short pool, or no trade.
2. **Stock scoring (selection).** About 214 futures-eligible stocks are scored on 13 futures-microstructure features: basis, open-interest flow, put-call ratio, 5-day return reversal, crowding. The top quintile is the long pool and the bottom quintile the short pool. An open-interest crowding filter drops crowded names. The three strongest remaining names are traded.
3. **Exits.** A fixed horizon (T+7, or T+5 in risk-off regimes), a −3% basket stop, and a breaker after three consecutive losing cycles.

## The record

| | Period | n | Mean | Hit rate |
|---|---|---|---|---|
| **Backtest, raw** (fixed T+5 exit, no overlay rules) | 2024-11-04 → 2026-04-28 | 216 cycles | **+0.66% per cycle, gross** | 58.8% |
| **Live paper trading, futures** | 2026-05-20 → 2026-06-17 | 42 closed positions | **−0.84% per position** | 26% |

Notes on reading these numbers:

- **Cycles overlap.** A new cycle opens each trading day and holds for five, so the 216 cycles are not independent. The per-cycle information ratio (0.23) overstates significance, and no t-statistic is quoted.
- **The backtest basket is wider than the live one.** The backtest scores the ten strongest names per cycle; live trading takes three.
- **The raw figure is gross of costs.** At the retail cost and slippage assumptions I used, costs take roughly 0.4–0.7 pp per cycle. That erases most of the raw edge.
- **The parameter record.** It states that feature signs, weights and regime thresholds were frozen on 2024-10-31, before the backtest window. The overlay rules (regime-dependent exit, basket stop) were designed while studying this same window. That is why I report the raw figure and not the rules-applied one.
- **Live paper trading was worse.** 30 of the 42 live exits were basket stops. Four weeks is too short to falsify the signal. It does not confirm it either.

## A number I withdrew

The strategy's internal headline was **+1.36% per cycle** (information ratio 0.44). I found that one of its exit rules, a "basket-stop rescue", took the T+5 exit whenever that turned out better than the T+7 one. That choice is only possible with hindsight. Removing that rule, and the rules tuned on the same window, leaves the raw +0.66% above. I would rather show the smaller number and the reason.

## Also not reported

An options variant ran from 2026-05-29 in paper. Its ledger records some exits at the underlying stock's price instead of the option's, so its average return is an artifact of that defect. For example, one position shows a premium bought at 7.25 and "sold" at 610.15. Until the ledger is repaired and re-derived from exchange prices, it has no record I can stand behind.

## What carried over into Anka

The habits Anka enforces were formed here:

- declare which tier a number is: raw, rules-applied, or net
- never report a figure you cannot reproduce from its canonical script
- split every aggregate by sub-period
- treat any rule chosen on the evaluation window as in-sample

Every number in the table above is computed from files the strategy wrote while running. None was typed from memory.
