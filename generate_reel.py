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
    rate = "+8%" if "Prabhat" in voice else "+4%"
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

    f_tag = get_font(30)
    f_name = get_font(42)
    f_dialogue = get_font(46)

    draw.rectangle([(0, 0), (W, 14)], fill=(255, 255, 255, 40))
    draw.rectangle([(0, 0), (W, 14)], fill=(0, 229, 255, 255))

    draw.rounded_rectangle([(W/2 - 300, 60), (W/2 + 300, 130)], radius=24, fill=(15, 23, 42, 230), outline=(56, 189, 248, 200), width=2)
    draw.text((W/2, 95), f"🏢 {setting}", font=f_tag, fill=(0, 229, 255, 255), anchor="mm")

    draw.rounded_rectangle([(80, 240), (W - 80, 1100)], radius=40, fill=(15, 23, 42, 240), outline=avatar_color, width=4)
    draw.ellipse([(W/2 - 120, 340), (W/2 + 120, 580)], fill=avatar_color)
    draw.text((W/2, 460), "🧑‍💻" if "ROHIT" in speaker_name else "👩‍💻", font=get_font(90), anchor="mm")
    draw.text((W/2, 660), speaker_name, font=f_name, fill=(255, 255, 255, 255), anchor="mm")
    draw.text((W/2, 740), "Office Desk • Live Discussion", font=f_tag, fill=(148, 163, 184, 255), anchor="mm")

    draw.rounded_rectangle([(70, 1200), (W - 70, 1750)], radius=32, fill=(30, 41, 59, 245), outline=(255, 255, 255, 100), width=2)
    wrapped = textwrap.wrap(dialogue, width=28)
    sy = 1290
    for line in wrapped:
        draw.text((W/2, sy), line, font=f_dialogue, fill=(255, 255, 255, 255), anchor="mm", align="center")
        sy += 64

    img.save(out_png, "PNG")

def draw_postman_scene(scene_data: dict, out_png: Path):
    W, H = 1080, 1920
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    f_title = get_font(30)
    f_code = get_font(32)
    f_ui = get_font(28)

    draw.rectangle([(0, 0), (W, 14)], fill=(255, 255, 255, 40))
    draw.rectangle([(0, 0), (W, 14)], fill=(255, 115, 0, 255))

    draw.rounded_rectangle([(40, 80), (W - 40, 1840)], radius=24, fill=(30, 30, 30, 250), outline=(255, 115, 0, 200), width=3)
    draw.rounded_rectangle([(40, 80), (W - 40, 160)], radius=24, fill=(45, 45, 45, 255))
    draw.text((80, 120), "📭 Postman - UPI Payment Collection API", font=f_title, fill=(255, 115, 0, 255))

    draw.rounded_rectangle([(70, 200), (W - 70, 300)], radius=12, fill=(50, 50, 50, 255))
    draw.text((100, 250), "POST", font=f_ui, fill=(0, 255, 128, 255))
    draw.text((220, 250), scene_data["endpoint"], font=f_code, fill=(255, 255, 255, 255))
    draw.rounded_rectangle([(W - 220, 215), (W - 90, 285)], radius=10, fill=(255, 115, 0, 255))
    draw.text((W - 155, 250), "Send", font=f_ui, fill=(255, 255, 255, 255), anchor="mm")

    draw.rounded_rectangle([(70, 350), (W - 70, 850)], radius=12, fill=(20, 20, 20, 255), outline=(70, 70, 70, 255), width=2)
    draw.text((100, 380), "Body (JSON)", font=f_ui, fill=(150, 150, 150, 255))
    payload_lines = scene_data["payload"].split("\n")
    py = 440
    for line in payload_lines:
        draw.text((100, py), line, font=f_code, fill=(156, 220, 254, 255))
        py += 45

    draw.rounded_rectangle([(70, 920), (W - 70, 1750)], radius=12, fill=(20, 20, 20, 255), outline=(0, 255, 128, 200), width=3)
    draw.text((100, 960), "Response", font=f_ui, fill=(150, 150, 150, 255))
    draw.text((W - 200, 960), scene_data["status"], font=f_code, fill=(0, 255, 128, 255), anchor="mm")

    res_text = "{ \"status\": \"SUCCESS\", \"txn_id\": \"TXN_984192\", \"message\": \"Amount Debited\" }"
    draw.text((100, 1060), res_text, font=f_code, fill=(206, 145, 120, 255))

    img.save(out_png, "PNG")

def draw_architecture_scene(flow_steps: list, out_png: Path):
    W, H = 1080, 1920
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    f_title = get_font(36)
    f_step = get_font(34)

    draw.rectangle([(0, 0), (W, 14)], fill=(255, 255, 255, 40))
    draw.rectangle([(0, 0), (W, 14)], fill=(255, 69, 58, 255))

    draw.rounded_rectangle([(70, 100), (W - 70, 220)], radius=24, fill=(15, 23, 42, 240), outline=(255, 69, 58, 200), width=3)
    draw.text((W/2, 160), "⚡ WHY RETRY FAILS WITHOUT IDEMPOTENCY", font=f_title, fill=(255, 69, 58, 255), anchor="mm")

    y_pos = 320
    for i, step in enumerate(flow_steps):
        box_col = (239, 68, 68, 220) if "❌" in step else (30, 41, 59, 230)
        draw.rounded_rectangle([(80, y_pos), (W - 80, y_pos + 240)], radius=28, fill=box_col, outline=(255, 255, 255, 180), width=3)
        draw.text((W/2, y_pos + 120), step, font=f_step, fill=(255, 255, 255, 255), anchor="mm", align="center")
        y_pos += 300

    img.save(out_png, "PNG")

def draw_takeaway_scene(takeaway_text: str, out_png: Path):
    W, H = 1080, 1920
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    f_takeaway = get_font(40)

    draw.rectangle([(0, 0), (W, 14)], fill=(0, 255, 163, 255))
    draw.rounded_rectangle([(70, 400), (W - 70, 1450)], radius=36, fill=(15, 23, 42, 250), outline=(0, 255, 163, 255), width=4)
    wrapped = textwrap.wrap(takeaway_text, width=26)
    sy = 650
    for line in wrapped:
        color = (0, 255, 163, 255) if "💡" in line else (255, 255, 255, 255)
        draw.text((W/2, sy), line, font=f_takeaway, fill=color, anchor="mm", align="center")
        sy += 70

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
    print(f"Successfully posted {video_path.name} to Telegram ({TG_CHAT_ID})!")

async def build_full_reel(item: dict, final_mp4: Path):
    segment_videos = []

    s1 = item["scene_1"]
    s1_audio = TEMP_DIR / "s1_audio.mp3"
    await synth_line(s1["dialogue"], s1["voice"], s1_audio)
    s1_dur = get_duration(s1_audio) + 0.4
    s1_png = TEMP_DIR / "s1.png"
    draw_office_scene(s1["setting"], "ROHIT (Backend Dev)", (255, 69, 58, 255), s1["dialogue"], s1_png)

    s1_seg = TEMP_DIR / "seg_1.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(BG_VIDEO),
        "-loop", "1", "-i", str(s1_png), "-i", str(s1_audio),
        "-filter_complex", "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=brightness=-0.35:contrast=1.3[bg];[bg][1:v]overlay=0:0:shortest=1[v]",
        "-map", "[v]", "-map", "2:a", "-r", "30", "-fps_mode", "cfr",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21", "-c:a", "aac", "-b:a", "192k",
        "-t", str(s1_dur), "-pix_fmt", "yuv420p", str(s1_seg)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    segment_videos.append(s1_seg)

    s2 = item["scene_2"]
    s2_audio = TEMP_DIR / "s2_audio.mp3"
    await synth_line("Here is the Postman request returning 200 OK successfully.", "en-IN-PrabhatNeural", s2_audio)
    s2_dur = 4.0
    s2_png = TEMP_DIR / "s2.png"
    draw_postman_scene(s2, s2_png)

    s2_seg = TEMP_DIR / "seg_2.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(BG_VIDEO),
        "-loop", "1", "-i", str(s2_png), "-i", str(s2_audio),
        "-filter_complex", "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=brightness=-0.35:contrast=1.3[bg];[bg][1:v]overlay=0:0:shortest=1[v]",
        "-map", "[v]", "-map", "2:a", "-r", "30", "-fps_mode", "cfr",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21", "-c:a", "aac", "-b:a", "192k",
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
        "-filter_complex", "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=brightness=-0.35:contrast=1.3[bg];[bg][1:v]overlay=0:0:shortest=1[v]",
        "-map", "[v]", "-map", "2:a", "-r", "30", "-fps_mode", "cfr",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21", "-c:a", "aac", "-b:a", "192k",
        "-t", str(s3_dur), "-pix_fmt", "yuv420p", str(s3_seg)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    segment_videos.append(s3_seg)

    s4 = item["scene_4"]
    s4_audio = TEMP_DIR / "s4_audio.mp3"
    await synth_line("When client timeout triggers a retry without idempotency, the server processes both requests.", "en-IN-NeerjaNeural", s4_audio)
    s4_dur = 4.5
    s4_png = TEMP_DIR / "s4.png"
    draw_architecture_scene(s4["flow"], s4_png)

    s4_seg = TEMP_DIR / "seg_4.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(BG_VIDEO),
        "-loop", "1", "-i", str(s4_png), "-i", str(s4_audio),
        "-filter_complex", "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=brightness=-0.35:contrast=1.3[bg];[bg][1:v]overlay=0:0:shortest=1[v]",
        "-map", "[v]", "-map", "2:a", "-r", "30", "-fps_mode", "cfr",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21", "-c:a", "aac", "-b:a", "192k",
        "-t", str(s4_dur), "-pix_fmt", "yuv420p", str(s4_seg)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    segment_videos.append(s4_seg)

    t_audio = TEMP_DIR / "t_audio.mp3"
    await synth_line("Never test APIs with status 200 alone. Always validate idempotency headers.", "en-IN-NeerjaNeural", t_audio)
    t_dur = get_duration(t_audio) + 0.5
    t_png = TEMP_DIR / "takeaway.png"
    draw_takeaway_scene(item["takeaway"], t_png)

    t_seg = TEMP_DIR / "seg_takeaway.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(BG_VIDEO),
        "-loop", "1", "-i", str(t_png), "-i", str(t_audio),
        "-filter_complex", "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=brightness=-0.35:contrast=1.3[bg];[bg][1:v]overlay=0:0:shortest=1[v]",
        "-map", "[v]", "-map", "2:a", "-r", "30", "-fps_mode", "cfr",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21", "-c:a", "aac", "-b:a", "192k",
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
    print(f"Building Multi-Scene Office + Postman + Architecture Reel...")
    await build_full_reel(target, out_mp4)

    print(f"Publishing to Telegram...")
    send_to_telegram(out_mp4, target)

    target["done"] = True
    QUEUE_FILE.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n🔥 Done! Reel rendered and posted to Telegram!")

if __name__ == "__main__":
    asyncio.run(main())
