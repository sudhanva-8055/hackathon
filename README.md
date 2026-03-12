# SmartSettle 🚀
**AI-Powered Transaction Optimizer**

---

## What it does

SmartSettle schedules financial transactions across three payment channels using a **Priority Queue + Greedy Assignment** algorithm, minimising total system cost while respecting deadlines and capacity limits.

---

## How to run

1. Download `SmartSettle.html`
2. Double-click it to open in Chrome
3. That's it — no installs, no server, no internet required

---

## How to use

| Step | Action |
|------|--------|
| **1** | Drop your CSV file into the **Upload CSV** panel on the left |
| **2** | Click **CALCULATE** — the algorithm runs instantly in your browser |
| **3** | View results: success %, estimated cost, channel breakdown |
| **4** | Click **Download JSON** to save your submission file |
| **5** | Click **New Run** in the status bar to reset and try another file |

---

## CSV format

Your input file must have exactly these columns:

```
tx_id, amount, arrival_time, max_delay, priority
```

Example:
```csv
tx_id,amount,arrival_time,max_delay,priority
TX0001,1500.00,100,20,3
TX0002,300.50,102,5,1
TX0003,8000.00,105,10,5
```

---

## Algorithm

### Channels
| Channel | Fee | Latency | Capacity |
|---------|-----|---------|----------|
| `Channel_F` (Fast) | ₹5.00 | 1 min | 2 concurrent |
| `Channel_S` (Standard) | ₹1.00 | 3 min | 4 concurrent |
| `Channel_B` (Bulk) | ₹0.20 | 10 min | 10 concurrent |

### Cost formula
```
Successful tx:  cost = channel_fee + (0.001 × amount × delay)
Failed tx:      cost = 0.5 × amount
```

### Steps
1. Parse CSV and compute a score for each transaction: `priority × amount × (1 / max_delay)`
2. Sort by score descending — highest priority transactions go first
3. For each transaction, find the cheapest channel + timeslot that fits within the deadline without exceeding channel capacity
4. Compute total system cost across all assignments
5. Return results and generate the submission JSON

---

## Output (submission.json)

```json
{
  "assignments": [
    { "tx_id": "TX0001", "channel_id": "Channel_S", "start_time": 100 },
    { "tx_id": "TX0002", "channel_id": "Channel_F", "start_time": 102 },
    { "tx_id": "TX0003", "channel_id": null, "start_time": null, "failed": true }
  ],
  "total_system_cost_estimate": 142.75
}
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Nothing happens on Calculate | Make sure your CSV has all 5 required columns |
| `Missing columns` error | Check column names match exactly: `tx_id, amount, arrival_time, max_delay, priority` |
| Download doesn't trigger | Use Chrome or Edge |
| Results look unexpected | Check for empty rows or extra commas in your CSV |
