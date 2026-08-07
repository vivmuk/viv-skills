#!/usr/bin/env python3
"""Assemble four approved host clips and 3:2 slides into a 35/65 LinkedIn video."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


HOST_WIDTH = 672
SLIDE_WIDTH = 1248
HEIGHT = 1080
FPS = 30


def run(command: list[str]) -> None:
    subprocess.run(command, check=True, capture_output=True)


def duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def parse_segments(value: str) -> list[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        raise argparse.ArgumentTypeError("Supply at least one segment ID.")
    return items


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slides-dir", type=Path, required=True)
    parser.add_argument("--host-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--segments", type=parse_segments, default=["01", "02", "03", "04"])
    parser.add_argument("--work-dir", type=Path)
    args = parser.parse_args()

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    work_dir = (args.work_dir or output.parent / f"{output.stem}-segments").resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    filters = (
        f"[0:v]scale={SLIDE_WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={SLIDE_WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=0xfbf8f0,setsar=1[slide];"
        f"[1:v]scale={HOST_WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={HOST_WIDTH}:{HEIGHT},setsar=1,tpad=stop_mode=clone:stop_duration=0.10[host];"
        "[host][slide]hstack=inputs=2[v]"
    )

    rendered: list[Path] = []
    for segment_id in args.segments:
        slide = args.slides_dir / f"slide_{segment_id}.png"
        host = args.host_dir / f"segment_{segment_id}.mp4"
        rendered_clip = work_dir / f"segment_{segment_id}.mp4"
        for asset in (slide, host):
            if not asset.is_file():
                raise FileNotFoundError(f"Missing required asset: {asset}")
        run(
            [
                "ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-i", str(slide),
                "-i", str(host), "-filter_complex", filters, "-map", "[v]", "-map", "1:a:0",
                "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-r", str(FPS),
                "-c:a", "aac", "-b:a", "192k", "-shortest", str(rendered_clip),
            ]
        )
        rendered.append(rendered_clip)

    concat = work_dir / "concat.txt"
    concat.write_text(
        "".join(f"file '{clip.as_posix().replace(chr(39), chr(92) + chr(39))}'\n" for clip in rendered),
        encoding="utf-8",
    )
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(output)])

    video_duration = duration(output)
    print(f"Created {output} ({video_duration:.3f}s, {HOST_WIDTH}/{SLIDE_WIDTH} host/slide layout)")


if __name__ == "__main__":
    main()
