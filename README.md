# Brain age from structural MRI and metabolic biomarkers

This pipeline takes a T1-weighted brain MRI and estimates how old the brain looks. It compares that number with the person's real age. Then it checks which blood and vascular markers track with a brain that looks older than it should.

I built it on a cohort of 118 adults who each had a full body MRI and a metabolic blood panel.

No deep learning. Every step is a standard open tool or a simple linear model, so you can see exactly why a subject got the score they got.

## Privacy first

The patient data is not in this repo and never will be.

- No MRI scans, no Excel sheet, no patient IDs. The `.gitignore` blocks `data/raw/`, `data/dicom/`, `data/nifti/`, `data/private/` and the de-identified CSV.
- `scripts/00_anonymize.py` swaps every Study ID for a shuffled code like `SUBJ-001`. It rounds height and weight to the nearest 5. The key that links codes back to real IDs goes to `data/private/` and stays on your machine.
- Anywhere this README mentions a person, they show up as `SUBJ-XXX` or as a synthetic `DEMO` subject.
- To run the code without patient data, `scripts/make_sample_data.py` builds a fake cohort of 118 people. Its numbers are simulated. They are not results.

## How the brain age score works

The idea comes from BrainAGE (Gaser et al., 2013) and brainageR (Cole et al., 2017).

1. Measure the brain. From the MRI we get gray matter, white matter, white matter hyperintensities (WMH, small scars from poor blood flow) and the hippocampus.
2. Divide by head size. Bigger heads hold bigger brains. So every volume is divided by intracranial volume (ICV). That gives four ratios: GM/ICV, WM/ICV, WMH/ICV and Hipp/ICV.
3. Teach a model what normal aging looks like. A Ridge regression learns to predict a person's age from those four ratios. Its output is the **brain age**.
4. Score the gap.

```
Brain Age Delta = Predicted Brain Age - Chronological Age
```

A positive delta means the brain looks older than the person. A negative delta means it looks younger. Near zero means on track.

Each subject is scored by a model that never saw them. This is leave one out cross validation (LOOCV). The model trains on 117 people and predicts the 118th, then repeats for everyone.

Linear brain age models drift toward the average. They make young brains look older and old brains look younger. The code removes that age trend from the delta (Beheshti et al., 2019; de Lange and Cole, 2020). You can turn it off with `--no-bias-correction`.

### A worked example (synthetic data)

These three people come from the fake demo cohort, not from the real one.

| Subject | Sex | Real age | Brain age | Delta | HbA1c | SBP | WMH/ICV |
|---|---|---|---|---|---|---|---|
| DEMO-035 | M | 52 | 44.0 | -8.0 | 5.4 | 107 | 0.0067 |
| DEMO-031 | F | 67 | 66.8 | -0.2 | 5.6 | 128 | 0.0106 |
| DEMO-118 | F | 46 | 58.0 | +12.0 | 6.1 | 142 | 0.0133 |

DEMO-118 is 46 but her brain scores like a 58 year old. She also has the highest HbA1c, blood pressure and WMH load of the three. That is the pattern the pipeline is built to catch.

## Pipeline

| Step | Script | Tool | Output |
|---|---|---|---|
| 0 | `00_anonymize.py` | Python | Coded, de-identified cohort |
| 1 | `01_dicom_to_nifti.sh` | dcm2niix | One `.nii.gz` per subject with a JSON sidecar |
| 1b | `02_check_nifti_qc.py` | Python | QC table of TE, TR, flip angle, field strength |
| 2 | `03_cat12_segmentation.m` | MATLAB, SPM12, CAT12 | Bias correction, skull strip, GM/WM/CSF/WMH segmentation, MNI normalization, ICV, Hammers atlas ROIs |
| 3 | `04_extract_cat12_volumes.py` | Python | One table of volumes from the CAT12 XML reports |
| 4 to 7 | `05_run_analysis.py` | pandas, scikit-learn, SciPy | Ratios, formula checks, brain age, delta, correlations, figures |

The T1 series was picked by hand in an online DICOM viewer. The right series has sharp gray and white matter contrast, about 1 mm voxels and "T1" or "MPRAGE" in its name. Those files were exported into `data/dicom/<subject>/` before step 1.

## What we found in the real cohort (N = 118)

The cohort was 78 men and 40 women aged 21 to 75 (mean 45.6). The numbers below use the brain ages in the original analysis sheet. Run `05_run_analysis.py --use-reported-brain-age` on the de-identified cohort to reproduce them.

Brain age tracked real age closely: r = 0.90 and mean absolute error 3.6 years. Mean delta was +0.34 years (SD 4.95). 57 people (48.3%) had brains that looked older than their age.

| Marker | Pearson r with delta | Strength |
|---|---|---|
| WMH / ICV | +0.59 | strong |
| Total hippocampus | -0.46 | moderate |
| HbA1c | +0.41 | moderate |
| hsCRP | +0.35 | moderate |
| SBP | +0.33 | moderate |
| Fasting glucose | +0.32 | moderate |
| GM / ICV | -0.32 | moderate |
| Triglycerides | +0.10 | negligible |
| LDL | -0.07 | negligible |

All markers rated moderate or strong survived false discovery rate correction (q < 0.05). They also held after controlling for age and sex.

In plain words: the brains that looked older had more white matter scarring and smaller hippocampi. Those same people tended to carry higher blood sugar, more inflammation and higher blood pressure. Cholesterol and triglycerides didn't move the score much.

When the Ridge model in this repo is refit from scratch with LOOCV, it lands at MAE 5.4 years and R² 0.46. WMH (+0.60), hippocampus (-0.47) and HbA1c (+0.34) still lead the list. SBP drops to +0.21. Four MRI ratios on 118 people is a small model, so treat the refit as a check on direction and not as a better score.

## Limits

- 118 people from a single site. No outside test set yet.
- Cross sectional. We see who has an older looking brain, not why it got that way.
- Correlation is not cause. High HbA1c sits next to high WMH. That doesn't prove one drives the other.
- The 21 to 30 group has only 4 people and the 61 to 75 group has 12. Group averages there are noisy.
- CAT12 estimates WMH from T1 alone. A FLAIR scan would measure it better.

## Run it

```bash
pip install -r requirements.txt

# Demo with fake data, no patient files needed
python scripts/make_sample_data.py
python scripts/05_run_analysis.py data/sample_cohort.csv

# With your own data (stays local)
python scripts/00_anonymize.py data/raw/your_cohort.xlsx
python scripts/05_run_analysis.py data/cohort_deidentified.csv
python scripts/05_run_analysis.py data/cohort_deidentified.csv --use-reported-brain-age

# Full imaging pipeline from DICOM
bash scripts/01_dicom_to_nifti.sh data/dicom data/nifti
python scripts/02_check_nifti_qc.py data/nifti
# then in MATLAB: run scripts/03_cat12_segmentation.m
python scripts/04_extract_cat12_volumes.py data/nifti
```

The demo writes its tables and four figures to `outputs/`. The ones committed here come from the synthetic cohort.

## References

- Gaser C. et al. (2013). BrainAGE in mild cognitive impaired patients. PLOS ONE 8(6): e67346.
- Cole J.H. et al. (2017). Predicting brain age with deep learning from raw imaging data. NeuroImage 163: 115-124.
- Franke K. and Gaser C. (2019). Ten years of BrainAGE as a neuroimaging biomarker of brain aging. Frontiers in Neurology 10: 789.
- Beheshti I. et al. (2019). Bias-adjustment in neuroimaging-based brain age frameworks. NeuroImage: Clinical 24: 102063.
- de Lange A.M.G. and Cole J.H. (2020). Commentary: Correction procedures in brain-age prediction. NeuroImage: Clinical 26: 102229.
- Benjamini Y. and Hochberg Y. (1995). Controlling the false discovery rate. JRSS B 57(1): 289-300.
- Hoerl A.E. and Kennard R.W. (1970). Ridge regression. Technometrics 12(1): 55-67.
- Tools: [dcm2niix](https://github.com/rordenlab/dcm2niix), [SPM12](https://www.fil.ion.ucl.ac.uk/spm/software/spm12/), [CAT12](https://neuro-jena.github.io/cat/), [scikit-learn](https://scikit-learn.org).

## Author

Dhiyanesh S

This code is for research and learning. It is not a medical device and should not be used to diagnose anyone.
