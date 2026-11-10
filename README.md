# RobloxFactory

A starter pipeline for turning a short, scene-based story into a vertical Roblox-inspired 3D video.

## Project files

- `story.json` — story title, duration, and scene captions.
- `blender/render_story.py` — builds a simple block-style kitchen scene and renders a 720 × 1280 MP4.
- `.github/workflows/render-video.yml` — GitHub Actions workflow that renders the video and uploads it as an artifact.

## Run a render

1. Install Blender and FFmpeg on a computer.
2. From the repository root, run:

   ```bash
   blender -b --python blender/render_story.py
   ```

3. The video is written to `output/roblox_story.mp4`.

You can also open the **Actions** tab on GitHub and run **Render RobloxFactory story**. The workflow runs automatically when the story or renderer files change. Download the `roblox-story-video` artifact from a completed run.

## Voiceover

If a voice track is available, place it at `audio/audio.wav` before rendering. The workflow will mix it into the MP4. If that file is absent, the render will be silent.

## Current scope

This is the first working render scaffold, not yet a complete daily video factory. It creates a basic block-built scene with captions and a camera move. Automated story generation, fetching the real voice file from Make, richer scene-by-scene animation, and scheduled two-videos-per-day production still need to be connected.
