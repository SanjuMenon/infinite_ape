from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Union


FinancialsJSON = Mapping[str, Union[int, float, None]]  # one-year record
ExposureJSON = Optional[Mapping[str, Any]]              # metadata; not used in calc


def debt_capacity(financials: FinancialsJSON, exposure: ExposureJSON) -> Dict[str, float]:
    """
    Single-year version of debt_capacity.

    Input:
      financials: JSON dict with required fields:
        YEAR, ER12, ER32, P88, EM06, ER13, ER41, P19, P14, P03, P20
      exposure: accepted for signature compatibility; not used.

    Output:
      JSON dict with components + FCF + DC + DCU
      (All numeric outputs are floats.)
    """

    # ---- Validate required fields ----
    required = ["YEAR", "ER12", "ER32", "P88", "EM06", "ER13", "ER41", "P19", "P14", "P03", "P20"]
    missing = [k for k in required if k not in financials]
    if missing:
        raise ValueError(f"Missing required fields in financials JSON: {missing}")

    # ---- Original assumptions ----
    interest_rate = 0.05
    tax_rate = 0.18
    effective_rate = interest_rate * (1 - tax_rate)
    period = 7

    interest_calc_hypo = 0.05
    interest_calc_subordinate = 0.06

    # Annuity PV factor
    if abs(effective_rate) < 1e-12:
        dc_factor = float(period)
    else:
        dc_factor = (1 - (1 + effective_rate) ** (-period)) / effective_rate

    # ---- Pull values as floats (None -> error early) ----
    def f(key: str) -> float:
        v = financials[key]
        if v is None:
            raise ValueError(f"financials[{key}] is None; expected a number.")
        return float(v)

    YEAR = f("YEAR")  # kept numeric; you can also return as int if you prefer

    ER12 = f("ER12")
    ER32 = f("ER32")
    P88 = -f("P88")
    EM06 = -f("EM06")
    Re_CapEx = f("ER13") + f("ER41")

    int_sub = -abs(f("P19")) * interest_calc_subordinate
    int_hypo = -abs(f("P14")) * interest_calc_hypo

    # FCF = sum of the constructed components (mirrors the DataFrame sum intent)
    FCF = ER12 + ER32 + P88 + EM06 + Re_CapEx + int_sub + int_hypo

    DC = FCF * dc_factor

    debt_used = f("P03") + f("P20") - f("P19")
    DCU = (debt_used / DC) if DC != 0 else float("nan")

    return {
        "year": YEAR,
        "ER12": ER12,
        "ER32": ER32,
        "P88": P88,
        "EM06": EM06,
        "Re_CapEx": Re_CapEx,
        "int_sub": int_sub,
        "int_hypo": int_hypo,
        "FCF": FCF,
        "DC": DC,
        "DCU": DCU,
    }