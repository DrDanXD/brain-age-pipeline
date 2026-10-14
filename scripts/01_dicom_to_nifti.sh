#!/usr/bin/env bash
# Step 1: Convert T1-weighted DICOM series to NIfTI with dcm2niix.
#
# Expected input layout (one folder per subject, T1 series already selected
# in the DICOM viewer and exported):
#   data/dicom/<subject_id>/*.dcm
#
# Output:
#   data/nifti/<subject_id>/<subject_id>_<protocol>.nii.gz  (+ JSON sidecar)
#
# Requires dcm2niix: https://github.com/rordenlab/dcm2niix
# Usage: bash scripts/01_dicom_to_nifti.sh [dicom_root] [nifti_root]

set -euo pipefail

DICOM_ROOT="${1:-data/dicom}"
NIFTI_ROOT="${2:-data/nifti}"

if ! command -v dcm2niix >/dev/null 2>&1; then
  echo "dcm2niix not found. Install it from https://github.com/rordenlab/dcm2niix" >&2
  exit 1
fi

mkdir -p "$NIFTI_ROOT"

for subj_dir in "$DICOM_ROOT"/*/; do
  subj=$(basename "$subj_dir")
  out_dir="$NIFTI_ROOT/$subj"
  mkdir -p "$out_dir"
  echo "Converting $subj"
  # -z y : gzip output (.nii.gz)
  # -f   : output filename pattern (%i = patient ID, %p = protocol name)
  # -b y : write BIDS JSON sidecar with TE, TR, flip angle, field strength
  dcm2niix -z y -b y -f "${subj}_%p" -o "$out_dir" "$subj_dir"
done

echo "Done. NIfTI files are in $NIFTI_ROOT"
