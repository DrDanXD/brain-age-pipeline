"""Steps 4 to 7: features, brain age model, biomarker correlations, figures.

Usage:
  python scripts/05_run_analysis.py data/cohort_deidentified.csv
  python scripts/05_run_analysis.py data/sample_cohort.csv   # synthetic demo

Outputs (in outputs/):
  formula_checks.csv        derived-column checks on the input sheet
  model_metrics.csv         LOOCV MAE, R², bias correction, delta summary
  model_weights.csv         standardized Ridge weights
  subject_brain_age.csv     per subject: age, brain age, delta (coded IDs only)
  biomarker_correlations.csv  Pearson, Spearman, FDR q-values
  biomarker_partial_corr.csv  same, controlling for age and sex
  delta_by_age_group.csv, delta_by_sex.csv
  figures/*.png
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data import BIOMARKERS, load_cohort  # noqa: E402
from src.features import MODEL_FEATURES, add_features, verify_formulas  # noqa: E402
from src.model import run_brain_age, use_reported_brain_age  # noqa: E402
from src.plots import make_all  # noqa: E402
from src.stats import correlate, partial_correlate, summarize_groups  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cohort", nargs="?", default="data/sample_cohort.csv")
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--alpha", type=float, default=1.0)
    ap.add_argument("--no-bias-correction", action="store_true")
    ap.add_argument("--use-reported-brain-age", action="store_true",
                    help="Skip the model and use the Brain Age column in the sheet")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 140)

    raw = load_cohort(args.cohort)
    checks = verify_formulas(raw)
    checks.to_csv(out / "formula_checks.csv", index=False)
    print("Formula checks\n", checks.to_string(index=False), "\n")

    df = add_features(raw)
    if args.use_reported_brain_age:
        df, metrics = use_reported_brain_age(df)
        coefs = None
        print(f"Brain age taken from the sheet (N={metrics['n_subjects']})")
    else:
        df, metrics, coefs = run_brain_age(df, MODEL_FEATURES, alpha=args.alpha,
                                           correct_bias=not args.no_bias_correction)
        coefs.to_csv(out / "model_weights.csv", index=False)
        print(f"Brain age model (Ridge, alpha={args.alpha}, LOOCV, N={metrics['n_subjects']})")
    pd.DataFrame([metrics]).to_csv(out / "model_metrics.csv", index=False)
    print(f"  MAE {metrics['loocv_mae_years']:.2f} y | R² {metrics['loocv_r2']:.2f} | "
          f"r {metrics['loocv_r_pred_vs_age']:.2f}")
    print(f"  Delta mean {metrics['mean_delta']:+.2f} ± {metrics['sd_delta']:.2f} y | "
          f"{metrics['n_delta_positive']} subjects ({metrics['pct_delta_positive']:.1f}%) older than their age\n")
    if coefs is not None:
        print(coefs.to_string(index=False), "\n")

    cols = ["subject", "sex", "chrono_age", "brain_age_raw", "brain_age", "brain_age_delta"]
    df[cols].round(2).to_csv(out / "subject_brain_age.csv", index=False)

    vars_ = [v for v in BIOMARKERS if v in df]
    corr = correlate(df, "brain_age_delta", vars_, BIOMARKERS)
    corr.round(4).to_csv(out / "biomarker_correlations.csv", index=False)
    print("Biomarkers vs Brain Age Delta\n", corr.round(3).to_string(index=False), "\n")

    pcorr = partial_correlate(df, "brain_age_delta", vars_, ["chrono_age", "sex"], BIOMARKERS)
    pcorr.round(4).to_csv(out / "biomarker_partial_corr.csv", index=False)
    print("Controlling for age and sex\n", pcorr.round(3).to_string(index=False), "\n")

    by_age, by_sex = summarize_groups(df)
    by_age.round(4).to_csv(out / "delta_by_age_group.csv", index=False)
    by_sex.round(4).to_csv(out / "delta_by_sex.csv", index=False)
    print(by_age.round(3).to_string(index=False), "\n")
    print(by_sex.round(3).to_string(index=False), "\n")

    make_all(df, metrics, corr, out / "figures")
    print(f"All outputs written to {out}/")


if __name__ == "__main__":
    main()
