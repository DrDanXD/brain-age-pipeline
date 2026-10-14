"""Step 4: ICV-normalized features and formula checks."""
import numpy as np
import pandas as pd

MODEL_FEATURES = ["gm_icv", "wm_icv", "wmh_icv", "hipp_icv"]


def add_features(df):
    df = df.copy()
    df["total_hipp_calc"] = df["l_hipp"] + df["r_hipp"]
    df["gm_icv_calc"] = df["gm"] / df["icv"]
    df["wm_icv"] = df["wm"] / df["icv"]
    df["wmh_icv_calc"] = df["wmh"] / df["icv"]
    df["hipp_icv"] = df["total_hipp_calc"] / df["icv"]
    # Use the computed values as the source of truth for modelling
    df["total_hipp"] = df["total_hipp_calc"]
    df["gm_icv"] = df["gm_icv_calc"]
    df["wmh_icv"] = df["wmh_icv_calc"]
    return df


def verify_formulas(raw, tol=0.005):
    """Check the derived columns in the source sheet against their formulas.

    Returns a table of formula, matches, total. tol is a relative tolerance
    (0.5%) because the sheet stores ratios rounded to 4 decimals.
    """
    checks = []

    def check(name, stored_col, computed):
        if stored_col not in raw:
            return
        ok = np.isclose(raw[stored_col], computed, rtol=tol, atol=0.01 if "Delta" in name else 0)
        checks.append({"formula": name, "matches": int(ok.sum()), "total": len(raw)})

    check("Total Hipp = L Hipp + R Hipp", "total_hipp", raw["l_hipp"] + raw["r_hipp"])
    check("GM/ICV = GM / ICV", "gm_icv", raw["gm"] / raw["icv"])
    check("WMH/ICV = WMH / ICV", "wmh_icv", raw["wmh"] / raw["icv"])
    if "brain_age_reported" in raw and "delta_reported" in raw:
        check("Brain Age Delta = Brain Age - Chrono Age", "delta_reported",
              raw["brain_age_reported"] - raw["chrono_age"])
    return pd.DataFrame(checks)
