# RobloxFactory — AI Clip Shorts

This repository assembles **AI-generated scene clips** into vertical YouTube Shorts. The Blender renderer has been removed from the production workflow.

## How the new workflow works

1. Create short AI-generated clips for the story's scenes.
2. Add them to `clips/` in order, named `scene_01.mp4`, `scene_02.mp4`, and so on. Animated GIFs are also supported.
3. Add matching captions to `story.json`.
4. Optionally add `audio/voiceover.wav` and/or `audio/music.wav`.
5. GitHub Actions joins the clips, converts them to vertical 9:16, burns in captions, mixes optional audio, and uploads the final MP4 plus an 8-second preview.

Each input clip is normalized to six seconds by default. The final length is therefore six seconds multiplied by the number of scene clips, and remains below the YouTube Shorts 60-second limit when there are at most nine clips.

## Build a Short

- Add or replace files in `clips/`.
- Open **Actions → Build AI-generated Shorts → Run workflow** for a manual build.
- A new build also starts when clips, audio, the story file, or the assembly script is updated.
- Download the `robloxfactory-ai-short` artifact from the completed run. It includes the final video, preview and metadata.

## Project files

- `clips/` — input AI-generated scene clips.
- `story.json` — scene captions in the same order as the clips.
- `audio/voiceover.wav` — optional narration track.
- `audio/music.wav` — optional background music track.
- `scripts/build_ai_short.py` — FFmpeg assembly, captioning, audio mixing and preview creation.
- `.github/workflows/render-video.yml` — build and artifact-upload workflow.

## What is and is not automated

The repository now automates **editing and packaging** once AI-generated clips are added. It does not currently generate video clips by itself, automatically upload to YouTube, or produce two new AI-generated videos every day. Those require a separate video-generation service with an allowed, available API; the old free Blender render has intentionally been removed from this path.

Review the preview and final video before publishing.
