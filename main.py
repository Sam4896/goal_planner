#!/usr/bin/env python3
"""
main.py  –  driver & auto‑plot for the SWP‑aware solver
-------------------------------------------------------

Inputs
------
A_today      – desired real monthly withdrawal (₹, today's value)
Tw           – withdrawal horizon (years)

Exactly one of:
    • initial (I)      – upfront lump sum
    • monthly (Mi)     – monthly SIP during accumulation
    • years   (Ti)     – accumulation period (yrs)
may be left **None**; that one will be solved for.

unknowns = 1  → prints result
unknowns = 2  → figs/curve.png (trade‑off curve)
unknowns = 3  → figs/surface.png (3‑D surface, negatives clipped)
"""

from __future__ import annotations
import os, sys
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from planner_core import solve_swp  # <-- NEW import

# ------------------------------------------------------------------ #
# USER INPUT                                                         #
# ------------------------------------------------------------------ #
A_today = 100000  # ₹/month in today's money
Tw = 10  # withdrawal period (years)

inflation_rate = 0.07  # 7 % p.a.
annual_return = 0.125  # 12.5 % p.a. pre‑tax
tax_rate = 0.125  # 12.5 % capital‑gains tax at withdrawal

initial = None  # I  – put number or None
monthly = 16000  # Mi – put number or None
years = None  # Ti – put number or None
# ------------------------------------------------------------------ #

OUT_DIR = "figs"
os.makedirs(OUT_DIR, exist_ok=True)
for old in ("curve.png", "surface.png"):
    try:
        os.remove(os.path.join(OUT_DIR, old))
    except FileNotFoundError:
        pass

# ------------------------------------------------------------------ #
# Branch on how many unknowns                                        #
# ------------------------------------------------------------------ #
unk = [v is None for v in (initial, monthly, years)].count(True)
base = dict(
    A_today=A_today,
    Tw=Tw,
    inflation_rate=inflation_rate,
    annual_return=annual_return,
    tax_rate=tax_rate,
)

# ---------- 1 unknown → print ------------------------------------ #
if unk == 1:
    res = solve_swp(**base, Ti=years, Mi=monthly, I=initial)
    print("\n─ Result ─")
    for k, v in res.items():
        print(f"{k:<25}: {v:,.2f}" if isinstance(v, float) else f"{k:<25}: {v}")
    print()

# ---------- 2 unknowns → 2‑D curve ------------------------------- #
elif unk == 2:
    common_title = (
        f"Tax rate = {tax_rate * 100:.1f}%, "
        f"Inflation rate = {inflation_rate * 100:.1f}%, "
        f"Annual return = {annual_return * 100:.1f}%, "
        f"Withdrawal horizon = {Tw} years, "
        f"Monthly withdrawal = {A_today} ₹"
    )
    print(common_title)
    print("Generating 2‑D trade‑off curve…")
    plt.figure()

    # Ti known  → sweep I, solve Mi
    if years is not None:
        initials = np.linspace(0, A_today * 50, 250)
        monthlies = [
            max(solve_swp(**base, Ti=years, I=i, Mi=None)["Mi"], 0) for i in initials
        ]
        plt.plot(initials, monthlies)
        plt.xlabel("Initial lump sum (₹)")
        plt.ylabel("Monthly SIP required (₹)")
        plt.title(f"Monthly vs Initial  ({common_title})")

    # Mi known → sweep I, solve Ti
    elif monthly is not None:
        initials = np.linspace(0, A_today * 50, 250)
        yrs = [
            max(solve_swp(**base, Mi=monthly, I=i, Ti=None)["Ti"], 0) for i in initials
        ]
        plt.plot(initials, yrs)
        plt.xlabel("Initial lump sum (₹)")
        plt.ylabel("Years required")
        plt.title(f"Years vs Initial  ({common_title})")

    # I known → sweep Mi, solve Ti
    else:
        monthlies = np.linspace(100, A_today * 4, 250)
        yrs = [
            max(solve_swp(**base, I=initial, Mi=m, Ti=None)["Ti"], 0) for m in monthlies
        ]
        plt.plot(monthlies, yrs)
        plt.xlabel("Monthly SIP (₹)")
        plt.ylabel("Years required")
        plt.title(f"Years vs Monthly  ({common_title})")

    plt.grid(True)
    curve_path = os.path.join(OUT_DIR, "curve.png")
    plt.savefig(curve_path, dpi=150, bbox_inches="tight")
    plt.show()
    plt.close()
    print(f"Saved plot → {curve_path}")

# ---------- 3 unknowns → 3‑D surface ----------------------------- #
elif unk == 3:
    print("Generating 3‑D surface…")
    monthlies = np.linspace(100, A_today * 4, 40)
    years_grid = np.linspace(1, 30, 40)
    M, Y = np.meshgrid(monthlies, years_grid)

    initial_needed = np.zeros_like(M)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            val = solve_swp(**base, Ti=Y[i, j], Mi=M[i, j], I=None)["I"]
            initial_needed[i, j] = max(val, 0)  # clip negatives

    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(M, Y, initial_needed, linewidth=0, antialiased=True)
    ax.set_xlabel("Monthly SIP (₹)")
    ax.set_ylabel("Years")
    ax.set_zlabel("Initial needed (₹)")
    ax.set_title("Initial requirement surface (negatives clipped)")
    surf_path = os.path.join(OUT_DIR, "surface.png")
    plt.savefig(surf_path, dpi=150, bbox_inches="tight")
    plt.show()
    plt.close()
    print(f"Saved surface → {surf_path}")

else:
    print("Nothing to solve – all three variables provided.")
    sys.exit(1)


# entry‑point for `python -m` or `sipgp`
def main() -> None:
    pass


if __name__ == "__main__":
    main()
