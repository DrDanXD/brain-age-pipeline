"""Step 1b: QC the dcm2niix output by reading each JSON sidecar.

Flags subjects whose acquisition parameters are missing or look off.
Writes outputs/nifti_qc.csv.

Usage: python scripts/02_check_nifti_qc.py [nifti_root]
"""
import json
import sys
from pathlib import Path

import pandas as pd

NIFTI_ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "data/nifti")
OUT = Path("outputs/nifti_qc.csv")

FIELDS = ["EchoTime", "RepetitionTime", "FlipAngle", "MagneticFieldStrength",
          "Manufacturer", "SeriesDescription"]


def main():
    rows = []
    for subj_dir in sorted(p for p in NIFTI_ROOT.iterdir() if p.is_dir()):
        sidecars = list(subj_dir.glob("*.json"))
        niftis = list(subj_dir.glob("*.nii*"))
        row = {"subject": subj_dir.name, "n_nifti": len(niftis)}
        if sidecars:
            meta = json.loads(sidecars[0].read_text())
            for f in FIELDS:
                row[f] = meta.get(f)
        missing = [f for f in FIELDS[:4] if row.get(f) is None]
        is_t1 = "t1" in str(row.get("SeriesDescription", "")).lower()
        row["qc_pass"] = len(niftis) == 1 and not missing and is_t1
        row["qc_note"] = "; ".join(
            ([f"missing {', '.join(missing)}"] if missing else [])
            + ([] if is_t1 else ["series name not T1"])
            + ([] if len(niftis) == 1 else [f"{len(niftis)} NIfTI files"])
        )
        rows.append(row)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)
    print(f"{df['qc_pass'].sum()}/{len(df)} subjects passed QC -> {OUT}")


if __name__ == "__main__":
    main()
