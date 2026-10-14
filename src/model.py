"""Step 5: Ridge Regression brain age model with leave-one-out CV.

Follows the BrainAGE (Gaser et al., 2013) and brainageR (Cole et al., 2017)
idea: learn chronological age from structural features, then read the
model's prediction as "brain age".

Every subject's brain age is predicted by a model that never saw that
subject (LOOCV), so the predictions are out of sample.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def build_model(alpha=1.0):
    # Scaling sits inside the pipeline so each LOOCV fold is scaled using
    # only its own training subjects (no leakage from the held-out subject).
    return make_pipeline(StandardScaler(), Ridge(alpha=alpha))


def bias_correct(pred, age):
    """Remove the age-dependence of Brain Age Delta.

    Brain age models regress toward the cohort mean: they overestimate young
    brains and underestimate old ones, so the raw delta correlates with age.
    Fix (Beheshti et al., 2019; de Lange & Cole, 2020): fit
    delta = a*age + b and subtract that trend. This keeps delta in years
    without the variance blow-up you get from dividing by a weak slope.
    With an independent test cohort, fit a and b on training data only.
    """
    delta = pred - age
    a, b = np.polyfit(age, delta, 1)
    corrected_delta = delta - (a * age + b)
    return age + corrected_delta, a, b


def run_brain_age(df, features, alpha=1.0, correct_bias=True):
    X = df[features].to_numpy()
    y = df["chrono_age"].to_numpy(dtype=float)

    pred_raw = cross_val_predict(build_model(alpha), X, y, cv=LeaveOneOut())

    out = df.copy()
    out["brain_age_raw"] = pred_raw
    if correct_bias:
        corrected, a, b = bias_correct(pred_raw, y)
        out["brain_age"] = corrected
    else:
        out["brain_age"] = pred_raw
        a, b = 1.0, 0.0
    out["brain_age_delta"] = out["brain_age"] - y

    metrics = {
        "brain_age_source": "ridge_loocv",
        "n_subjects": len(df),
        "features": ", ".join(features),
        "alpha": alpha,
        "loocv_mae_years": mean_absolute_error(y, pred_raw),
        "loocv_r2": r2_score(y, pred_raw),
        "loocv_r_pred_vs_age": float(np.corrcoef(y, pred_raw)[0, 1]),
        "bias_slope": a,
        "bias_intercept": b,
        "mean_delta": out["brain_age_delta"].mean(),
        "sd_delta": out["brain_age_delta"].std(),
        "pct_delta_positive": 100 * (out["brain_age_delta"] > 0).mean(),
    }

    # Weights of a model fit on everyone, for interpretation only
    full = build_model(alpha).fit(X, y)
    coefs = pd.DataFrame({
        "feature": features,
        "standardized_weight_years": full.named_steps["ridge"].coef_,
    })
    metrics["intercept_years"] = float(full.named_steps["ridge"].intercept_)
    metrics["n_delta_positive"] = int((out["brain_age_delta"] > 0).sum())
    return out, metrics, coefs


def use_reported_brain_age(df):
    """Use the Brain Age column already in the sheet instead of refitting.

    This reproduces the original analysis numbers exactly.
    """
    out = df.copy()
    y = out["chrono_age"].to_numpy(dtype=float)
    out["brain_age_raw"] = out["brain_age_reported"]
    out["brain_age"] = out["brain_age_reported"]
    out["brain_age_delta"] = out["brain_age"] - y
    pred = out["brain_age"].to_numpy(dtype=float)
    metrics = {
        "brain_age_source": "reported_in_sheet",
        "n_subjects": len(out),
        "mae_years": mean_absolute_error(y, pred),
        "r2": r2_score(y, pred),
        "r_pred_vs_age": float(np.corrcoef(y, pred)[0, 1]),
        "mean_delta": out["brain_age_delta"].mean(),
        "sd_delta": out["brain_age_delta"].std(),
        "pct_delta_positive": 100 * (out["brain_age_delta"] > 0).mean(),
        "n_delta_positive": int((out["brain_age_delta"] > 0).sum()),
    }
    # Aliases so plots and printouts work in both modes
    metrics["loocv_mae_years"] = metrics["mae_years"]
    metrics["loocv_r2"] = metrics["r2"]
    metrics["loocv_r_pred_vs_age"] = metrics["r_pred_vs_age"]
    return out, metrics
