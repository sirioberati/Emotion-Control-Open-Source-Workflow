# Final tech stack, processing steps and material layers

This maps the actual executable `approved-sculpted-glossy-v1` implementation to its dependencies and outputs. The code is the source of truth. `preset.json` records the approved constants; it is not a runtime configuration loader.

## Scope

The repository contains the complete custom **video-to-performance-mask pipeline**, its runner, renderer, asset preparation, dependency versions and setup instructions. External code is fetched at pinned commits. Licensed model weights are obtained separately.

Seedance is the downstream generator used for the supplied performance-transfer results. This repository includes those results and documents the handoff, but does **not** contain Seedance's proprietary model or a provider-specific API submission client. The HTML social reel and discarded prototype renderers are not dependencies of this final mask workflow.

## Runtime stack

| Component | Role | Where to find it |
| --- | --- | --- |
| Python 3.12 | Pipeline runner and seven processing stages | `run.py`, `scripts/` |
| FFmpeg / ffprobe | Normalize footage, encode/mux audio, crop mask, validate exports, generate README GIFs | PATH or `FFMPEG` / `FFPROBE` overrides |
| MediaPipe Face Landmarker | 478 face/iris landmarks, 52 blendshape coefficients and head transformation | `scripts/prepare.py`; model downloaded with checksum verification |
| SPECTRE | Temporal expression, jaw, pose, camera and identity-shape estimates | Pinned `models/spectre`; checkpoint obtained separately |
| PyTorch / torchvision | CPU inference with SPECTRE ResNet50/MobileNetV2 encoders and FLAME decoding | Versioned in `requirements.txt` |
| FLAME 2020 via SMIRK | Parametric face geometry, shape/expression basis and landmark embedding | Pinned `models/smirk`; licensed FLAME model obtained separately |
| NumPy / SciPy | Arrays, within-shot smoothing, sparse constrained surface solve | `scripts/fit.py` and processing stages |
| OpenCV | Frame decoding, crop/warp, UV transfer, source detail, normal-map gradients, masks and point drawing | Processing and rendering stages |
| Numba | Compiled CPU triangle rasterization, UV interpolation and normal buffers | `scripts/raster.py`, `scripts/render.py` |
| PyAV | Frame-timed H.264 intermediate video encoding | Fit/detail/render stages |
| scikit-image | SPECTRE input crop transforms and warps | `scripts/infer.py` |
| chumpy + compatibility aliases | Loading legacy FLAME data in the current Python/NumPy runtime | Decode/fit setup |

Direct package versions: [requirements.txt](../requirements.txt). The original complete environment snapshot is recorded separately in [original-environment.txt](original-environment.txt). Only the dependencies needed by this workflow are installed by the main requirements file.

SMIRK supplies the FLAME decoder and support assets here; the active inference branch is **SPECTRE**, not SMIRK's expression network. The wrapper does not require Blender, Three.js, GSAP, HyperFrames, PyTorch3D, or an external emotion-classification service.

## Seven executable stages

`run.py` invokes these in order. Each successful stage gets an ignored `_work/<stage>.done` stamp. A saved configuration and log accompany the outputs.

| Stage | What actually happens | Principal intermediate/output |
| --- | --- | --- |
| 1. `prepare.py` | Normalize to 30 fps and max width 1920, preserve aspect ratio/audio; track one face; reset at detected cuts; construct 1024-square UV relief and gloss | `source.mp4`, `points.npz`, `Blendshapes.json`, `shots.npy`, `maps/fused.npz`, `maps/uvrelief`, `maps/uvgloss` |
| 2. `infer.py` | Crop to 224-square encoder input; infer SPECTRE shape, expression, pose, jaw and camera; pad temporal features at each shot boundary | `spectre-full-params.npz` |
| 3. `decode.py` | Decode FLAME vertices with median identity shape per input, unless the caller explicitly supplies a matching identity reference | `spectre-full-geometry.npz` |
| 4. `fit.py` | Lightly smooth the 3D prior within shots; constrain 105 barycentric features and 56 boundary vertices against per-frame tracked targets; solve using topology regularization; preserve estimated Z | `full-test/Corrected-geometry.npz`, `Clean-clay.npz`, landmark-correction video and fitting diagnostics |
| 5. `detail.py` | Add local grayscale appearance residual; restore feathered, locally normalized eyes, lips and brows; reset appearance statistics at cuts; fall back to clay outside visible source pixels | `full-test/Detail-assisted-test-silent.mp4` |
| 6. `package_detail.py` | Assemble source/detail comparison and attach original audio when present | `full-test/Original-and-detailed-mesh.mp4` |
| 7. `render.py` | Transfer UV maps, recompute normal buffers, apply approved clay/light/bump/gloss layers and tracked green points; export comparisons and isolated mask; verify streams | Three final MP4s, `Validation.json`, `Map-effect-stats.json` |

Native output: 512 × 512 mask, 30 fps; source/mask comparison: 1024 × 568. The pipeline stops if no face can be tracked. It does not invent a replacement face for missed frames.

The inherited final log sentence in `decode.py` mentions “original pilot identity”; the executable logic directly above it uses the **current input's median shape by default**. This historical log wording does not change the implementation.

## Material layers, in code order

These are computed image/geometry layers, not separate Photoshop files. Their intermediate arrays and videos stay under `_work/` for review.

1. **Tracked geometry and clean clay.** SPECTRE/FLAME prior plus constrained feature/contour fitting. The custom CPU rasterizer produces the base clay face and normal field.
2. **Source grayscale detail.** High-frequency luminance residual over the clean face; separately normalized, feathered eye/lip/brow regions preserve expression readability.
3. **UV relief.** Source luminance bandpass is projected through canonical face UV triangles into 1024 × 1024 maps, neutral at 127.5. Out-of-frame triangles are neutral. This is estimated appearance detail, not measured depth.
4. **UV gloss.** Local bright peaks plus eye-region response are transferred into a separate 1024 × 1024 map. Mapping and visibility masks prevent unsupported source regions from adding detail.
5. **View-space bump.** Relief gradients perturb shading normals with a scale of 1.5. The mesh vertices are not displaced. Bump diffuse differences are clamped and combined with a small crease-darkening term.
6. **Clay/source blend.** Clay weight is **0.84** on skin and **0.10** in protected feature regions. Feature masks are dilated/feathered; the estimated face silhouette controls coverage.
7. **Directional lighting.** Normalized light direction **[-0.60, 0.45, 0.66]**, ambient **34**, diffuse gain **166**, plus a small half-vector highlight and rim response. Lighting is added to the detailed clay blend.
8. **Gloss-driven roughness.** Roughness is **0.36 − 0.17 × gloss**, with specular exponent **2 / roughness² − 2**.
9. **Clear coat and mapped shine.** Broad coat gain **58**, exponent **30**; mapped shine gain **65**. A feathered mouth mask suppresses added shine over mouth/teeth; protected features receive reduced shine.
10. **Porcelain tint and final range.** Small BGR multiplier offsets **[-0.025, -0.006, 0.012]**, restricted to the face; final intensity clipped to 0–250.
11. **478 tracked points.** Green anti-aliased points are drawn from the current frame's tracked locations. They visualize tracking; extra points do not create extra recovered detail.
12. **Presentation and source audio.** Black background, comparison labels, isolated crop, and original audio where available. Export validation checks frame counts, fps, audio presence and duration.

See [render.py](../scripts/render.py), [detail.py](../scripts/detail.py) and [preset.json](../preset.json) for all constants and equations. Layer details above describe the final implementation; they do not imply measured tears, emotion scores or a photogrammetry scan.

## Exact assets and reproducibility

- `tools/fetch_public_assets.py` fetches pinned SPECTRE/SMIRK code and checksum-verified MediaPipe assets.
- `tools/prepare_assets.py` reconstructs the approved 5,584-face render subset and 56 boundary indices from locally licensed FLAME data. It validates topology hashes.
- `config/asset-selection.json` records the exact selections, including the 852 canonical triangles used for relief mapping.
- `tools/check_setup.py` checks dependency/asset presence. It does not replace a real inference pilot.
- New clips derive their own identity. The old actor-specific identity file, private logs, credentials, runtime and model weights are excluded from Git.
- Optional `--reuse-tracking`, `--map-project`, and `--identity-reference` are documented in the setup guide; they require matching inputs. They are not defaults for new videos.

[Provenance](PROVENANCE.md) and [release validation](release-validation.json) describe the exact preservation checks and the successful fresh 12-frame end-to-end pilot. This was tested with the existing local runtime and model assets, not a clean installation on every operating system.

## Seedance handoff and the supplied example

1. Extract and review the mask from the raw source performance.
2. Give the generator the mask as the facial-performance reference.
3. Supply Sirio's separate appearance reference as the identity/appearance guide.
4. Specify the desired speaker/voice and original dialogue timing separately; a listening reaction should not lip-sync another speaker.
5. Generate in the chosen Seedance interface/provider and inspect the result against the source.

The new expressive gallery uses the exact original named in the mask run manifest (`1008(5).mp4`), the approved mask, and the user-supplied Seedance result. The original/mask run approximately 21.47 seconds at 30 fps; the generated delivery is approximately 22.08 seconds at 24 fps. Full files are preserved unchanged. This release does not claim their timing is frame-perfect or reconstruct generation parameters from an MP4 filename.

Provider-specific prompts, generation settings and API automation are not included for that supplied download because its generation receipt was not supplied. No paid submission is made by the extraction code.

## Licenses

Original wrapper/docs: MIT. Third-party code/assets keep their own terms; FLAME and SPECTRE have noncommercial/research restrictions. Follow [SETUP.md](SETUP.md) and [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). Open wrapper source does not mean every required model is bundled or unrestricted.
