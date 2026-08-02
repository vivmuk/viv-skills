#!/usr/bin/env python3
"""
Prepare a Jessica TTS audio segment so its duration matches a full Seedance clip.

Usage:
    python prepare_audio_segment.py input.mp3 output.mp3 --target 15.0 --max-speed 1.12

Strategy:
1. If audio is shorter than target, slow it to fill more of the target, then pad silence.
2. If audio is longer than target, speed it up (up to max-speed).
3. Never produce audio longer than target; Seedance will pace lip motion incorrectly
   if the provided reference audio is truncated.
"""
import argparse
import subprocess
import json
import sys
from pathlib import Path


def get_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True, text=True, check=True
    ).stdout
    return float(json.loads(out)["format"]["duration"])


def apply_atempo(input_path: Path, output_path: Path, speed: float) -> None:
    # atempo only accepts 0.5–2.0; chain filters if outside that range
    if 0.5 <= speed <= 2.0:
        filter_str = f"atempo={speed}"
    elif speed < 0.5:
        chains = []
        remaining = speed
        while remaining < 0.5:
            chains.append("atempo=0.5")
            remaining /= 0.5
        chains.append(f"atempo={remaining}")
        filter_str = ",".join(chains)
    else:
        chains = []
        remaining = speed
        while remaining > 2.0:
            chains.append("atempo=2.0")
            remaining /= 2.0
        chains.append(f"atempo={remaining}")
        filter_str = ",".join(chains)

    subprocess.run(
        ["ffmpeg", "-y", "-i", str(input_path), "-filter:a", filter_str, "-vn", str(output_path)],
        check=True
    )


def pad_silence(input_path: Path, output_path: Path, target: float) -> None:
    dur = get_duration(input_path)
    pad = max(0.0, target - dur)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(input_path),
            "-af", f"apad=pad_dur={pad}",
            "-t", f"{target:.3f}",
            "-vn", str(output_path)
        ],
        check=True
    )


def main():
    parser = argparse.ArgumentParser(description="Prepare audio segment for Seedance R2V")
    parser.add_argument("input", type=Path, help="Input audio file")
    parser.add_argument("output", type=Path, help="Output audio file")
    parser.add_argument("--target", type=float, default=15.0, help="Target duration in seconds")
    parser.add_argument("--max-speed", type=float, default=1.12, help="Maximum speed multiplier")
    parser.add_argument("--slow-ratio", type=float, default=0.95, help="Slow-down ratio for short audio")
    args = parser.parse_args()

    original_dur = get_duration(args.input)
    print(f"Original duration: {original_dur:.3f}s")

    if original_dur > args.target:
        speed = args.target / original_dur
        if speed < 1.0 / args.max_speed:
            print(
                f"ERROR: audio needs {1/speed:.2f}x slow-down; max allowed is {args.max_speed:.2f}x. "
                "Rewrite the script or raise --max-speed.",
                file=sys.stderr
            )
            sys.exit(1)
        temp = args.output.with_suffix(".temp.mp3")
        apply_atempo(args.input, temp, speed)
        pad_silence(temp, args.output, args.target)
        temp.unlink(missing_ok=True)
    else:
        # Slow short audio to fill more of the target, then pad
        temp = args.output.with_suffix(".temp.mp3")
        apply_atempo(args.input, temp, args.slow_ratio)
        slowed_dur = get_duration(temp)
        if slowed_dur > args.target:
            # Slowing made it too long; use original speed and pad
            temp.unlink(missing_ok=True)
            pad_silence(args.input, args.output, args.target)
        else:
            pad_silence(temp, args.output, args.target)
            temp.unlink(missing_ok=True)

    final_dur = get_duration(args.output)
    print(f"Final duration: {final_dur:.3f}s")


if __name__ == "__main__":
    main()
