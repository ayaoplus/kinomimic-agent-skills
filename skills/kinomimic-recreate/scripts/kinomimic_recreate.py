#!/usr/bin/env python3
"""Prepare full-video analysis artifacts and validate KinoMimic plans."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Dict, List


class KinoMimicError(RuntimeError):
    pass


def run(command: List[str], capture: bool = False) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            command,
            check=True,
            text=True,
            capture_output=capture,
        )
    except FileNotFoundError as exc:
        raise KinoMimicError(f"Required command not found: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() if exc.stderr else str(exc)
        raise KinoMimicError(f"Command failed: {detail}") from None


def ffprobe(video: Path) -> Dict[str, Any]:
    result = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size,bit_rate:"
            "stream=index,codec_type,codec_name,width,height,r_frame_rate,"
            "sample_rate,channels",
            "-of",
            "json",
            str(video),
        ],
        capture=True,
    )
    return json.loads(result.stdout)


def detect_scenes(video: Path, opening_seconds: float) -> List[float]:
    result = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(video),
            "-t",
            str(opening_seconds),
            "-vf",
            "select='gt(scene,0.22)',showinfo",
            "-an",
            "-f",
            "null",
            "-",
        ],
        text=True,
        capture_output=True,
    )
    times: List[float] = []
    for line in result.stderr.splitlines():
        marker = "pts_time:"
        if marker not in line:
            continue
        value = line.split(marker, 1)[1].split()[0]
        try:
            times.append(round(float(value), 3))
        except ValueError:
            pass
    return times


def run_ocr(frames_dir: Path, output: Path) -> None:
    if not shutil.which("tesseract"):
        output.write_text("Tesseract is not installed.\n", encoding="utf-8")
        return
    lines: List[str] = []
    for frame in sorted(frames_dir.glob("*.jpg")):
        result = subprocess.run(
            ["tesseract", str(frame), "stdout", "-l", "eng+chi_sim"],
            text=True,
            capture_output=True,
        )
        text = " ".join(result.stdout.split())
        if text:
            lines.append(f"{frame.name}: {text}")
    output.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def prepare(args: argparse.Namespace) -> Dict[str, Any]:
    source = Path(args.source).expanduser().resolve()
    if not source.is_file():
        raise KinoMimicError(f"Source video not found: {source}")
    root = Path(args.output_dir).expanduser().resolve()
    analysis = root / "source-analysis"
    frames = analysis / "frames"
    frames.mkdir(parents=True, exist_ok=True)

    metadata = ffprobe(source)
    duration = float(metadata["format"]["duration"])
    analysis_duration = duration
    frame_count = max(1, int(analysis_duration * args.frames_per_second))
    columns = min(4, frame_count)
    rows = (frame_count + columns - 1) // columns

    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-t",
            str(analysis_duration),
            "-vf",
            f"fps={args.frames_per_second},scale=720:-1",
            str(frames / "frame-%03d.jpg"),
        ]
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-t",
            str(analysis_duration),
            "-vf",
            f"fps={args.frames_per_second},scale=360:-1,tile={columns}x{rows}",
            "-frames:v",
            "1",
            "-update",
            "1",
            str(analysis / "storyboard.jpg"),
        ]
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-t",
            str(analysis_duration),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(analysis / "opening.wav"),
        ]
    )
    run_ocr(frames, analysis / "ocr.txt")

    media_analysis = {
        "source": str(source),
        "source_duration": duration,
        "analysis_duration": analysis_duration,
        "input_contract": "user-selected-complete-reference-video",
        "metadata": metadata,
        "scene_change_times": detect_scenes(source, analysis_duration),
        "frames_per_second": args.frames_per_second,
        "storyboard": str(analysis / "storyboard.jpg"),
        "frames_directory": str(frames),
        "audio": str(analysis / "opening.wav"),
        "ocr": str(analysis / "ocr.txt"),
    }
    media_path = analysis / "media-analysis.json"
    media_path.write_text(
        json.dumps(media_analysis, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    requirements = "\n".join(args.requirement).strip()
    requirements_path = root / "user-requirements.md"
    if requirements:
        requirements_path.write_text(requirements + "\n", encoding="utf-8")
    elif not requirements_path.exists():
        requirements_path.write_text(
            "# User requirements\n\n"
            "- Preserve the supplied video as the complete reference; do not auto-trim.\n"
            "- Add requested role, product, scene, language, or shot-level changes here before planning.\n",
            encoding="utf-8",
        )

    template = {
        "schema": "kinomimic.analysis/v1",
        "source": {
            "path": str(source),
            "duration": duration,
        },
        "user_requirements": requirements,
        "summary": "",
        "content_type": "",
        "narrative_structure": "",
        "commercial_logic": None,
        "characters": [],
        "timeline": [],
        "objects_and_products": [],
        "evidence_chain": [],
        "must_preserve": [],
        "may_change": [],
        "uncertain_facts": [],
    }
    template_path = root / "analysis.template.json"
    template_path.write_text(
        json.dumps(template, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    script_template_path = root / "recreation-script.template.md"
    if not script_template_path.exists():
        script_template_path.write_text(
            "# Recreation script\n\n"
            "## 1. Video overview\n\n"
            "One sentence covering the core content, proof/action chain, main scene, and pacing.\n\n"
            "## 2. Adaptation blueprint\n\n"
            "- User requirements:\n"
            "  - ...\n"
            "- Must preserve:\n"
            "  - ...\n"
            "- May change:\n"
            "  - ...\n"
            "- Uncertain facts to confirm:\n"
            "  - ...\n\n"
            "## 3. Shot script\n\n"
            "Write every independent shot in source order. Do not add, delete, or reorder shots unless the user explicitly asks.\n\n"
            "| # | Time | Visual prompt | Voice / spoken line |\n"
            "|---|---:|---|---|\n"
            "| 1 | 0.0-0.0s | 中文一句话：以【景别，运镜】开头，包含场景、人物/手部状态、关键道具、动作、表情反应、画面焦点、节奏。 | 留空或写目标语言台词 |\n\n"
            "## 4. Render prompt\n\n"
            "Condense the shot script into one chronological provider prompt for `generation.prompt`.\n",
            encoding="utf-8",
        )
    return {
        "project_dir": str(root),
        "media_analysis": str(media_path),
        "storyboard": str(analysis / "storyboard.jpg"),
        "analysis_template": str(template_path),
        "user_requirements": str(requirements_path),
        "script_template": str(script_template_path),
    }


def validate_plan_data(plan: Dict[str, Any]) -> None:
    if plan.get("schema") != "kinomimic.plan/v1":
        raise KinoMimicError("Plan schema must be kinomimic.plan/v1.")
    prompt = (plan.get("generation") or {}).get("prompt")
    if not isinstance(prompt, str) or len(prompt.strip()) < 40:
        raise KinoMimicError("generation.prompt must be a detailed prompt.")
    duration = (plan.get("generation") or {}).get("duration", 5)
    if duration != -1 and not 4 <= int(duration) <= 15:
        raise KinoMimicError("generation.duration must be -1 or 4..15.")
    inputs = plan.get("inputs") or {}
    if not isinstance(inputs.get("reference_images", []), list):
        raise KinoMimicError("inputs.reference_images must be a list.")
    script = plan.get("script")
    if script is not None:
        if not isinstance(script, dict):
            raise KinoMimicError("script must be an object when present.")
        shots = script.get("shots", [])
        if not isinstance(shots, list):
            raise KinoMimicError("script.shots must be a list when present.")


def validate_plan(args: argparse.Namespace) -> Dict[str, Any]:
    plan_path = Path(args.plan).expanduser().resolve()
    if not plan_path.is_file():
        raise KinoMimicError(f"Generation plan not found: {plan_path}")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    validate_plan_data(plan)
    return {"valid": True, "plan": str(plan_path), "schema": plan["schema"]}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare full reference-video analysis artifacts."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    prepare_parser = sub.add_parser("prepare", help="Extract local analysis artifacts.")
    prepare_parser.add_argument("source")
    prepare_parser.add_argument("--frames-per-second", type=float, default=2)
    prepare_parser.add_argument("--output-dir", required=True)
    prepare_parser.add_argument(
        "--requirement",
        action="append",
        default=[],
        help="User adaptation requirement to preserve in user-requirements.md.",
    )
    prepare_parser.set_defaults(handler=prepare)

    validate_parser = sub.add_parser(
        "validate-plan", help="Validate a kinomimic.plan/v1 file."
    )
    validate_parser.add_argument("plan")
    validate_parser.set_defaults(handler=validate_plan)
    return parser


def main() -> int:
    try:
        args = build_parser().parse_args()
        print(json.dumps(args.handler(args), ensure_ascii=False, indent=2))
        return 0
    except (KinoMimicError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
