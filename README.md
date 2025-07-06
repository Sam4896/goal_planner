# Advanced SIP & SWP Goal-Planner

This repo lets you answer three practical questions in one shot:

1. **Accumulation:**  
   *How much must I invest (lump sum `I`, monthly SIP `Mi`, or time `Ti`) so that…*  
2. **Retirement corpus:**  
   …after paying a **one-off capital-gains tax**, my pot is big enough to…  
3. **Systematic Withdrawal Plan (SWP):**  
   …pay myself **₹ A in today’s money every month for `Tw` years**, with the
   payment auto-inflating to keep pace with CPI.

The maths lives in **`swp_planner.py`** (`solve_swp`), while **`main.py`**
acts as a Swiss-army driver and auto-plotter.

| File             | Role |
|------------------|------|
| `swp_planner.py` | Pure maths – `solve_swp` handles *accumulation → tax → SWP* |
| `main.py`        | Edit the **USER INPUT** block and run `python main.py` |
| `figs/`          | Output PNGs land here (`curve.png`, `surface.png`) |

---

## How `main.py` decides what to do

| Leave as `None` | What happens                           | Output in `figs/` |
|-----------------|----------------------------------------|-------------------|
| exactly **1** of `I / Mi / Ti` | Prints the missing number in the console | — |
| exactly **2** | Generates a **2-D curve** showing the trade-off between the two unknowns | `curve.png` |
| all **3** | Generates a **3-D surface** (unknown plotted over a grid of the other two) | `surface.png` |

> **Negative results are clipped to zero** before plotting, and old PNGs are
> deleted at the start of each run so you never mix outputs.

---

## Quick example

```python
# --- USER INPUT in main.py ---------------------------------------
A_today        = 8_000      # today's rupees you want each month in retirement
Tw             = 20         # withdrawal horizon (years)

inflation_rate = 0.07
annual_return  = 0.11
tax_rate       = 0.125

I   = 500_000   # upfront lump sum
Mi  = None      # <- solve for required monthly SIP
Ti  = None      # <- solve for accumulation time
# ---------------------------------------------------------------

$ python main.py
─ Result ─
I           : 500,000.00
Mi          :  2,455.31   # <= solver found this
Ti          :     9.25    # ≈ 9 years 3 months
corpus_at_retirement: 3,184,621.25
