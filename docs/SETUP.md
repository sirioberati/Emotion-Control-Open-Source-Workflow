# Install the final mask workflow

This package preserves the approved rendering and fitting implementation. The original runtime was macOS with Python 3.12. The packaged code is tested against that existing runtime; a fresh environment on every OS is not certified.

## 1. Python and FFmpeg

Install Python 3.12 and FFmpeg through your OS package manager. On macOS with Homebrew:

```bash
brew install python@3.12 ffmpeg
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
ffmpeg -version
ffprobe -version
```

`requirements.txt` pins direct packages from the working environment. `docs/original-environment.txt` records the entire original environment for diagnosis; it contains unrelated packages and is not the installation list. If a pinned build is unavailable on your platform, report that instead of silently changing versions and claiming equivalence. The wrapper uses a custom CPU rasterizer; PyTorch3D, the SMIRK inference checkpoint, and training datasets are not needed.

`FFMPEG` and `FFPROBE` environment variables may specify alternative executable paths.

## 2. Public upstream code and MediaPipe assets

```bash
python tools/fetch_public_assets.py
```

This fetches SPECTRE and SMIRK at pinned commits and downloads two checksum-verified MediaPipe files. It does not run upstream installation scripts, request credentials or fetch licensed FLAME weights. Existing checkouts with a different commit are left unchanged with an error.

- SPECTRE: `0b339a8486ab0869466d145628be03c56eb6c2b9`
- SMIRK: `c7de404c4389f073906a6db1adabf62efcea3f35`

The required encoder/FLAME source modules and SMIRK support assets were compared byte-for-byte with the approved local copies and matched.

## 3. Obtain model files separately

Read [the third-party notices](../THIRD_PARTY_NOTICES.md) before using the model stack.

### FLAME 2020

Register at [the official FLAME site](https://flame.is.tue.mpg.de/), accept the applicable terms and obtain FLAME 2020 through its official download flow. Extract `generic_model.pkl` to:

```text
models/smirk/assets/FLAME2020/generic_model.pkl
```

Use the approved FLAME 2020 topology. Do not substitute FLAME 2023, upload the model here, or commit credentials. The required landmark embedding and eyelid arrays are supplied by the pinned SMIRK repository.

### SPECTRE checkpoint

Follow the pretrained-model link in the [official SPECTRE installation script](https://github.com/filby89/spectre/blob/0b339a8486ab0869466d145628be03c56eb6c2b9/quick_install.sh). Put the official checkpoint at:

```text
models/spectre/pretrained/spectre_model.tar
```

The upstream Google Drive file ID is `1vmWX6QmXGPnXTXWFgj67oHzOoOmxBh6B`. If downloading manually, verify that you saved the checkpoint, not a login or quota HTML page. Only load checkpoints from the official source. The workflow uses `torch.load(..., weights_only=True)` for this checkpoint; FLAME's upstream loader uses pickle, so its model must also come from the trusted official source.

## 4. Prepare exact topology and verify setup

```bash
python tools/prepare_assets.py
python tools/check_setup.py
```

The preparation tool reconstructs the approved 5,584-face subset and 56 outline indices locally using `config/asset-selection.json`. It verifies topology and canonical-mesh hashes. No FLAME vertices, identity coefficients or licensed model weights are distributed in this repository. The MediaPipe triangle filter excludes pilot-specific iris recordings.

## 5. Render and inspect a short pilot

```bash
python run.py "/absolute/path/to/raw-performance.mp4" \
  --start 4 --duration 3 --output outputs/pilot
```

Choose a start time within your own source. Read `outputs/pilot/Run.log` if a stage fails. Review all three MP4s and `Validation.json`. Confirm expressions change, blinks and mouth closure remain readable, source/mask timing matches, and audio is correct. A setup check only checks presence, not model compatibility or tracking quality.

Then run the full source into a new output directory. `--resume` is only for the same unchanged run: it reuses saved configuration and completed-stage stamps. Do not use it to apply a new trim, source file, model or renderer setting.

Advanced options: `python run.py --help`. Reusing tracking, UV maps or an identity reference requires the exact matching person, dimensions, frame timing and source. Fresh inputs derive a median identity shape per clip by default.

## Optional generation handoff

Use the mask as the performance reference and a separate portrait/video as the appearance reference in your chosen generator. Keep voice and dialogue references explicit. No provider SDK, paid generation or API credential is required for mask extraction. The gallery's generated results illustrate that separate step.
