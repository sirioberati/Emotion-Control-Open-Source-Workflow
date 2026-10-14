# Final implementation and release checks

This is the approved October 8, 2026 `approved-sculpted-glossy-v1` workflow, packaged for publication on October 14, 2026. It is the facial-performance extraction/rendering framework shown in the demos, not the HTML social reel.

## What changed for publication

- Python stages use the interpreter running `run.py` instead of a hardcoded `.runtime` path.
- FFmpeg/ffprobe are resolved from PATH or explicit environment overrides instead of `/opt/homebrew/bin`.
- A setup preflight reports missing dependencies and assets before processing.
- A local asset-preparation tool reconstructs the approved face subset using explicit indices and hash checks. Licensed FLAME geometry is not distributed.
- The MediaPipe topology asset includes only the triangle set used by the renderer. Pilot-specific iris trajectories and actor identity are not distributed.
- Added setup tools, examples, GIF generation, TEIN branding, documentation and license scope.

`infer.py`, `decode.py`, `fit.py`, `detail.py` and `raster.py` are byte-identical to the approved source. `prepare.py`, `package_detail.py` and `render.py` differ only in executable discovery. `preset.json` is unchanged. Original source hashes are in `original-source-sha256.json`.

## Upstream reproducibility

The required encoder/FLAME source files and SMIRK landmark/eyelid assets were compared against pinned upstream commits and matched byte-for-byte. Public MediaPipe downloads were checked against the approved local file hashes. The locally reconstructed FLAME face subset matches the approved subset hash; the renderer's MediaPipe triangle set is identical.

## Validation actually performed

- Parsed all publication Python files and checked preservation of approved fitting/rendering math.
- Fresh 0.4-second, 12-frame source excerpt at 4 seconds: prepare, MediaPipe tracking, UV maps, SPECTRE inference, FLAME decode, constrained fitting, source detail, final render and audio export completed.
- Checked all output streams for 30 fps, frame count, dimensions and audio duration; see `release-validation.json`.
- Probed both full supplied comparison MP4s, both matching mask MP4s and all four GIFs. Technical metadata and hashes are in `examples/manifest.json`.
- Reviewed rendered sample frames and GIF motion. Full example MP4s were copied without re-encoding.

The pilot uses the existing verified local macOS Python runtime and locally obtained model assets. It is not a fresh-install, Windows/Linux, long-video or production robustness certification. The historical pilot report is preserved separately as `original-verification.json`.
