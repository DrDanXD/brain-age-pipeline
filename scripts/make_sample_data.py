"""Generate a fully synthetic cohort so the repo runs without patient data.

Values are simulated from rough population trends (GM shrinks with age, WMH
and hippocampal loss track age and metabolic load). They are NOT the real
cohort data and must not be reported as results.

Usage: python scripts/make_sample_data.py [n] -> data/sample_cohort.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

N = int(sys.argv[1]) if len(sys.argv) > 1 else 118
OUT = Path("data/sample_cohort.csv")


def main(seed=42):
    rng = np.random.default_rng(seed)
    age = np.clip(rng.normal(46, 10, N), 21, 75).round()
    male = rng.random(N) < 0.66
    hba1c = np.clip(rng.normal(5.2 + 0.01 * (age - 45), 0.6, N), 4.2, 9.5)
    sbp = np.clip(rng.normal(118 + 0.4 * (age - 45) + 5 * male, 12, N), 95, 180).round()
    hscrp = np.clip(rng.lognormal(-0.9, 0.8, N), 0.02, 6)
    glucose = np.clip(70 + 4.5 * hba1c + rng.normal(0, 6, N), 70, 200)
    tg = np.clip(rng.lognormal(4.8, 0.35, N), 40, 400)
    ldl = np.clip(rng.normal(125, 30, N), 50, 240)
    risk = (0.8 * (hba1c - 5.4) + 0.03 * (sbp - 120) + 0.4 * np.log(hscrp / 0.4))

    icv = rng.normal(1_440_000 + 90_000 * male, 70_000, N)
    gm_ratio = 0.46 - 0.0016 * (age - 20) - 0.004 * risk + rng.normal(0, 0.012, N)
    wm_ratio = 0.37 - 0.0006 * (age - 20) - 0.002 * risk + rng.normal(0, 0.012, N)
    wmh_ratio = np.clip(0.002 + 0.00018 * (age - 20) + 0.0012 * risk
                        + rng.normal(0, 0.002, N), 0.0006, 0.03)
    hipp_ratio = 0.0052 - 0.000018 * (age - 20) - 0.00008 * risk + rng.normal(0, 0.00025, N)

    gm, wm, wmh = gm_ratio * icv, wm_ratio * icv, wmh_ratio * icv
    hipp = hipp_ratio * icv
    l_hipp = hipp * rng.normal(0.49, 0.01, N)

    df = pd.DataFrame({
        "Study ID": [f"DEMO-{i + 1:03d}" for i in range(N)],
        "Age (yrs)": age.astype(int),
        "Sex": np.where(male, "male", "female"),
        "Height (cm)": (np.where(male, 172, 159) + rng.normal(0, 6, N)).round(),
        "Weight (kg)": (np.where(male, 74, 60) + rng.normal(0, 10, N)).round(),
        "Smoking Status": np.where(rng.random(N) < 0.2, "Smoker", "Non-Smoker"),
        "SBP (mmHg)": sbp.astype(int),
        "DBP (mmHg)": (sbp * 0.65 + rng.normal(0, 5, N)).round().astype(int),
        "HbA1c (%)": hba1c.round(1),
        "LDL (mg/dL)": ldl.round(1),
        "Triglycerides (mg/dL)": tg.round(),
        "hsCRP (mg/dL)": hscrp.round(2),
        "Fasting Glucose (mg/dL)": glucose.round(1),
        "ICV (mm³)": icv.round(-3),
        "GM Vol (mm³)": gm.round(-3),
        "WM Vol (mm³)": wm.round(-3),
        "L. Hippocampus (mm³)": l_hipp.round(-1),
        "R. Hippocampus (mm³)": (hipp - l_hipp).round(-1),
        "WMH Vol (mm³)": wmh.round(-2),
    })
    df["Total Hipp. (mm³)"] = df["L. Hippocampus (mm³)"] + df["R. Hippocampus (mm³)"]
    df["GM/ICV Ratio"] = (df["GM Vol (mm³)"] / df["ICV (mm³)"]).round(4)
    df["WMH/ICV Ratio"] = (df["WMH Vol (mm³)"] / df["ICV (mm³)"]).round(6)
    df["Biological Age (yrs)"] = df["Age (yrs)"]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Wrote {N} synthetic subjects -> {OUT}")


if __name__ == "__main__":
    main()
