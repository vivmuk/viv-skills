import subprocess, json, os
from pathlib import Path

root = Path.home() / "faces" / "aipharmaxchange_openevidence_30s"
host_dir = root / "host_video"
final_dir = root / "final"

# Paths
slide1 = root / "slides" / "slide1_intro_cases_watercolor.jpg"
slide2 = root / "slides" / "slide2_scores_conclusion_watercolor.jpg"
host1 = host_dir / "seg1.mp4"
host2 = host_dir / "seg2.mp4"
audio1 = root / "audio" / "seg1.mp3"
audio2 = root / "audio" / "seg2.mp3"

# 1. Check host video durations / existence
for f in [host1, host2]:
    if not f.exists():
        raise FileNotFoundError(f"Missing {f}")

# 2. Build per-segment split-screen videos (top slide + bottom host, 16:9)
#    Slide fills top ~55%, host scaled/padded bottom ~45%
#    Target: 1536x864. Top: 1536x475, bottom: 1536x389

def build_split(slide_path, host_path, audio_path, out_path):
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(slide_path),
        "-i", str(host_path),
        "-i", str(audio_path),
        "-filter_complex",
        "[0:v]scale=1536:475:force_original_aspect_ratio=decrease,pad=1536:475:(ow-iw)/2:(oh-ih)/2[top];"
        "[1:v]scale=1536:389:force_original_aspect_ratio=decrease,pad=1536:389:(ow-iw)/2:(oh-ih)/2[bot];"
        "[top][bot]vstack=inputs=2[v]",
        "-map", "[v]", "-map", "2:a:0",
        "-c:v", "libx264", "-crf", "23", "-preset", "fast",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-shortest", "-t", "15",
        str(out_path)
    ]
    subprocess.run(cmd, check=True)

build_split(slide1, host1, audio1, final_dir / "split_seg1.mp4")
build_split(slide2, host2, audio2, final_dir / "split_seg2.mp4")

# 3. Concatenate segments with exact durations
concat_list = final_dir / "concat.txt"
concat_list.write_text(
    f"file '{final_dir / 'split_seg1.mp4'}'\nduration 15.0\n"
    f"file '{final_dir / 'split_seg2.mp4'}'\nduration 15.0\n"
)

final_out = final_dir / "openevidence_30s_final.mp4"
subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
    "-c", "copy", str(final_out)
], check=True)

print("Final video:", final_out)
