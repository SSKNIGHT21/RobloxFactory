# Anime Reddit Story Factory

This is the new 1990s-anime-inspired Reddit-style storytelling pipeline. It is being developed separately from the old clip assembler so the existing project remains recoverable.

## First version

- Original Reddit-style stories (not copied Reddit posts).
- One illustrated scene image per story beat.
- Slow camera pans/zooms to give the still artwork movement.
- Text-to-speech narration, burned-in captions, optional background music.
- Vertical 9:16 MP4, with a preview and metadata uploaded as a GitHub Actions artifact.

**Important:** Version 1 animates illustrated stills with camera movement. It does not yet create full character animation or automatically generate the artwork. The image-generation step will be integrated after the first render works.

## Add scene artwork

Create one 9:16 image for each scene prompt in `story.json` and save them as:

- `anime_assets/scenes/scene_01.png`
- `anime_assets/scenes/scene_02.png`
- Continue in order for every scene.

Keep character design, hair, clothing and colours consistent between scenes. Use original artwork and avoid copying existing anime characters or frames.

## Build

1. Open **Actions** in the repository.
2. Select **Build 90s Anime Reddit Short**.
3. Choose **Run workflow**.
4. Download the `anime-reddit-short` artifact after the run succeeds.

The first successful build is a prototype. Automatic story sourcing, image generation and scheduled daily production are later milestones.
