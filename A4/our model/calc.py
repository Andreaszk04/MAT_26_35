"""
CALC – Calculate: "What can we derive?"

Thermal resistance and U-value (DS/EN ISO 6946, simplified: homogeneous layers),
quantities in the Table 7 declared unit, GWP, and the insulation thickness of an
alternative material that gives the same thermal resistance.
"""


# ----------------------------------------------------------------------------
# Thermal
# ----------------------------------------------------------------------------
def CALC_LAYER_R(thickness_m, lam=None, fixed_R=None):
    """Thermal resistance of one layer [m2K/W]. R = d / lambda, or a fixed R (air layers)."""
    if fixed_R is not None:
        return float(fixed_R) if thickness_m > 0 else 0.0
    if thickness_m == 0:
        return 0.0  # membranes etc. have no thermal resistance
    if not lam:
        return None
    return thickness_m / lam


def CALC_UVALUE(layer_R_values, Rsi=0.13, Rse=0.04):
    """U = 1 / (Rsi + sum(R) + Rse). Returns None if any layer R is unknown."""
    if any(R is None for R in layer_R_values):
        return None
    return 1.0 / (Rsi + sum(layer_R_values) + Rse)


def CALC_INSULATION_UVALUE(R_insulation):
    """'U-value' of the insulation layer(s) alone, 1/R_ins [W/m2K]."""
    return 1.0 / R_insulation if R_insulation else None


def CALC_EQUIVALENT_THICKNESS(R_target, lam_alternative):
    """Thickness of an alternative insulation with the same R: d = R * lambda [m]."""
    return R_target * lam_alternative


# ----------------------------------------------------------------------------
# Quantity in Table 7 declared unit + GWP
# ----------------------------------------------------------------------------
def CALC_QUANTITY(epd, area_m2, thickness_m, R=None):
    """Convert a layer (area, thickness, R) into the Table 7 functional unit.
    Returns (quantity, note). quantity is None when the conversion is impossible."""
    fu = epd["unit"].replace("³", "3").replace("²", "2")
    volume = area_m2 * thickness_m
    rho, rho_unit = epd["mass_factor"], epd["mass_unit"]

    if fu == "m3":
        return volume, ""
    if fu == "m2":
        return area_m2, ""
    if "R=1" in fu:  # 'm2 with R=1 m2K/W': amount = area * R
        if R is None:
            return None, "R unknown - cannot convert to 'm2 with R=1'"
        return area_m2 * R, ""
    if fu in ("kg", "ton"):
        if rho_unit == "kg/m3":
            mass = volume * rho
        elif rho_unit == "g/cm3":
            mass = volume * rho * 1000.0
        elif rho_unit == "kg/m2":
            mass = area_m2 * rho
        else:
            return None, f"mass unit '{rho_unit}' not handled"
        return (mass if fu == "kg" else mass / 1000.0), ""
    return None, f"declared unit '{epd['unit']}' not handled for walls"


def CALC_GWP(epd, quantity):
    """GWP [kg CO2-eq] for modules A1-A3, C3, C4 (BR18 scope used by the old model)
    plus module D reported separately."""
    if epd is None or quantity is None:
        return None
    a, c3, c4 = epd["gwp_A1A3"] * quantity, epd["gwp_C3"] * quantity, epd["gwp_C4"] * quantity
    return {
        "GWP_A1A3": a,
        "GWP_C3": c3,
        "GWP_C4": c4,
        "GWP_total": a + c3 + c4,
        "GWP_D": epd["gwp_D"] * quantity,
    }
