# Third-party notices

The MIT license applies to this repository's original wrapper code and documentation. It does not relicense the complete model stack.

| Component | Source | Terms and use here |
| --- | --- | --- |
| SPECTRE | [filby89/spectre](https://github.com/filby89/spectre) | CC BY-NC-SA 4.0 in the pinned repository. Expression inference code/checkpoint are fetched separately; retain upstream notices. |
| SMIRK | [georgeretsi/smirk](https://github.com/georgeretsi/smirk) | Root code license is MIT, copyright George Retsinas. Nested FLAME components have separate MPG notices; do not assume the root license replaces them. Used for FLAME decoding and support assets. |
| FLAME 2020 | [Official FLAME site](https://flame.is.tue.mpg.de/) | Noncommercial scientific-research license. Users obtain and accept the model terms themselves. Model geometry/weights are not bundled. |
| MediaPipe | [google-ai-edge/mediapipe](https://github.com/google-ai-edge/mediapipe) | Canonical face mesh and MediaPipe code come from Google's Apache-2.0 project. Face Landmarker model comes from Google's official model storage; retain its applicable notices/terms. Files are fetched separately and checksum-verified. |
| FFmpeg | [ffmpeg.org](https://ffmpeg.org/legal.html) | Installed externally; licensing depends on the build and enabled codecs. |

PyTorch, torchvision, NumPy, SciPy, OpenCV, PyAV, Numba, scikit-image and chumpy retain their respective upstream licenses. No runtime, external repository, checkpoint, FLAME model or private actor identity is included in this Git repository.

The UV luminance relief/gloss construction was adapted from the supplied performance-capture project's `facs.py` / `uvrelief.py` approach. The final workflow uses Sirio's approved custom CPU rendering and constrained fitting, not a generic Blender head.

The example MP4s and derived GIFs are demonstration media supplied/selected for this release. They include source performance excerpts and generated results; they are not granted under the code's MIT license, and third-party rights remain with their owners. TEIN name, logo and banner are also excluded from the MIT grant. No endorsement by the depicted performers or model authors is implied.
