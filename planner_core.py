# swp_planner.py
from __future__ import annotations
import math

__all__ = ["solve_swp"]


def _gross_monthly(r_annual: float) -> float:
    return (1 + r_annual) ** (1 / 12) - 1


def _fv_before_tax(L: float, M: float, r: float, n: int) -> float:
    """Future value before tax (ordinary annuity)."""
    fv = L * (1 + r) ** n
    fv += M * ((1 + r) ** n - 1) / r if abs(r) > 1e-12 else M * n
    return fv


def _corpus_after_tax(L: float, M: float, r: float, n: int, tax: float) -> float:
    fv_bt = _fv_before_tax(L, M, r, n)
    gains = fv_bt - (L + M * n)
    return fv_bt - max(gains, 0) * tax


def _corpus_needed_for_swp(
    A_today: float,
    Ti: float,
    Tw: float,
    infl: float,
    r_month: float,
) -> float:
    """
    Corpus required at retirement to pay an inflation‑indexed SWP.

    W₀ (first withdrawal, nominal)  =  A_today · (1+infl)^Ti
    W_t grows every month with inflation.

    Formula: growing‑annuity PV with growth g, discount r.
    """
    g = (1 + infl) ** (1 / 12) - 1
    M = int(round(Tw * 12))
    W0 = A_today * (1 + infl) ** Ti

    if abs(r_month - g) < 1e-12:  # r ≈ g edge‑case
        return W0 * M / (1 + r_month)
    k = (1 + g) / (1 + r_month)
    return W0 * (1 - k**M) / (r_month - g)


# --------------------------------------------------------------------------- #
# Public solver                                                               #
# --------------------------------------------------------------------------- #
def solve_swp(
    A_today: float,
    Tw: float,
    *,
    inflation_rate: float,
    annual_return: float,
    tax_rate: float,
    Ti: float | None,
    Mi: float | None,
    I: float | None,
    search_cap_years: int = 100,
) -> dict[str, float]:
    """
    Exactly ONE of (Ti, Mi, I) must be None; that variable is solved for so the
    retirement corpus meets the SWP requirement.

    Returns a dict with all three variables plus the post‑tax corpus.
    """
    if [Ti, Mi, I].count(None) != 1:
        raise ValueError("Exactly one of (Ti, Mi, I) must be None.")

    r = _gross_monthly(annual_return)

    # -------------------- Unknown I ------------------------- #
    if I is None:
        n = int(round(Ti * 12))
        Cn = _corpus_needed_for_swp(A_today, Ti, Tw, inflation_rate, r)
        growth = (1 + r) ** n
        annuity = ((growth - 1) / r) if abs(r) > 1e-12 else n

        A_L = (1 - tax_rate) * growth + tax_rate
        A_M = (1 - tax_rate) * annuity + tax_rate * n

        I = (Cn - A_M * Mi) / A_L

    # -------------------- Unknown Mi ------------------------ #
    elif Mi is None:
        n = int(round(Ti * 12))
        Cn = _corpus_needed_for_swp(A_today, Ti, Tw, inflation_rate, r)
        growth = (1 + r) ** n
        annuity = ((growth - 1) / r) if abs(r) > 1e-12 else n

        A_L = (1 - tax_rate) * growth + tax_rate
        A_M = (1 - tax_rate) * annuity + tax_rate * n

        Mi = (Cn - A_L * I) / A_M

    # -------------------- Unknown Ti ------------------------ #
    else:
        months = 0
        while months <= search_cap_years * 12:
            yrs_now = months / 12
            Cneed = _corpus_needed_for_swp(A_today, yrs_now, Tw, inflation_rate, r)
            Chave = _corpus_after_tax(I, Mi, r, months, tax_rate)
            if Chave >= Cneed:
                Ti = yrs_now
                break
            months += 1
        else:
            raise RuntimeError("Goal unreachable within search_cap_years.")

    # Final corpus check
    n_final = int(round(Ti * 12))
    C_after = _corpus_after_tax(I, Mi, r, n_final, tax_rate)

    return dict(
        I=I,
        Mi=Mi,
        Ti=Ti,
        corpus_at_retirement=C_after,
    )
