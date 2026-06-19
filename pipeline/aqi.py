"""CPCB National Air Quality Index (2014) computation.

Sub-index per pollutant via linear interpolation within breakpoint buckets;
AQI = max of available sub-indices. The lower five bands (Good..Very Poor) are
verified against official CPCB documentation. The Severe (401-500) band is
open-ended officially, so its upper concentration bound below is a documented
convention and the sub-index clamps at 500.
"""

from __future__ import annotations

# (C_lo, C_hi, I_lo, I_hi). Units: ug/m3 except CO in mg/m3.
BREAKPOINTS: dict[str, list[tuple[float, float, int, int]]] = {
    "PM2.5": [(0, 30, 0, 50), (30, 60, 51, 100), (60, 90, 101, 200),
              (90, 120, 201, 300), (120, 250, 301, 400), (250, 500, 401, 500)],
    "PM10":  [(0, 50, 0, 50), (50, 100, 51, 100), (100, 250, 101, 200),
              (250, 350, 201, 300), (350, 430, 301, 400), (430, 600, 401, 500)],
    "NO2":   [(0, 40, 0, 50), (40, 80, 51, 100), (80, 180, 101, 200),
              (180, 280, 201, 300), (280, 400, 301, 400), (400, 1000, 401, 500)],
    "O3":    [(0, 50, 0, 50), (50, 100, 51, 100), (100, 168, 101, 200),
              (168, 208, 201, 300), (208, 748, 301, 400), (748, 1000, 401, 500)],
    "CO":    [(0, 1.0, 0, 50), (1.0, 2.0, 51, 100), (2.0, 10, 101, 200),
              (10, 17, 201, 300), (17, 34, 301, 400), (34, 50, 401, 500)],
    "SO2":   [(0, 40, 0, 50), (40, 80, 51, 100), (80, 380, 101, 200),
              (380, 800, 201, 300), (800, 1600, 301, 400), (1600, 2620, 401, 500)],
    "NH3":   [(0, 200, 0, 50), (200, 400, 51, 100), (400, 800, 101, 200),
              (800, 1200, 201, 300), (1200, 1800, 301, 400), (1800, 2400, 401, 500)],
}

MIN_POLLUTANTS = 3
PM_POLLUTANTS = ("PM2.5", "PM10")


def sub_index(pollutant: str, concentration: float | None) -> int | None:
    """Linear-interpolated CPCB sub-index, or None for missing/negative/unknown."""
    if pollutant not in BREAKPOINTS or concentration is None or concentration < 0:
        return None
    table = BREAKPOINTS[pollutant]
    c = float(concentration)
    for c_lo, c_hi, i_lo, i_hi in table:
        if c_lo <= c <= c_hi:
            return round((i_hi - i_lo) / (c_hi - c_lo) * (c - c_lo) + i_lo)
    if c > table[-1][1]:  # beyond the top bucket -> clamp
        return 500
    return None


def compute_aqi(concentrations: dict[str, float | None]) -> tuple[int | None, str | None]:
    """CPCB AQI = max sub-index. Requires >=3 pollutants incl. PM2.5/PM10.

    Returns (aqi, dominant_pollutant) or (None, None) if the validity rule is unmet.
    """
    subs: dict[str, int] = {}
    for pol in BREAKPOINTS:
        si = sub_index(pol, concentrations.get(pol))
        if si is not None:
            subs[pol] = si
    has_pm = any(p in subs for p in PM_POLLUTANTS)
    if len(subs) < MIN_POLLUTANTS or not has_pm:
        return None, None
    dominant = max(subs, key=subs.get)
    return subs[dominant], dominant
