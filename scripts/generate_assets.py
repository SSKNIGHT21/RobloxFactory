#!/usr/bin/env python3
"""Generate an original short story, narration, and a small original music/SFX bed."""
import base64, json, math, os, struct, time, urllib.error, urllib.request, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"
AUDIO.mkdir(exist_ok=True)
API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
TEXT_MODEL = os.environ.get("GEMINI_TEXT_MODEL", "gemini-3.8-flash")
TTS_MODEL = os.environ.get("GEMINI_TTS_MODEL", "gemini-3.1-flash-tts-preview")
DURATION, SAMPLE_RATE = 45, 24000

def api_post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": API_KEY}, method="POST")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            if exc.code < 500 or attempt == 2:
                raise RuntimeError(f"Gemini API error {exc.code}: {detail[:1200]}") from exc
            time.sleep(3 * (attempt + 1))
        except (TimeoutError, urllib.error.URLError):
            if attempt == 2:
                raise
            time.sleep(3 * (attempt + 1))
    raise RuntimeError("Gemini request failed after retries")

def generate_story():
    theme = os.environ.get("STORY_THEME", "").strip()
    seed = os.environ.get("GITHUB_RUN_ID", str(int(time.time())))
    prompt = f"""
Create one original, family-friendly, funny and surprising Roblox-inspired vertical YouTube Short story.
Run seed: {seed}. Theme hint: {theme or "invent a fresh everyday mystery or comedy"}.
Visually simple to animate: one main kid character named Toby, one cute orange cat, and 1-2 simple props.
No real people, brands, copyrighted characters, violence, injuries, or dangerous stunts.
Make the first two seconds a strong visual hook. Use setup, escalation, twist, and satisfying ending.
Return ONLY valid JSON with fields:
{{
 "title":"short title",
 "duration_seconds":45,
 "narration":"85-115 spoken words, energetic natural English narration, no stage directions",
 "characters":["Toby","Cat"],
 "scenes":[
   {{"caption":"short on-screen caption, max 7 words","beat":"short beat label","action":"walk|point|surprise|jump|panic|fix|celebrate|look|idle","camera":"wide|toby|toaster|cat|action"}}
 ]
}}
Return exactly 7 scenes. Captions must be brief and readable, ideally 3-6 words.
"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{TEXT_MODEL}:generateContent"
    result = api_post(url, {"contents":[{"parts":[{"text":prompt}]}],
        "generationConfig":{"responseMimeType":"application/json","maxOutputTokens":4096,
                            "thinkingConfig":{"thinkingLevel":"low"}}})
    parts = result.get("candidates",[{}])[0].get("content",{}).get("parts",[])
    raw = next((p.get("text","").strip() for p in parts if p.get("text")), "")
    if not raw:
        raise RuntimeError("Gemini returned no story text")
    if raw.startswith(chr(96)*3):
        raw = raw.split("\n",1)[1].rsplit(chr(96)*3,1)[0]
    story = json.loads(raw)
    scenes = story.get("scenes")
    if not isinstance(scenes,list) or len(scenes)<6:
        raise ValueError("Gemini must return at least six scenes")
    scenes = scenes[:7]
    while len(scenes)<7:
        scenes.append(dict(scenes[-1]))
    actions={"idle","walk","point","surprise","jump","panic","fix","celebrate","look"}
    cameras={"wide","toby","toaster","cat","action"}
    for i,item in enumerate(scenes):
        if not isinstance(item,dict):
            raise ValueError("Every scene must be an object")
        item["caption"]=str(item.get("caption",f"Scene {i+1}"))[:58]
        item["beat"]=str(item.get("beat","story"))
        if item.get("action") not in actions:
            item["action"]=["walk","surprise","point","jump","panic","fix","celebrate"][i]
        if item.get("camera") not in cameras:
            item["camera"]=["wide","toaster","toby","cat","action","toby","wide"][i]
    narration=str(story.get("narration","")).strip()
    if not 65 <= len(narration.split()) <= 145:
        raise ValueError("Narration must contain 65-145 words")
    story.update({"duration_seconds":DURATION,"scenes":scenes,"narration":narration,
                  "characters":story.get("characters") or ["Toby","Cat"],"generated_by":TEXT_MODEL})
    (ROOT/"story.json").write_text(json.dumps(story,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return story

def generate_voiceover(story):
    prompt="Read this as a lively, clear, upbeat storyteller for a short animated comedy. Do not add words. Narration:\n"+story["narration"]
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{TTS_MODEL}:generateContent"
    result=api_post(url,{"contents":[{"parts":[{"text":prompt}]}],
        "generationConfig":{"responseModalities":["AUDIO"],
          "speechConfig":{"voiceConfig":{"prebuiltVoiceConfig":{"voiceName":"Puck"}},"languageCode":"en-US"}}})
    parts=result.get("candidates",[{}])[0].get("content",{}).get("parts",[])
    encoded=next((p.get("inlineData",{}).get("data") or p.get("inline_data",{}).get("data")
                  for p in parts if p.get("inlineData") or p.get("inline_data")),None)
    if not encoded:
        raise RuntimeError("Gemini TTS returned no audio data")
    pcm=base64.b64decode(encoded)
    out=AUDIO/"voiceover.wav"
    if pcm[:4]==b"RIFF":
        out.write_bytes(pcm)
    else:
        with wave.open(str(out),"wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SAMPLE_RATE); wf.writeframes(pcm)
    if out.stat().st_size<10000:
        raise RuntimeError("Generated voiceover is unexpectedly small")
    return out

def make_original_music(duration=DURATION):
    """Create a quiet, original synth bed with gentle transition dings; no sampled music."""
    count=duration*SAMPLE_RATE
    notes=[261.63,329.63,392.00,349.23,293.66,392.00,440.00,349.23]
    scene_length=duration/7
    out=AUDIO/"background.wav"
    with wave.open(str(out),"wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SAMPLE_RATE)
        chunk=bytearray()
        for n in range(count):
            t=n/SAMPLE_RATE
            freq=notes[int(t/1.5)%len(notes)]
            nt=t%1.5
            env=min(1.0,nt/0.08)*max(0.0,min(1.0,(1.5-nt)/0.25))
            value=(0.045*math.sin(2*math.pi*freq*t)+0.022*math.sin(2*math.pi*(freq/2)*t)+
                   0.012*math.sin(2*math.pi*(freq*1.5)*t))*env
            for boundary in range(1,7):
                dt=t-boundary*scene_length
                if 0<=dt<0.32:
                    decay=math.exp(-12*dt)
                    value+=0.10*decay*(math.sin(2*math.pi*880*dt)+0.45*math.sin(2*math.pi*1320*dt))
            fade=min(1.0,t/1.2,max(0.0,(duration-t)/1.4))
            sample=max(-0.95,min(0.95,value*fade))
            chunk.extend(struct.pack("<h",int(sample*32767)))
            if len(chunk)>=48000:
                wf.writeframes(chunk); chunk.clear()
        if chunk: wf.writeframes(chunk)
    return out

def main():
    if not API_KEY:
        raise SystemExit("GEMINI_API_KEY is missing. Add it as a GitHub Actions repository secret.")
    story=generate_story()
    voice=generate_voiceover(story)
    music=make_original_music()
    print(f"Generated story: {story['title']}")
    print(f"Narration words: {len(story['narration'].split())}")
    print(f"Voiceover: {voice} ({voice.stat().st_size} bytes)")
    print(f"Original score: {music} ({music.stat().st_size} bytes)")

if __name__=="__main__":
    main()
