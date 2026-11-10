# AI-generated scene clips

Place the AI-generated scene clips for one Short in this folder, in story order:

- `scene_01.gif` or `scene_01.mp4`
- `scene_02.gif` or `scene_02.mp4`
- `scene_03.gif` or `scene_03.mp4`
- and so on

Supported formats: GIF, MP4, MOV, MKV, and WebM. Use one clip per story beat. The assembly workflow normalizes each clip to vertical 9:16 and 6 seconds, joins them, burns in the matching captions from `story.json`, and optionally adds audio.

Optional audio files:
- `audio/voiceover.wav` — narration
- `audio/music.wav` — background music

The workflow does not generate source video by itself. The video clips must first be created with an AI video/image tool and added here. Do not place API keys or other secrets in this folder.
