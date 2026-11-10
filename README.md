# RobloxFactory Shorts

A GitHub Actions pipeline for creating vertical, Roblox-inspired story Shorts.

## What it does

- Uses Gemini to generate an original seven-beat story and spoken narration when `GEMINI_API_KEY` is configured.
- Uses Blender to build a block-style kitchen, Toby and Miso characters, animated acting, story props, camera cuts and on-screen captions.
- Generates an original, simple background music bed and scene-transition chimes.
- Uses FFmpeg to combine the animation and audio into a 45-second, 540 × 960, 12 fps MP4.
- Validates video duration, dimensions, frame rate and the presence of an audio track.
- Uploads the full Short plus an 8-second preview and preview image as a GitHub Actions artifact.

## One-time setup for Gemini

1. Open **Settings → Secrets and variables → Actions** in this repository.
2. Choose **New repository secret**.
3. Name it exactly `GEMINI_API_KEY` and add your Gemini API key as the secret value.
4. Never paste the key into chat, source code, or a public issue.

Without this secret, manual test renders use the checked-in sample story and generated background music. Scheduled story generation requires the secret and stops with a clear error if it is missing.

## Run and schedule

- Open **Actions → Render RobloxFactory Shorts → Run workflow** to start one Short. An optional theme can be supplied.
- The scheduled workflow is set for **10:00 AM and 6:00 PM India time** (04:30 and 12:30 UTC).
- After a successful run, open its **Artifacts** section and download `roblox-short-<run number>`.
- The ZIP includes `roblox_story.mp4`, `preview.mp4`, `preview.jpg`, `story.json`, and `metadata.json`.

## Files

- `story.json` — current sample story and scene directions.
- `scripts/generate_assets.py` — Gemini story and voiceover generation plus original audio bed.
- `blender/render_story.py` — character/set construction and animation.
- `.github/workflows/render-video.yml` — scheduled build, validation and artifact upload.

## Current limits

This project produces review-ready video artifacts; it does **not** upload to YouTube automatically. A human should review the preview and full Short before publishing. The visuals are a procedural Roblox-inspired Blender animation, not a recreation of another channel's exact assets or style. Scheduled Gemini generation is not fully ready until the repository secret above has been added and a scheduled run succeeds.
