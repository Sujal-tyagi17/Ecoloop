import math
from typing import Dict, Any, Tuple

def calculate_pmv_ppd(
    ta: float,          # Air temperature (C)
    tr: float = None,   # Mean radiant temperature (C), defaults to ta if None
    vel: float = 0.1,   # Relative air velocity (m/s)
    rh: float = 50.0,   # Relative humidity (%)
    met: float = 1.2,   # Metabolic rate (met) (1 met = 58.15 W/m2)
    clo: float = 0.5,   # Clothing insulation (clo) (1 clo = 0.155 m2K/W)
    wme: float = 0.0    # External work (met), normally 0
) -> Tuple[float, float, str]:
    """
    Calculates Fanger PMV (Predicted Mean Vote) and PPD (Predicted Percentage Dissatisfied)
    according to ISO 7730 / ASHRAE Standard 55.

    Returns:
        (PMV, PPD, Category_Description)
    """
    if tr is None:
        tr = ta

    # Convert units
    m = met * 58.15     # Metabolic rate in W/m2
    w = wme * 58.15     # External work in W/m2
    mw = m - w          # Internal heat production in human body

    # Clothing thermal resistance
    icl = 0.155 * clo

    # Saturated water vapor pressure (Pa)
    pa = rh * 10.0 * math.exp(16.6536 - 4030.18 / (ta + 235.0))

    # Clothing surface area factor
    if icl <= 0.078:
        fcl = 1.0 + 1.29 * icl
    else:
        fcl = 1.05 + 0.645 * icl

    hcf = 12.1 * math.sqrt(max(0.001, vel))
    tcaa = ta + 273.15
    traa = tr + 273.15
    tcla = tcaa + (35.5 - ta) / (3.5 * (icl * 100.0) + 1.0)

    p1 = icl * fcl
    p2 = p1 * 3.96
    p3 = p1 * 100.0
    p4 = p1 * tcaa
    p5 = 308.7 - 0.028 * mw + p2 * math.pow(traa / 100.0, 4)

    xn = tcla / 100.0
    count = 0
    eps = 0.0001
    hc = 0.0

    while count < 150:
        xf = xn
        # Bound xf to physically realistic clothing surface temp scale [2.0, 4.0] (200K to 400K)
        xf = max(2.0, min(4.0, xf))
        
        hcn = 2.38 * math.pow(abs(100.0 * xf - tcaa), 0.25)
        if hcf > hcn:
            hc = hcf
        else:
            hc = hcn
        
        xn = (p5 + p3 * hc * tcaa - p2 * math.pow(xf, 4)) / (100.0 + p3 * hc)
        xn = max(2.0, min(4.0, xn))
        if abs(xn - xf) < eps:
            break
        count += 1

    tcl = 100.0 * xn - 273.15  # Surface temperature of clothing (C)

    # Heat loss components
    hl1 = 3.05 * 0.001 * (5733.0 - 6.99 * mw - pa)                  # Skin diffusion
    hl2 = 0.42 * (mw - 58.15) if mw > 58.15 else 0.0               # Sweating
    hl3 = 1.7 * 0.00001 * m * (5867.0 - pa)                        # Latent respiration
    hl4 = 0.0014 * m * (34.0 - ta)                                 # Dry respiration
    hl5 = 3.96 * fcl * (math.pow(xn, 4) - math.pow(traa / 100.0, 4))# Radiation
    hl6 = fcl * hc * (tcl - ta)                                    # Convection

    # Thermal sensation load
    ts = 0.303 * math.exp(-0.036 * m) + 0.028
    pmv = ts * (mw - hl1 - hl2 - hl3 - hl4 - hl5 - hl6)

    # Bound PMV between -3.0 and +3.0
    pmv = max(-3.0, min(3.0, pmv))

    # Calculate PPD (%)
    ppd = 100.0 - 95.0 * math.exp(-0.03353 * math.pow(pmv, 4) - 0.2179 * math.pow(pmv, 2))
    ppd = max(5.0, min(100.0, ppd))

    # Category classification
    if abs(pmv) <= 0.2:
        cat = "Optimal Comfort (Cat A)"
    elif abs(pmv) <= 0.5:
        cat = "Comfortable (Cat B)"
    elif abs(pmv) <= 0.7:
        cat = "Slight Discomfort (Cat C)"
    else:
        cat = "Uncomfortable (Out of Bounds)"

    return round(pmv, 3), round(ppd, 1), cat

def evaluate_comfort_score(pmv: float) -> Tuple[bool, float]:
    is_compliant = -0.5 <= pmv <= 0.5
    penalty = 0.0 if is_compliant else abs(pmv) - 0.5
    return is_compliant, penalty
