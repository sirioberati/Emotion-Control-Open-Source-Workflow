# Example gallery

| File | Description |
| --- | --- |
| videos/courtroom-performance.mp4 | Full supplied `1008(14).mp4`, unchanged: original, mask and generated performance |
| videos/courtroom-preview.mp4 | Full supplied `asdfasdUntitled.mp4`, unchanged; used for the main courtroom GIF |
| videos/emotional-performance.mp4 | Full supplied `1008(15).mp4`, unchanged: original and generated performance |
| masks/expressive-mask.mp4 | Approved full mask from the earlier smiling-man performance |
| masks/emotional-mask.mp4 | Approved emotional-reaction mask from the original extraction |
| previews/courtroom.gif | Full new courtroom clip, looping silently from its beginning |
| Other previews/*.gif | Silent, looping six-second excerpts beginning at 2 seconds |

The mask files preserve the full extracted source performances. The comparison videos are edited demonstrations and can differ in duration/timing from the complete masks. Do not feed comparison layouts into the one-face extraction pipeline.

Regenerate previews with `python tools/build_previews.py` (requires FFmpeg). GIFs use 10 fps; the full MP4s retain their original frame rates and audio. No audio is present in GIF format.

Example media are excluded from the MIT code license. See ../THIRD_PARTY_NOTICES.md. Technical metadata and SHA-256 hashes are recorded in manifest.json.
