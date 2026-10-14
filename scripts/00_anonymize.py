"""Step 0: De-identify the cohort before any analysis or sharing.

- Replaces every Study ID with a code like SUBJ-001 (order shuffled, so the
  code says nothing about the original ID or row order)
- Drops the Patient ID Reference sheet entirely (it is never read)
- Rounds height and weight to the nearest 5 so they can't be matched back
- Writes the ID key to data/private/id_key.csv, which is git-ignored.
  Keep that file off GitHub. Delete it if you don't need to re-link.

Usage: python scripts/00_anonymize.py data/raw/MRI_BrainAge_Complete.xlsx
Output: data/cohort_deidentified.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data import COLUMN_MAP  # noqa: E402

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else "data/raw/MRI_BrainAge_Complete.xlsx")
OUT = Path("data/cohort_deidentified.csv")
KEY = Path("data/private/id_key.csv")
SEED = 20260107


def main():
    if SRC.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(SRC, sheet_name="Cleaned Data", header=1)
    else:
        df = pd.read_csv(SRC)
    df = df.dropna(subset=["Age (yrs)"]).reset_index(drop=True)

    rng = np.random.default_rng(SEED)
    order = rng.permutation(len(df))
    codes = [f"SUBJ-{i + 1:03d}" for i in range(len(df))]
    new_ids = pd.Series(codes, index=order).sort_index().to_numpy()

    KEY.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"original_id": df["Study ID"], "subject_code": new_ids}).to_csv(KEY, index=False)

    df["Study ID"] = new_ids
    for col in ["Height (cm)", "Weight (kg)"]:
        if col in df:
            df[col] = (df[col] / 5).round() * 5

    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)
    keep = [c for c in COLUMN_MAP if c in df.columns]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df[keep].to_csv(OUT, index=False)
    print(f"De-identified {len(df)} subjects -> {OUT}")
    print(f"ID key (do NOT upload) -> {KEY}")


if __name__ == "__main__":
    main()
