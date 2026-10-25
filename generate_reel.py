import asyncio
import json
import os
import subprocess
import textwrap
from pathlib import Path
import edge_tts
import requests
from PIL import Image, ImageDraw, ImageFont

QUEUE_FILE = Path("content_queue.json")
BG_VIDEO = Path("assets/bg_loop.mp4")
BG_MUSIC = Path("assets/bg_music.mp3")
OUTPUT_DIR = Path("output")
TEMP_DIR = OUTPUT_DIR / "temp"
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

TG_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
STORE_URL = os.getenv("STORE_URL", "https://github.com/SagarIndure")
STORE_BTN_TEXT = os.getenv("STORE_BTN_TEXT", "⚡ Download Full Automation Kit")

def get_font(size: int):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

async def synth_line(text: str, voice: str, out_mp3: Path):
    rate = "+12%" if "Prabhat" in voice else "+8%"
    comm = edge_tts.Communicate(text, voice, rate=rate)
    await comm.save(str(out_mp3))

def get_duration(media_path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
        str(media_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())

def draw_office_scene(setting: str, speaker_name: str, avatar_color: tuple, dialogue: str, out_png: Path):
    W, H = 1080, 1920
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    f_tag = get_font(34)
    f_name = get_font(48)
    f_dialogue = get_font(50)

    # Top glow indicator
    draw.rectangle([(0, 0), (W, 18)], fill=(0, 229, 255, 255))

    # Setting Badge
    draw.rounded_rectangle([(W/2 - 360, 80), (W/2 + 360, 160)], radius=30, fill=(10, 15, 30, 245), outline=(56, 189, 248, 240), width=4)
    draw.text((W/2, 120), f"⚡ {setting}", font=f_tag, fill=(0, 229, 255, 255), anchor="mm")

    # Speaker Card with Neon Glow
    draw.rounded_rectangle([(70, 260), (W - 70, 1040)], radius=48, fill=(15, 23, 42, 250), outline=avatar_color, width=6)
    draw.ellipse([(W/2 - 120, 360), (W/2 + 120, 600)], fill=avatar_color)
    draw.text((W/2, 480), "🧑‍💻" if "ROHIT" in speaker_name else "👩‍💻", font=get_font(96), anchor="mm")
    draw.text((W/2, 680), speaker_name, font=f_name, fill=(255, 255, 255, 255), anchor="mm")
    draw.text((W/2, 760), "World Test Organisation • Live Incident Trace", font=f_tag, fill=(148, 163, 184, 255), anchor="mm")

    # Dialogue Card (Glassmorphism with strong contrast)
    draw.rounded_rectangle([(60, 1140), (W - 60, 1820)], radius=40, fill=(20, 30, 50, 250), outline=(255, 255, 255, 150), width=3)
    wrapped = textwrap.wrap(dialogue, width=25)
    sy = 1240
    for line in wrapped:
        draw.text((W/2, sy), line, font=f_dialogue, fill=(255, 255, 255, 255), anchor="mm", align="center")
        sy += 74

    img.save(out_png, "PNG")

def draw_postman_scene(scene_data: dict, out_png: Path):
    W, H = 1080, 1920
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    f_title = get_font(36)
    f_code = get_font(34)
    f_ui = get_font(30)

    draw.rectangle([(0, 0), (W, 18)], fill=(255, 115, 0, 255))

    draw.rounded_rectangle([(40, 70), (W - 40, 1850)], radius=30, fill=(18, 18, 18, 255), outline=(255, 115, 0, 240), width=4)
    draw.rounded_rectangle([(40, 70), (W - 40, 160)], radius=30, fill=(35, 35, 35, 255))
    draw.text((80, 115), "📭 Postman API Studio - Live Debugger", font=f_title, fill=(255, 115, 0, 255))

    draw.rounded_rectangle([(70, 200), (W - 70, 310)], radius=14, fill=(45, 45, 45, 255))
    draw.text((100, 255), "POST", font=f_ui, fill=(0, 255, 128, 255))
    draw.text((220, 255), scene_data["endpoint"], font=f_code, fill=(255, 255, 255, 255))
    draw.rounded_rectangle([(W - 220, 218), (W - 90, 292)], radius=12, fill=(255, 115, 0, 255))
    draw.text((W - 155, 255), "Send", font=f_ui, fill=(255, 255, 255, 255), anchor="mm")

    draw.rounded_rectangle([(70, 360), (W - 70, 880)], radius=14, fill=(12, 12, 12, 255), outline=(70, 70, 70, 255), width=2)
    draw.text((100, 400), "Request Payload (JSON)", font=f_ui, fill=(150, 150, 150, 255))
    payload_lines = scene_data["payload"].split("\n")
    py = 470
    for line in payload_lines:
        draw.text((100, py), line, font=f_code, fill=(156, 220, 254, 255))
        py += 48

    draw.rounded_rectangle([(70, 950), (W - 70, 1780)], radius=14, fill=(12, 12, 12, 255), outline=(0, 255, 128, 240), width=3)
    draw.text((100, 990), "Response Inspector", font=f_ui, fill=(150, 150, 150, 255))
    draw.text((W - 220, 990), scene_data["status"], font=f_code, fill=(0, 255, 128, 255), anchor="mm")

    res_text = "{\n  \"status\": \"FAILURE_RISK\",\n  \"error\": \"Idempotency Key Missing\",\n  \"retry_storm\": true\n}"
    res_lines = res_text.split("\n")
    ry = 1080
    for line in res_lines:
        draw.text((100, ry), line, font=f_code, fill=(206, 145, 120, 255))
        ry += 48

    img.save(out_png, "PNG")

def draw_architecture_scene(flow_steps: list, out_png: Path):
    W, H = 1080, 1920
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    f_title = get_font(40)
    f_step = get_font(36)

    draw.rectangle([(0, 0), (W, 18)], fill=(255, 69, 58, 255))

    draw.rounded_rectangle([(60, 100), (W - 60, 240)], radius=30, fill=(15, 23, 42, 250), outline=(255, 69, 58, 240), width=4)
    draw.text((W/2, 170), "⚡ ARCHITECTURE VULNERABILITY FLOW", font=f_title, fill=(255, 69, 58, 255), anchor="mm")

    y_pos = 320
    for i, step in enumerate(flow_steps):
        box_col = (239, 68, 68, 240) if "❌" in step else (30, 41, 59, 250)
        draw.rounded_rectangle([(70, y_pos), (W - 70, y_pos + 270)], radius=36, fill=box_col, outline=(255, 255, 255, 220), width=4)
        draw.text((W/2, y_pos + 135), step, font=f_step, fill=(255, 255, 255, 255), anchor="mm", align="center")
        y_pos += 330

    img.save(out_png, "PNG")

def draw_takeaway_scene(takeaway_text: str, out_png: Path):
    W, H = 1080, 1920
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    f_takeaway = get_font(46)

    draw.rectangle([(0, 0), (W, 18)], fill=(0, 255, 163, 255))

    draw.rounded_rectangle([(60, 350), (W - 60, 1520)], radius=44, fill=(15, 23, 42, 250), outline=(0, 255, 163, 255), width=6)
    wrapped = textwrap.wrap(takeaway_text, width=23)
    sy = 600
    for line in wrapped:
        color = (0, 255, 163, 255) if "💡" in line else (255, 255, 255, 255)
        draw.text((W/2, sy), line, font=f_takeaway, fill=color, anchor="mm", align="center")
        sy += 85

    img.save(out_png, "PNG")

def send_to_telegram(video_path: Path, item: dict):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("Telegram credentials not set. Skipping Telegram upload.")
        return

    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendVideo"
    caption = f"🔥 *{item['title']}*\n\n{item['takeaway']}\n\n_{item['author']}_"
    reply_markup = {
        "inline_keyboard": [[
            {"text": STORE_BTN_TEXT, "url": STORE_URL}
        ]]
    }

    with open(video_path, "rb") as video_file:
        resp = requests.post(
            url,
            data={
                "chat_id": TG_CHAT_ID,
                "caption": caption,
                "parse_mode": "Markdown",
                "reply_markup": json.dumps(reply_markup)
            },
            files={"video": video_file},
            timeout=120
        )
    resp.raise_for_status()
    print(f"Successfully posted {video_path.name} to Telegram!")

async def build_full_reel(item: dict, final_mp4: Path):
    segment_videos = []

    s1 = item["scene_1"]
    s1_audio = TEMP_DIR / "s1_audio.mp3"
    await synth_line(s1["dialogue"], s1["voice"], s1_audio)
    s1_dur = get_duration(s1_audio) + 0.4
    s1_png = TEMP_DIR / "s1.png"
    draw_office_scene(s1["setting"], "ROHIT (Backend Dev)", (255, 69, 58, 255), s1["dialogue"], s1_png)

    s1_seg = TEMP_DIR / "seg_1.mp4"
    # Added FFmpeg zoompan and dynamic filter for cinematic motion instead of static slideshow
    subprocess.run([
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(BG_VIDEO),
        "-loop", "1", "-i", str(s1_png), "-i", str(s1_audio),
        "-filter_complex", "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=brightness=-0.38:contrast=1.35[bg];[1:v]scale=1080:1920[fg_scaled];[bg][fg_scaled]overlay=0:0:shortest=1[v]",
        "-map", "[v]", "-map", "2:a", "-r", "30", "-fps_mode", "cfr",
        "-c:v", "libx264", "-preset", "fast", "-crf", "24", "-c:a", "aac", "-b:a", "192k",
        "-t", str(s1_dur), "-pix_fmt", "yuv420p", str(s1_seg)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    segment_videos.append(s1_seg)

    s2 = item["scene_2"]
    s2_audio = TEMP_DIR / "s2_audio.mp3"
    await synth_line(f"Inspecting the Postman payload for {s2['endpoint']}.", "en-IN-PrabhatNeural", s2_audio)
    s2_dur = 4.0
    s2_png = TEMP_DIR / "s2.png"
    draw_postman_scene(s2, s2_png)

    s2_seg = TEMP_DIR / "seg_2.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(BG_VIDEO),
        "-loop", "1", "-i", str(s2_png), "-i", str(s2_audio),
        "-filter_complex", "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=brightness=-0.38:contrast=1.35[bg];[1:v]scale=1080:1920[fg_scaled];[bg][fg_scaled]overlay=0:0:shortest=1[v]",
        "-map", "[v]", "-map", "2:a", "-r", "30", "-fps_mode", "cfr",
        "-c:v", "libx264", "-preset", "fast", "-crf", "24", "-c:a", "aac", "-b:a", "192k",
        "-t", str(s2_dur), "-pix_fmt", "yuv420p", str(s2_seg)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    segment_videos.append(s2_seg)

    s3 = item["scene_3"]
    s3_audio = TEMP_DIR / "s3_audio.mp3"
    await synth_line(s3["dialogue"], s3["voice"], s3_audio)
    s3_dur = get_duration(s3_audio) + 0.4
    s3_png = TEMP_DIR / "s3.png"
    draw_office_scene(s3["setting"], "PRIYA (Lead QA)", (0, 229, 255, 255), s3["dialogue"], s3_png)

    s3_seg = TEMP_DIR / "seg_3.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(BG_VIDEO),
        "-loop", "1", "-i", str(s3_png), "-i", str(s3_audio),
        "-filter_complex", "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=brightness=-0.38:contrast=1.35[bg];[1:v]scale=1080:1920[fg_scaled];[bg][fg_scaled]overlay=0:0:shortest=1[v]",
        "-map", "[v]", "-map", "2:a", "-r", "30", "-fps_mode", "cfr",
        "-c:v", "libx264", "-preset", "fast", "-crf", "24", "-c:a", "aac", "-b:a", "192k",
        "-t", str(s3_dur), "-pix_fmt", "yuv420p", str(s3_seg)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    segment_videos.append(s3_seg)

    s4 = item["scene_4"]
    s4_audio = TEMP_DIR / "s4_audio.mp3"
    await synth_line("Tracing the exact architecture vulnerability step by step.", "en-IN-NeerjaNeural", s4_audio)
    s4_dur = 4.5
    s4_png = TEMP_DIR / "s4.png"
    draw_architecture_scene(s4["flow"], s4_png)

    s4_seg = TEMP_DIR / "seg_4.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(BG_VIDEO),
        "-loop", "1", "-i", str(s4_png), "-i", str(s4_audio),
        "-filter_complex", "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=brightness=-0.38:contrast=1.35[bg];[1:v]scale=1080:1920[fg_scaled];[bg][fg_scaled]overlay=0:0:shortest=1[v]",
        "-map", "[v]", "-map", "2:a", "-r", "30", "-fps_mode", "cfr",
        "-c:v", "libx264", "-preset", "fast", "-crf", "24", "-c:a", "aac", "-b:a", "192k",
        "-t", str(s4_dur), "-pix_fmt", "yuv420p", str(s4_seg)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    segment_videos.append(s4_seg)

    t_audio = TEMP_DIR / "t_audio.mp3"
    await synth_line(item["takeaway"], "en-IN-NeerjaNeural", t_audio)
    t_dur = get_duration(t_audio) + 0.5
    t_png = TEMP_DIR / "takeaway.png"
    draw_takeaway_scene(item["takeaway"], t_png)

    t_seg = TEMP_DIR / "seg_takeaway.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(BG_VIDEO),
        "-loop", "1", "-i", str(t_png), "-i", str(t_audio),
        "-filter_complex", "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=brightness=-0.38:contrast=1.35[bg];[1:v]scale=1080:1920[fg_scaled];[bg][fg_scaled]overlay=0:0:shortest=1[v]",
        "-map", "[v]", "-map", "2:a", "-r", "30", "-fps_mode", "cfr",
        "-c:v", "libx264", "-preset", "fast", "-crf", "24", "-c:a", "aac", "-b:a", "192k",
        "-t", str(t_dur), "-pix_fmt", "yuv420p", str(t_seg)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    segment_videos.append(t_seg)

    concat_list = TEMP_DIR / "all_segments.txt"
    concat_list.write_text("\n".join(f"file '{p.resolve()}'" for p in segment_videos), encoding="utf-8")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-stream_loop", "-1", "-i", str(BG_MUSIC),
        "-filter_complex", "[0:a]volume=1.3[va];[1:a]volume=0.15[ma];[va][ma]amix=inputs=2:duration=first[outa]",
        "-map", "0:v", "-map", "[outa]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        str(final_mp4)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

async def main():
    queue = json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
    target = next((x for x in queue if not x.get("done")), None)
    if not target:
        print("All items completed!")
        return

    out_mp4 = OUTPUT_DIR / f"{target['id']}.mp4"
    print(f"Building Cinematic Reel ({target['id']})...")
    await build_full_reel(target, out_mp4)

    print(f"Publishing to Telegram...")
    send_to_telegram(out_mp4, target)

    target["done"] = True
    QUEUE_FILE.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n🔥 Done! Reel rendered and posted to Telegram!")

if __name__ == "__main__":
    asyncio.run(main())
