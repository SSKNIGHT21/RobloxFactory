#!/usr/bin/env python3
"""Render an illustrated 1990s-anime-style Reddit story Short."""
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "anime"
FPS = 24
WIDTH, HEIGHT = 720, 1280

def run(args):
    print("+", " ".join(map(str, args)), flush=True)
    subprocess.run([str(x) for x in args], check=True)

def srt_time(seconds):
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def main():
    story_path = ROOT / "anime" / "story.json"
    story = json.loads(story_path.read_text(encoding="utf-8"))
    scenes = story.get("scenes", [])
    narration = str(story.get("narration", "")).strip()
    if not narration or not scenes:
        raise SystemExit("anime/story.json needs narration and at least one scene.")

    missing = [str(ROOT / s["image"]) for s in scenes if not (ROOT / s["image"]).is_file()]
    if missing:
        raise SystemExit("Scene artwork is missing. Add these image files first:\n" + "\n".join(missing))

    OUTPUT.mkdir(parents=True, exist_ok=True)
    duration = float(story.get("duration_seconds", 48))
    scene_duration = duration / len(scenes)
    concat_file = OUTPUT / "concat.txt"
    scene_files = []

    for i, scene in enumerate(scenes, 1):
        image = ROOT / scene["image"]
        clip = OUTPUT / f"scene_{i:02}.mp4"
        frames = max(1, round(scene_duration * FPS))
        # Slow zoom and slight horizontal drift create restrained motion without
        # pretending that a still image is full character animation.
        vf = (
            f"scale=960:1706:force_original_aspect_ratio=increase,"
            f"crop=960:1706,"
            f"zoompan=z='min(zoom+0.00035,1.06)':"
            f"x='iw/2-(iw/zoom/2)+8*sin(on/90)':"
            f"y='ih/2-(ih/zoom/2)':d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS},"
            f"setsar=1,format=yuv420p"
        )
        run(["ffmpeg", "-y", "-loop", "1", "-i", image, "-vf", vf,
             "-frames:v", str(frames), "-an", "-c:v", "libx264",
             "-preset", "veryfast", "-crf", "20", clip])
        scene_files.append(clip)

    concat_file.write_text("".join(f"file '{p.as_posix()}'\n" for p in scene_files), encoding="utf-8")
    silent = OUTPUT / "silent.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
         "-c", "copy", "-movflags", "+faststart", silent])

    srt = OUTPUT / "captions.srt"
    entries = []
    for i, scene in enumerate(scenes):
        caption = str(scene.get("caption", "")).strip()
        if caption:
            entries.extend([str(len(entries)//4 + 1),
                            f"{srt_time(i * scene_duration)} --> {srt_time((i+1) * scene_duration)}",
                            caption.replace("-->", "—>"), ""])
    srt.write_text("\n".join(entries), encoding="utf-8")

    voice = OUTPUT / "voice.mp3"
    voice_name = os.environ.get("TTS_VOICE", story.get("voice", "en-US-JennyNeural"))
    run(["edge-tts", "--voice", voice_name, "--text", narration, "--write-media", voice])

    captioned = OUTPUT / "captioned.mp4"
    run(["ffmpeg", "-y", "-i", silent, "-vf",
         "subtitles=output/anime/captions.srt:force_style='FontName=DejaVu Sans,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00101010,BorderStyle=1,Outline=2,Shadow=1,Alignment=2,MarginV=100'",
         "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-pix_fmt", "yuv420p", captioned])

    final = OUTPUT / "anime_reddit_story.mp4"
    music = ROOT / "audio" / "music.mp3"
    if music.is_file():
        run(["ffmpeg", "-y", "-i", captioned, "-i", voice, "-stream_loop", "-1", "-i", music,
             "-filter_complex", f"[1:a]apad,atrim=duration={duration}[v];[2:a]atrim=duration={duration},volume=0.12[m];[v][m]amix=inputs=2:duration=first[a]",
             "-map", "0:v:0", "-map", "[a]", "-t", str(duration),
             "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", final])
    else:
        run(["ffmpeg", "-y", "-i", captioned, "-i", voice, "-map", "0:v:0", "-map", "1:a:0",
             "-af", f"apad,atrim=duration={duration}", "-t", str(duration),
             "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", final])

    preview = OUTPUT / "preview.mp4"
    run(["ffmpeg", "-y", "-i", final, "-t", "8", "-vf", "scale=432:768",
         "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", preview])
    metadata = OUTPUT / "metadata.json"
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "format=duration,size:stream=codec_type,codec_name,width,height",
                            "-of", "json", final], check=True, capture_output=True, text=True)
    data = json.loads(probe.stdout)
    metadata.write_text(json.dumps(data, indent=2), encoding="utf-8")
    actual = float(data["format"]["duration"])
    video = next(s for s in data["streams"] if s["codec_type"] == "video")
    if not (5 < actual < 60 and video["width"] == WIDTH and video["height"] == HEIGHT):
        raise SystemExit(f"Output validation failed: duration={actual}, video={video}")
    print(f"VALID: {actual:.2f}s, {WIDTH}x{HEIGHT}")
    print(f"BUILT: {final}")

if __name__ == "__main__":
    main()
