# Example gallery

| File | Description |
| --- | --- |
| videos/courtroom-performance.mp4 | Full supplied `1008(14).mp4`, unchanged: original, mask and generated performance |
| videos/courtroom-preview.mp4 | Full supplied `asdfasdUntitled.mp4`, unchanged; used for the main courtroom GIF |
| videos/emotional-performance.mp4 | Full supplied `1008(15).mp4`, unchanged: original and generated performance |
| videos/expressive-original.mp4 | Matching original `1008(5).mp4`, confirmed by the approved mask run manifest |
| videos/expressive-sirio.mp4 | Supplied `seedance-2-5-6ac803f66ca719d85df91f7d.mp4`, unchanged generated Sirio result |
| masks/expressive-mask.mp4 | Approved full mask from the earlier smiling-man performance |
| masks/emotional-mask.mp4 | Approved emotional-reaction mask from the original extraction |
| previews/courtroom.gif | Full new courtroom clip, looping silently from its beginning |
| previews/emotional-mask.gif | Ten-second excerpt from 6–16 seconds, showing the transition from a smile into crying |
| Other previews/*.gif | Silent, looping six-second excerpts beginning at 2 seconds |

The mask files preserve the full extracted source performances. The comparison videos are edited demonstrations and can differ in duration/timing from the complete masks. Do not feed comparison layouts into the one-face extraction pipeline.

Regenerate previews with `python tools/build_previews.py` (requires FFmpeg). GIFs use 10 fps; the full MP4s retain their original frame rates and audio. No audio is present in GIF format.

Example media are excluded from the MIT code license. See ../THIRD_PARTY_NOTICES.md. Technical metadata and SHA-256 hashes are recorded in manifest.json.

The expressive original and mask run for approximately 21.47 seconds at 30 fps. The supplied generated Sirio file is approximately 22.08 seconds at 24 fps. These are separate, unchanged files; their previews are not presented as a frame-perfect synchronized composite.
