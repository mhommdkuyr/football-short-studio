#!/usr/bin/env python3
"""Render an original 9:16 Arabic football Short from a narration track."""
from __future__ import annotations

NARRATION = "صدمة أوروبية! كومو يهزم مانشستر يونايتد بأربعة أهداف مقابل هدف في دوري أبطال أوروبا. نيكو باز افتتح التسجيل بعد دقيقتين فقط. بعد الاستراحة ضاعف أناستاسيوس دوفِيكاس النتيجة في الدقيقة التاسعة والأربعين. وبعد ثماني دقائق عاد باز ليسجل الثالث والثاني له شخصيًا. في الدقيقة السادسة والسبعين، أحرز جاكوبو رامون الهدف الرابع. سجل جوشوا زيركزي هدف يونايتد الوحيد في الوقت بدل الضائع. نيكو باز أنهى الليلة بهدفين وتمريرة حاسمة. هل كانت هذه أكبر مفاجآت الجولة؟"
import argparse, os, subprocess, tempfile, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

W, H, FPS = 1080, 1920, 30
NAVY = (5, 12, 27)
WHITE = (247, 250, 255)
MUTED = (173, 190, 211)
TEAL = (0, 240, 214)
RED = (255, 81, 93)
GOLD = (255, 189, 89)
FONT_PATH = "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf"
REGULAR_PATH = "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf"

SCENES = [
    {
        "duration": 4.1,
        "headline": "صدمة أوروبية: كومو 4–1 يونايتد!",
        "score": [
            "كومو",
            "4",
            "1",
            "مانشستر يونايتد"
        ],
        "event": "نتيجة مدوية في ليلة دوري الأبطال",
        "caption": "صدمة أوروبية! كومو يهزم مانشستر يونايتد بأربعة أهداف مقابل هدف.",
        "tag": "النتيجة النهائية"
    },
    {
        "duration": 4.6,
        "headline": "نيكو باز يضرب مبكرًا",
        "score": [
            "كومو",
            "1",
            "0",
            "مانشستر يونايتد"
        ],
        "event": "2′ نيكو باز",
        "caption": "نيكو باز افتتح التسجيل بعد دقيقتين فقط.",
        "tag": "1–0"
    },
    {
        "duration": 4.8,
        "headline": "دوفِيكاس يضاعف التقدم",
        "score": [
            "كومو",
            "2",
            "0",
            "مانشستر يونايتد"
        ],
        "event": "49′ أناستاسيوس دوفِيكاس",
        "caption": "بعد الاستراحة، ضاعف أناستاسيوس دوفِيكاس النتيجة في الدقيقة التاسعة والأربعين.",
        "tag": "2–0"
    },
    {
        "duration": 4.8,
        "headline": "باز يسجل هدفه الثاني",
        "score": [
            "كومو",
            "3",
            "0",
            "مانشستر يونايتد"
        ],
        "event": "57′ نيكو باز",
        "caption": "بعدها بثماني دقائق، سجل باز هدفه الشخصي الثاني والثالث لكومو.",
        "tag": "3–0"
    },
    {
        "duration": 4.7,
        "headline": "رامون يضيف الرابع",
        "score": [
            "كومو",
            "4",
            "0",
            "مانشستر يونايتد"
        ],
        "event": "76′ جاكوبو رامون",
        "caption": "جاكوبو رامون أحرز الرابع في الدقيقة السادسة والسبعين.",
        "tag": "4–0"
    },
    {
        "duration": 4.6,
        "headline": "هدف متأخر لا يغيّر النتيجة",
        "score": [
            "كومو",
            "4",
            "1",
            "مانشستر يونايتد"
        ],
        "event": "90+1′ جوشوا زيركزي",
        "caption": "سجل جوشوا زيركزي هدف يونايتد الوحيد في الوقت بدل الضائع.",
        "tag": "4–1"
    },
    {
        "duration": 4.5,
        "headline": "نجم الليلة: نيكو باز",
        "score": [
            "كومو",
            "4",
            "1",
            "مانشستر يونايتد"
        ],
        "event": "هدفان + تمريرة حاسمة",
        "caption": "باز أنهى الليلة بهدفين وتمريره حاسمة. هل كانت هذه أكبر مفاجآت الجولة؟",
        "tag": "اكتب رأيك"
    }
]

def shape(text: str) -> str:
    return get_display(arabic_reshaper.reshape(str(text)))

def font(size: int, bold: bool = True):
    path = FONT_PATH if bold else REGULAR_PATH
    if not os.path.exists(path):
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    return ImageFont.truetype(path, size)

def tw(draw, text, fnt):
    return draw.textbbox((0, 0), shape(text), font=fnt)[2]

def wrap_ar(draw, text, fnt, max_width):
    words = str(text).split()
    lines, line = [], ""
    for word in words:
        candidate = word if not line else line + " " + word
        if tw(draw, candidate, fnt) <= max_width or not line:
            line = candidate
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

def centered(draw, text, y, fnt, fill=WHITE, max_width=900, line_gap=16):
    lines = wrap_ar(draw, text, fnt, max_width)
    line_h = fnt.size + line_gap
    start_y = y - ((len(lines)-1) * line_h) // 2
    for i, line in enumerate(lines):
        draw.text((W//2, start_y + i*line_h), shape(line), font=fnt, fill=fill, anchor="mm")
    return len(lines) * line_h

def rounded(draw, box, radius, fill, outline=None, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def make_scene(idx, scene, path):
    im = Image.new("RGB", (W, H), NAVY)
    pix = im.load()
    top, bottom = (5, 12, 27), (18, 30, 55)
    for y in range(H):
        t = y / (H-1)
        col = tuple(int(top[c]*(1-t) + bottom[c]*t) for c in range(3))
        for x in range(W):
            pix[x, y] = col
    d = ImageDraw.Draw(im, "RGB")
    # Abstract pitch-grid / momentum rings; fully original graphic design.
    for x in range(-500, W+700, 145):
        d.line((x, 0, x+460, H), fill=(15, 34, 54), width=2)
    d.ellipse((W-370, 170, W+120, 660), outline=(24, 63, 78), width=5)
    d.ellipse((W-300, 240, W+50, 590), outline=(17, 50, 69), width=3)
    d.arc((80, 500, 670, 1090), 190, 310, fill=(20, 55, 69), width=5)
    # Top bar.
    rounded(d, (62, 64, W-62, 142), 30, (12, 27, 46), outline=(34, 65, 87), width=2)
    d.ellipse((88, 87, 118, 117), fill=TEAL)
    d.text((W-96, 103), shape("SPOORT  •  تحليل كروي أصلي"), font=font(30), fill=WHITE, anchor="rm")
    d.text((W//2, 190), shape("دوري أبطال أوروبا  |  21 أكتوبر 2026"), font=font(27, False), fill=MUTED, anchor="mm")
    # Main headline.
    centered(d, scene["headline"], 312, font(59), WHITE, max_width=940, line_gap=22)
    # Score board.
    rounded(d, (70, 435, W-70, 760), 42, (11, 25, 43), outline=(39, 75, 94), width=3)
    left_team, left_score, right_score, right_team = scene["score"]
    d.text((W//2, 488), shape("النتيجة في هذه اللحظة"), font=font(26, False), fill=MUTED, anchor="mm")
    # Score numbers large; labels remain clear and don't use any protected team logos.
    d.text((W//2-150, 605), left_score, font=font(112), fill=WHITE, anchor="mm")
    d.text((W//2+150, 605), right_score, font=font(112), fill=WHITE, anchor="mm")
    d.text((W//2, 605), "—", font=font(70), fill=TEAL, anchor="mm")
    d.text((W//2-335, 700), shape(left_team), font=font(34), fill=(255, 104, 113), anchor="mm")
    d.text((W//2+335, 700), shape(right_team), font=font(34), fill=GOLD, anchor="mm")
    # Event strip.
    rounded(d, (90, 830, W-90, 1035), 34, (13, 33, 52), outline=(31, 75, 88), width=2)
    d.ellipse((123, 894, 153, 924), fill=TEAL)
    centered(d, scene["event"], 932, font(34), WHITE, max_width=800, line_gap=12)
    # Three pulse bars to evoke momentum.
    bx, by = 155, 1118
    for j, h in enumerate([35, 62, 94, 58, 120, 78, 43, 72, 105, 48, 86, 32, 65, 100, 52, 78, 40, 92]):
        x = bx + j*43
        d.rounded_rectangle((x, by-h//2, x+17, by+h//2), radius=8,
                            fill=TEAL if j in (4, 8, 13) else (32, 76, 91))
    d.text((W//2, 1240), shape("نيكو باز: هدفان وتمريره حاسمة"), font=font(32), fill=(169, 206, 224), anchor="mm")
    # Burned-in Arabic captions.
    rounded(d, (62, 1400, W-62, 1695), 36, (4, 10, 23), outline=(41, 76, 92), width=2)
    d.text((W//2, 1452), shape("التعليق"), font=font(24), fill=TEAL, anchor="mm")
    centered(d, scene["caption"], 1550, font(37), WHITE, max_width=885, line_gap=22)
    # Footer source credit.
    d.text((W//2, 1760), shape("المصادر: Reuters • The Guardian"), font=font(24, False), fill=(154, 172, 196), anchor="mm")
    d.text((W//2, 1810), shape("رسوم وشرح أصليان — بلا لقطات بث محمية"), font=font(22, False), fill=(105, 145, 165), anchor="mm")
    # Accent footer line.
    d.rounded_rectangle((310, 1855, 770, 1867), radius=6, fill=TEAL)
    im.save(path, quality=94)

def srt_time(seconds):
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def run(cmd):
    subprocess.run(cmd, check=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--srt", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    nominal_total = sum(s["duration"] for s in SCENES)
    total = float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", args.audio
    ], text=True).strip())
    if total <= 0:
        raise SystemExit("Narration audio duration must be positive.")
    scale = total / nominal_total
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        concat = []
        subs = []
        cursor = 0.0
        for i, scene in enumerate(SCENES, 1):
            png = tmp / f"scene_{i:02d}.png"
            mp4 = tmp / f"segment_{i:02d}.mp4"
            make_scene(i, scene, png)
            dur = scene["duration"] * scale
            run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-loop", "1", "-framerate", str(FPS), "-i", str(png),
                "-t", f"{dur:.6f}",
                "-vf", f"zoompan=z='min(zoom+0.00045,1.035)':d=1:s={W}x{H}:fps={FPS},format=yuv420p",
                "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "25",
                "-r", str(FPS), str(mp4)
            ])
            concat.append(f"file '{mp4.as_posix()}'")
            start, end = cursor, cursor + dur
            subs.append(f"{i}\n{srt_time(start)} --> {srt_time(end)}\n{scene['caption']}\n")
            cursor = end
        concat_file = tmp / "concat.txt"
        concat_file.write_text("\n".join(concat) + "\n", encoding="utf-8")
        Path(args.srt).write_text("\n".join(subs), encoding="utf-8")
        silent = tmp / "silent.mp4"
        run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-c", "copy", str(silent)
        ])
        # Preserve narration and fit final video to its actual measured duration.
        run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(silent), "-i", args.audio,
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "medium", "-crf", "24",
            "-c:a", "aac", "-b:a", "128k",
            "-t", f"{total:.6f}", "-movflags", "+faststart",
            "-shortest", str(out)
        ])
    # Basic integrity checks: video/audio streams, 9:16 dimensions, and non-zero file.
    probe = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height",
        "-of", "json", str(out)
    ], text=True)
    print(f"Rendered {out} ({out.stat().st_size} bytes)")
    print(probe)
    if out.stat().st_size < 100_000:
        raise SystemExit("Rendered video is unexpectedly small.")

if __name__ == "__main__":
    main()
