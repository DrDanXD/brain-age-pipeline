"""Step 7: Figures."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({"figure.dpi": 150, "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False})
BLUE, RED, GREY = "#2E75B6", "#C0392B", "#7F8C8D"


def predicted_vs_actual(df, metrics, path):
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(df["chrono_age"], df["brain_age_raw"], s=18, color=BLUE, alpha=0.7)
    lim = [df["chrono_age"].min() - 3, df["chrono_age"].max() + 3]
    ax.plot(lim, lim, "--", color=GREY, lw=1, label="Identity")
    ax.set(xlim=lim, ylim=lim, xlabel="Chronological age (years)",
           ylabel="Predicted brain age, LOOCV (years)",
           title=f"MAE = {metrics['loocv_mae_years']:.2f} y,  R² = {metrics['loocv_r2']:.2f}")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def delta_histogram(df, path):
    fig, ax = plt.subplots(figsize=(6, 4))
    d = df["brain_age_delta"]
    ax.hist(d, bins=20, color=BLUE, alpha=0.8, edgecolor="white")
    ax.axvline(0, color=GREY, ls="--", lw=1)
    ax.axvline(d.mean(), color=RED, lw=1.5, label=f"Mean = {d.mean():+.2f} y")
    ax.set(xlabel="Brain Age Delta (years)", ylabel="Subjects",
           title=f"Brain Age Delta distribution (N = {len(d)})")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def correlation_bars(corr, path):
    c = corr.sort_values("pearson_r")
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    colors = [RED if r > 0 else BLUE for r in c["pearson_r"]]
    ax.barh(c["variable"], c["pearson_r"], color=colors)
    for y, (r, q) in enumerate(zip(c["pearson_r"], c["q_value_fdr"])):
        mark = "*" if q < 0.05 else ""
        ax.text(r + (0.01 if r >= 0 else -0.01), y, f"{r:+.2f}{mark}",
                va="center", ha="left" if r >= 0 else "right", fontsize=8)
    ax.axvline(0, color=GREY, lw=0.8)
    ax.set(xlabel="Pearson r with Brain Age Delta", xlim=(-1, 1),
           title="Biomarkers vs Brain Age Delta  (* FDR q < 0.05)")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def scatter_panel(df, pairs, path):
    fig, axes = plt.subplots(2, 3, figsize=(11, 6.5))
    for ax, (var, label) in zip(axes.flat, pairs):
        x, y = df[var], df["brain_age_delta"]
        ax.scatter(x, y, s=14, color=BLUE, alpha=0.6)
        m, b = np.polyfit(x, y, 1)
        xs = np.linspace(x.min(), x.max(), 50)
        ax.plot(xs, m * xs + b, color=RED, lw=1.5)
        ax.axhline(0, color=GREY, ls="--", lw=0.8)
        ax.set(xlabel=label, ylabel="Brain Age Delta (y)",
               title=f"r = {np.corrcoef(x, y)[0, 1]:+.2f}")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def make_all(df, metrics, corr, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    predicted_vs_actual(df, metrics, out_dir / "fig1_predicted_vs_actual.png")
    delta_histogram(df, out_dir / "fig2_delta_histogram.png")
    correlation_bars(corr, out_dir / "fig3_biomarker_correlations.png")
    scatter_panel(df, [("wmh_icv", "WMH / ICV"), ("total_hipp", "Total hippocampus (mm³)"),
                       ("hba1c", "HbA1c (%)"), ("hscrp", "hsCRP (mg/dL)"),
                       ("sbp", "SBP (mmHg)"), ("gm_icv", "GM / ICV")],
                  out_dir / "fig4_biomarker_scatter.png")
