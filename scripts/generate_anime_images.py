#!/usr/bin/env python3
"""Generate missing anime scene artwork with Cloudflare Workers AI (free daily quota)."""
import base64
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = "@cf/black-forest-labs/flux-1-schnell"


def request_image(prompt, account_id, token, attempt=1):
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{MODEL}"
    body = json.dumps({"prompt": prompt[:2048], "steps": 4}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=240) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1200]
        if exc.code in (429, 500, 502, 503, 504) and attempt < 3:
            time.sleep(attempt * 12)
            return request_image(prompt, account_id, token, attempt + 1)
        raise RuntimeError(f"Cloudflare image request failed (HTTP {exc.code}): {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        if attempt < 3:
            time.sleep(attempt * 12)
            return request_image(prompt, account_id, token, attempt + 1)
        raise RuntimeError(f"Cloudflare image request failed: {exc}") from exc

    result = payload.get("result")
    if isinstance(result, dict):
        encoded = result.get("image") or result.get("data")
    elif isinstance(result, str):
        encoded = result
    else:
        encoded = payload.get("image")
    if not payload.get("success", True) or not encoded:
        raise RuntimeError("Cloudflare returned no image: " + json.dumps(payload)[:1200])
    try:
        return base64.b64decode(encoded)
    except Exception as exc:
        raise RuntimeError("Cloudflare returned an image in an unexpected format.") from exc


def main():
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not account_id or not token:
        raise SystemExit(
            "Automatic artwork needs CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN "
            "in GitHub Actions Secrets. No images were generated."
        )

    story = json.loads((ROOT / "anime" / "story.json").read_text(encoding="utf-8"))
    scenes = story.get("scenes", [])
    characters = story.get("characters", [])
    style = story.get("visual_style", "Original hand-drawn 1990s anime cel animation.")
    character_notes = "; ".join(
        f"{item.get('name', 'Character')}: {item.get('description', '')}"
        for item in characters
    )

    generated = 0
    for index, scene in enumerate(scenes, 1):
        target = ROOT / scene["image"]
        if target.is_file() and target.stat().st_size > 1000:
            print(f"Keeping existing artwork: {target.relative_to(ROOT)}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        prompt = (
            f"{style} Character designs to keep consistent: {character_notes}. "
            f"Scene: {scene.get('image_prompt', scene.get('caption', 'Cinematic story scene'))}. "
            "Carefully drawn expressive characters, coherent anatomy, detailed painted background, "
            "cinematic framing, no words, no subtitles, no logos, no watermark."
        )
        print(f"Generating scene {index}/{len(scenes)}: {scene.get('caption', '')}", flush=True)
        image_bytes = request_image(prompt, account_id, token)
        if not image_bytes.startswith(b"\x89PNG") and not image_bytes.startswith(b"\xff\xd8"):
            raise RuntimeError(f"Scene {index} did not return a valid PNG/JPEG image.")
        target.write_bytes(image_bytes)
        generated += 1
        print(f"Saved {target.relative_to(ROOT)} ({len(image_bytes)} bytes)", flush=True)

    print(f"Artwork ready. Newly generated: {generated}; total scenes: {len(scenes)}")


if __name__ == "__main__":
    main()
