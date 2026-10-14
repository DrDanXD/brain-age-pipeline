"""Load the cohort table and give every column a short, code-friendly name.

Accepts either the original Excel workbook (sheet "Cleaned Data", header on
row 2) or a CSV with the same columns, e.g. data/sample_cohort.csv.
"""
from pathlib import Path

import pandas as pd

COLUMN_MAP = {
    "Study ID": "subject",
    "Age (yrs)": "age",
    "Sex": "sex",
    "Height (cm)": "height_cm",
    "Weight (kg)": "weight_kg",
    "Smoking Status": "smoking",
    "SBP (mmHg)": "sbp",
    "DBP (mmHg)": "dbp",
    "HbA1c (%)": "hba1c",
    "LDL (mg/dL)": "ldl",
    "Triglycerides (mg/dL)": "triglycerides",
    "hsCRP (mg/dL)": "hscrp",
    "Fasting Glucose (mg/dL)": "fasting_glucose",
    "ICV (mm³)": "icv",
    "GM Vol (mm³)": "gm",
    "WM Vol (mm³)": "wm",
    "L. Hippocampus (mm³)": "l_hipp",
    "R. Hippocampus (mm³)": "r_hipp",
    "WMH Vol (mm³)": "wmh",
    "Total Hipp. (mm³)": "total_hipp",
    "GM/ICV Ratio": "gm_icv",
    "WMH/ICV Ratio": "wmh_icv",
    "Biological Age (yrs)": "chrono_age",
    "Brain Age (yrs)": "brain_age_reported",
    "Brain Age Delta (Δ)": "delta_reported",
}

BIOMARKERS = {
    "hba1c": "HbA1c (%)",
    "fasting_glucose": "Fasting Glucose (mg/dL)",
    "hscrp": "hsCRP (mg/dL)",
    "sbp": "SBP (mmHg)",
    "dbp": "DBP (mmHg)",
    "ldl": "LDL (mg/dL)",
    "triglycerides": "Triglycerides (mg/dL)",
    "gm_icv": "GM / ICV ratio",
    "wmh_icv": "WMH / ICV ratio",
    "total_hipp": "Total hippocampus (mm³)",
}


def load_cohort(path):
    path = Path(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path, sheet_name="Cleaned Data", header=1)
    else:
        df = pd.read_csv(path)
    df = df.rename(columns=COLUMN_MAP)
    df = df.dropna(subset=["age", "icv", "gm"]).reset_index(drop=True)
    if "chrono_age" not in df:
        df["chrono_age"] = df["age"]
    df["sex"] = df["sex"].str.strip().str.lower()
    return df
