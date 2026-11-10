#!/usr/bin/env python3
"""Assemble user-supplied AI-generated scene clips into a vertical Short."""
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIPS = ROOT / "clips"
AUDIO = ROOT / "audio"
OUTPUT = ROOT / "output"
WORK = OUTPUT / "normalized"
FPS = 24
WIDTH, HEIGHT = 720, 1280
CLIP_SECONDS = float(os.environ.get("CLIP_SECONDS", "6"))

def run(command):
    print("+", " ".join(str(x) for x in command), flush=True)
    subprocess.run([str(x) for x in command], check=True)

def timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    whole = int(secs)
    millis = int(round((secs - whole) * 1000))
    if millis == 1000:
        whole += 1
        millis = 0
    return f"{hours:02}:{minutes:02}:{whole:02},{millis:03}"

def write_captions(paths, total_duration):
    story_file = ROOT / "story.json"
    if not story_file.exists():
        return None
    story = json.loads(story_file.read_text(encoding="utf-8"))
    scenes = story.get("scenes", [])
    entries = []
    for index, _ in enumerate(paths):
        if index >= len(scenes):
            break
        caption = str(scenes[index].get("caption", "")).strip()
        if not caption:
            continue
        start = index * CLIP_SECONDS
        end = min(total_duration, (index + 1) * CLIP_SECONDS)
        entries.append((start, end, caption))
    if not entries:
        return None
    caption_path = OUTPUT / "captions.srt"
    lines = []
    for number, (start, end, caption) in enumerate(entries, 1):
        safe = caption.replace("-->", "—>")
        lines.extend([str(number), f"{timestamp(start)} --> {timestamp(end)}", safe, ""])
    caption_path.write_text("\n".join(lines), encoding="utf-8")
    return caption_path

def main():
    OUTPUT.mkdir(exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    CLIPS.mkdir(exist_ok=True)
    allowed = {".mp4", ".mov", ".mkv", ".webm", ".gif"}
    files = sorted((p for p in CLIPS.iterdir() if p.is_file() and p.suffix.lower() in allowed),
                   key=lambda p: p.name.lower())
    if not files:
        raise SystemExit("No AI-generated clips found. Add clips/scene_01.mp4, scene_02.mp4, etc. (GIF is also supported).")
    normalized = []
    for index, source in enumerate(files, 1):
        target = WORK / f"scene_{index:03}.mp4"
        run([
            "ffmpeg", "-y", "-stream_loop", "-1", "-i", source,
            "-t", str(CLIP_SECONDS),
            "-vf", f"fps={FPS},scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},setsar=1",
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-r", str(FPS), target
        ])
        normalized.append(target)
    concat_file = OUTPUT / "concat.txt"
    concat_file.write_text("".join(f"file '{p.as_posix()}'\n" for p in normalized), encoding="utf-8")
    silent = OUTPUT / "video_silent.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
         "-c", "copy", "-movflags", "+faststart", silent])
    duration = CLIP_SECONDS * len(normalized)
    caption_path = write_captions(files, duration)
    captioned = OUTPUT / "video_captioned.mp4"
    if caption_path:
        run(["ffmpeg", "-y", "-i", silent, "-vf",
             "subtitles=output/captions.srt:force_style='FontName=DejaVu Sans,FontSize=30,PrimaryColour=&H00FFFFFF,OutlineColour=&H00101010,BorderStyle=1,Outline=3,Shadow=1,Alignment=2,MarginV=110'",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
             "-an", captioned])
    else:
        captioned = silent

    voice = AUDIO / "voiceover.wav"
    music = AUDIO / "music.wav"
    final = OUTPUT / "roblox_story.mp4"
    if voice.exists() and music.exists():
        run(["ffmpeg", "-y", "-i", captioned, "-i", voice, "-stream_loop", "-1", "-i", music,
             "-filter_complex",
             f"[1:a]apad,atrim=duration={duration},volume=1.0[voice];[2:a]atrim=duration={duration},volume=0.17[music];[voice][music]amix=inputs=2:duration=longest:dropout_transition=2[a]",
             "-map", "0:v:0", "-map", "[a]", "-t", str(duration),
             "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", final])
    elif voice.exists():
        run(["ffmpeg", "-y", "-i", captioned, "-i", voice, "-map", "0:v:0", "-map", "1:a:0",
             "-af", f"apad,atrim=duration={duration}", "-t", str(duration), "-c:v", "copy",
             "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", final])
    elif music.exists():
        run(["ffmpeg", "-y", "-i", captioned, "-stream_loop", "-1", "-i", music,
             "-map", "0:v:0", "-map", "1:a:0", "-t", str(duration), "-c:v", "copy",
             "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", final])
    else:
        final.write_bytes(captioned.read_bytes())

    run(["ffmpeg", "-y", "-i", final, "-t", "8", "-vf", "scale=432:768",
         "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
         "-movflags", "+faststart", OUTPUT / "preview.mp4"])
    run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size",
         "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate",
         "-of", "json", final])
    print(f"BUILT {final} from {len(files)} AI clip(s); target length {duration:.1f}s")

if __name__ == "__main__":
    main()
