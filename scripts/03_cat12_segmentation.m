% Step 2: SPM12 + CAT12 preprocessing for every subject.
%
% Runs CAT12 segmentation, which covers:
%   - bias field correction
%   - skull stripping
%   - tissue segmentation into GM, WM, CSF (+ WMH as its own class)
%   - spatial normalization to MNI152 (SHOOT)
%   - TIV / ICV estimation
%   - ROI volumes from the Hammers atlas (used for hippocampus)
%
% Outputs per subject (next to the NIfTI):
%   report/cat_<name>.xml   -> TIV and absolute CSF/GM/WM/WMH volumes
%   label/catROI_<name>.xml -> atlas ROI volumes (hippocampus)
%   mri/mwp1*, mwp2*        -> modulated normalized GM and WM maps
%
% Requirements: MATLAB, SPM12 and CAT12 on the MATLAB path.
% Usage: edit NIFTI_ROOT below, then run this file in MATLAB.

NIFTI_ROOT = fullfile(pwd, 'data', 'nifti');
N_CORES    = 4;

spm('defaults', 'FMRI');
spm_jobman('initcfg');

% CAT12 needs uncompressed .nii, so unzip any .nii.gz first
gz = dir(fullfile(NIFTI_ROOT, '**', '*.nii.gz'));
for k = 1:numel(gz)
    gunzip(fullfile(gz(k).folder, gz(k).name));
end

files = dir(fullfile(NIFTI_ROOT, '**', '*.nii'));
files = files(~startsWith({files.name}, {'mwp', 'wm', 'p0', 'y_', 'iy_'}));
vols  = cellfun(@(f, n) [fullfile(f, n) ',1'], {files.folder}, {files.name}, ...
                'UniformOutput', false)';

fprintf('Found %d T1 volumes\n', numel(vols));

matlabbatch = {};
matlabbatch{1}.spm.tools.cat.estwrite.data = vols;
matlabbatch{1}.spm.tools.cat.estwrite.nproc = N_CORES;
matlabbatch{1}.spm.tools.cat.estwrite.opts.tpm = ...
    {fullfile(spm('dir'), 'tpm', 'TPM.nii')};
matlabbatch{1}.spm.tools.cat.estwrite.opts.affreg = 'mni';

% Treat WMH as a separate tissue class so its volume is reported
matlabbatch{1}.spm.tools.cat.estwrite.extopts.segmentation.WMHC = 2;

% ROI atlas for hippocampal volumes
matlabbatch{1}.spm.tools.cat.estwrite.output.ROImenu.atlases.hammers = 1;
matlabbatch{1}.spm.tools.cat.estwrite.output.ROImenu.atlases.neuromorphometrics = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.ROImenu.atlases.lpba40 = 0;

% Modulated normalized GM and WM maps
matlabbatch{1}.spm.tools.cat.estwrite.output.GM.mod = 1;
matlabbatch{1}.spm.tools.cat.estwrite.output.WM.mod = 1;
matlabbatch{1}.spm.tools.cat.estwrite.output.surface = 0;

spm_jobman('run', matlabbatch);
fprintf('CAT12 finished. Next: python scripts/04_extract_cat12_volumes.py\n');
