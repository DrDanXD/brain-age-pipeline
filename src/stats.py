"""Step 6: Correlate Brain Age Delta with biomarkers."""
import numpy as np
import pandas as pd
from scipy import stats


def strength(r):
    a = abs(r)
    if a >= 0.5:
        return "strong"
    if a >= 0.3:
        return "moderate"
    if a >= 0.1:
        return "weak"
    return "negligible"


def fdr_bh(pvals):
    """Benjamini-Hochberg FDR correction (Benjamini & Hochberg, 1995)."""
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order] * n / np.arange(1, n + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    q = np.empty(n)
    q[order] = np.clip(ranked, 0, 1)
    return q


def correlate(df, target, variables, labels):
    rows = []
    for var in variables:
        sub = df[[target, var]].dropna()
        r, p = stats.pearsonr(sub[target], sub[var])
        rho, p_s = stats.spearmanr(sub[target], sub[var])
        rows.append({"variable": labels.get(var, var), "n": len(sub),
                     "pearson_r": r, "p_value": p, "spearman_rho": rho,
                     "strength": strength(r), "direction": "positive" if r > 0 else "negative"})
    out = pd.DataFrame(rows)
    out["q_value_fdr"] = fdr_bh(out["p_value"])
    return out.sort_values("pearson_r", key=abs, ascending=False).reset_index(drop=True)


def partial_correlate(df, target, variables, covariates, labels):
    """Correlation after regressing covariates (e.g. age, sex) out of both sides.

    Brain Age Delta is known to correlate with age itself, so a raw correlation
    with an age-related biomarker can be partly an age effect. This controls
    for that.
    """
    rows = []
    cov = pd.get_dummies(df[covariates], drop_first=True).astype(float)
    C = np.column_stack([np.ones(len(df)), cov.to_numpy()])

    def resid(v):
        beta, *_ = np.linalg.lstsq(C, v, rcond=None)
        return v - C @ beta

    t = resid(df[target].to_numpy(dtype=float))
    for var in variables:
        r, p = stats.pearsonr(t, resid(df[var].to_numpy(dtype=float)))
        rows.append({"variable": labels.get(var, var), "partial_r": r, "p_value": p})
    out = pd.DataFrame(rows)
    out["q_value_fdr"] = fdr_bh(out["p_value"])
    return out.sort_values("partial_r", key=abs, ascending=False).reset_index(drop=True)


def summarize_groups(df):
    bins = [20, 30, 40, 50, 60, 75]
    labels = ["21-30", "31-40", "41-50", "51-60", "61-75"]
    g = df.assign(age_group=pd.cut(df["chrono_age"], bins=bins, labels=labels))
    by_age = g.groupby("age_group", observed=True).agg(
        n=("subject", "size"), mean_delta=("brain_age_delta", "mean"),
        sd_delta=("brain_age_delta", "std"), mean_wmh_icv=("wmh_icv", "mean")).reset_index()
    by_sex = df.groupby("sex").agg(
        n=("subject", "size"), mean_delta=("brain_age_delta", "mean"),
        sd_delta=("brain_age_delta", "std"), mean_hba1c=("hba1c", "mean"),
        mean_wmh_icv=("wmh_icv", "mean"), mean_gm_icv=("gm_icv", "mean"),
        mean_total_hipp=("total_hipp", "mean")).reset_index()
    return by_age, by_sex
