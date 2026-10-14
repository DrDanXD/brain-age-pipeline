"""Step 3: Pull volumes out of the CAT12 XML reports into one table.

Reads, per subject:
  report/cat_<name>.xml   -> TIV, absolute CSF / GM / WM / WMH (cm^3)
  label/catROI_<name>.xml -> left and right hippocampus (Hammers atlas, cm^3)

Writes data/cat12_volumes.csv in mm^3 with one row per subject.
Merge this with the clinical/biomarker sheet before step 4.

Usage: python scripts/04_extract_cat12_volumes.py [nifti_root]
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

NIFTI_ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "data/nifti")
OUT = Path("data/cat12_volumes.csv")
CM3_TO_MM3 = 1000.0


def parse_vector(text):
    """CAT12 stores vectors as text like '[426.1 624.3 563.2 4.1 0]'."""
    return [float(x) for x in re.findall(r"-?\d+\.?\d*(?:e-?\d+)?", text or "")]


def read_report(xml_path):
    root = ET.parse(xml_path).getroot()
    tiv = root.find(".//subjectmeasures/vol_TIV")
    cgw = root.find(".//subjectmeasures/vol_abs_CGW")
    vals = parse_vector(cgw.text) if cgw is not None else []
    # vol_abs_CGW order: CSF, GM, WM, WMH (WMH is filled when WMHC is on)
    return {
        "ICV": float(tiv.text) * CM3_TO_MM3 if tiv is not None else None,
        "CSF": vals[0] * CM3_TO_MM3 if len(vals) > 0 else None,
        "GM": vals[1] * CM3_TO_MM3 if len(vals) > 1 else None,
        "WM": vals[2] * CM3_TO_MM3 if len(vals) > 2 else None,
        "WMH": vals[3] * CM3_TO_MM3 if len(vals) > 3 else None,
    }


def read_hippocampus(xml_path, atlas="hammers"):
    root = ET.parse(xml_path).getroot()
    node = root.find(atlas)
    if node is None:
        return {"L_Hipp": None, "R_Hipp": None}
    names = [n.text for n in node.findall("./names/item")]
    vgm = parse_vector(node.find("./data/Vgm").text)
    out = {"L_Hipp": None, "R_Hipp": None}
    for name, vol in zip(names, vgm):
        low = name.lower()
        if "hippocamp" not in low:
            continue
        if low.startswith("l") or "left" in low:
            out["L_Hipp"] = vol * CM3_TO_MM3
        elif low.startswith("r") or "right" in low:
            out["R_Hipp"] = vol * CM3_TO_MM3
    return out


def main():
    rows = []
    for report in sorted(NIFTI_ROOT.rglob("report/cat_*.xml")):
        name = report.stem.replace("cat_", "", 1)
        subj = report.parents[1].name
        row = {"subject": subj, "scan": name, **read_report(report)}
        roi = report.parents[1] / "label" / f"catROI_{name}.xml"
        row.update(read_hippocampus(roi) if roi.exists() else {"L_Hipp": None, "R_Hipp": None})
        rows.append(row)

    if not rows:
        print(f"No CAT12 reports found under {NIFTI_ROOT}. Run step 2 first.")
        return

    df = pd.DataFrame(rows)
    df["Total_Hipp"] = df["L_Hipp"] + df["R_Hipp"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Extracted volumes for {len(df)} subjects -> {OUT}")
    print(df.isna().sum()[df.isna().sum() > 0].to_string() or "No missing values")


if __name__ == "__main__":
    main()
