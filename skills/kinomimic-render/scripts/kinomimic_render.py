#!/usr/bin/env python3
"""Provider-adapted asynchronous video generation for KinoMimic."""

import argparse
import base64
import getpass
import json
import mimetypes
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional
import urllib.error
import urllib.parse
import urllib.request


PROVIDER = os.environ.get("KINOMIMIC_PROVIDER", "volcengine-ark")
BASE_URL = os.environ.get(
    "KINOMIMIC_BASE_URL",
    os.environ.get("SEEDANCE_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
).rstrip("/")
TASKS_PATH = "/contents/generations/tasks"
DEFAULT_MODEL = os.environ.get(
    "KINOMIMIC_MODEL",
    os.environ.get("SEEDANCE_MODEL", "doubao-seedance-2-0-260128"),
)
KEYCHAIN_SERVICE = "kinomimic-render"
KEYCHAIN_ACCOUNT = "KINOMIMIC_API_KEY"
LEGACY_KEYCHAIN_SERVICE = "codex-volcengine-seedance"
LEGACY_KEYCHAIN_ACCOUNT = "ARK_API_KEY"
LEGACY_SEEDANCE_KEYCHAIN_SERVICE = "codex-seedance-video"
LEGACY_SEEDANCE_KEYCHAIN_ACCOUNT = "SEEDANCE_API_KEY"
TERMINAL_STATUSES = {"succeeded", "failed", "expired", "cancelled"}
RATIOS = ("adaptive", "16:9", "4:3", "1:1", "3:4", "9:16", "21:9")
RESOLUTIONS = ("480p", "720p", "1080p", "4k")


class KinoMimicRenderError(RuntimeError):
    pass


def keychain_key(service: str, account: str) -> Optional[str]:
    if sys.platform != "darwin":
        return None
    try:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-s",
                service,
                "-a",
                account,
                "-w",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() or None
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def api_key() -> str:
    key = api_key_source()["value"]
    if not key:
        raise KinoMimicRenderError(
            "No API key found. Set KINOMIMIC_API_KEY. The Volcengine adapter "
            "also accepts SEEDANCE_API_KEY or ARK_API_KEY. On macOS, run "
            "`auth-store` to save it in Keychain."
        )
    return key


def api_key_source() -> Dict[str, Any]:
    for name in ("KINOMIMIC_API_KEY", "SEEDANCE_API_KEY", "ARK_API_KEY"):
        value = os.environ.get(name)
        if value:
            return {
                "found": True,
                "source": "environment",
                "name": name,
                "value": value,
            }
    for service, account in (
        (KEYCHAIN_SERVICE, KEYCHAIN_ACCOUNT),
        (LEGACY_KEYCHAIN_SERVICE, LEGACY_KEYCHAIN_ACCOUNT),
        (LEGACY_SEEDANCE_KEYCHAIN_SERVICE, LEGACY_SEEDANCE_KEYCHAIN_ACCOUNT),
    ):
        value = keychain_key(service, account)
        if value:
            return {
                "found": True,
                "source": "macos-keychain",
                "service": service,
                "account": account,
                "value": value,
            }
    return {"found": False, "source": None, "value": None}


def request_json(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    query: Optional[List[tuple]] = None,
) -> Dict[str, Any]:
    url = BASE_URL + path
    if query:
        url += "?" + urllib.parse.urlencode(query, doseq=True)
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": "Bearer " + api_key(),
            "Content-Type": "application/json",
            "User-Agent": "kinomimic-render/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(body)
        except json.JSONDecodeError:
            detail = body
        raise KinoMimicRenderError(f"API HTTP {exc.code}: {detail}") from None
    except urllib.error.URLError as exc:
        raise KinoMimicRenderError(f"API connection failed: {exc.reason}") from None


def is_remote(source: str) -> bool:
    return source.startswith(("https://", "http://", "asset://", "data:"))


def local_data_url(source: str, kind: str) -> str:
    path = Path(source).expanduser().resolve()
    if not path.is_file():
        raise KinoMimicRenderError(f"Local {kind} file not found: {path}")
    size = path.stat().st_size
    limits = {"image": 30 * 1024 * 1024, "audio": 15 * 1024 * 1024}
    if size >= limits[kind]:
        raise KinoMimicRenderError(
            f"Local {kind} file is too large ({size} bytes); limit is "
            f"{limits[kind]} bytes."
        )
    mime = mimetypes.guess_type(path.name)[0]
    allowed = {
        "image": {
            "image/jpeg",
            "image/png",
            "image/webp",
            "image/bmp",
            "image/tiff",
            "image/gif",
            "image/heic",
            "image/heif",
        },
        "audio": {"audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3"},
    }
    if mime not in allowed[kind]:
        raise KinoMimicRenderError(f"Unsupported {kind} type for {path.name}: {mime}")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    normalized = {
        "audio/x-wav": "audio/wav",
        "audio/mpeg": "audio/mp3",
    }.get(mime, mime)
    return f"data:{normalized};base64,{encoded}"


def media_source(source: str, kind: str) -> str:
    if is_remote(source):
        return source
    if kind == "video":
        raise KinoMimicRenderError(
            "Local video input needs a public URL, asset:// ID, or TOS upload. "
            "TOS upload is not configured in this skill yet."
        )
    return local_data_url(source, kind)


def validate_create(args: argparse.Namespace) -> None:
    has_frames = bool(args.first_frame or args.last_frame)
    has_refs = bool(args.image or args.video or args.audio)
    if args.last_frame and not args.first_frame:
        raise KinoMimicRenderError("--last-frame requires --first-frame.")
    if has_frames and has_refs:
        raise KinoMimicRenderError(
            "First/last-frame mode cannot be mixed with reference media mode."
        )
    if args.audio and not (args.image or args.video):
        raise KinoMimicRenderError("Audio cannot be the only reference media.")
    if not args.prompt and not has_frames and not has_refs and not args.request_json:
        raise KinoMimicRenderError("Provide --prompt, media input, or --request-json.")
    if args.duration != -1 and not 4 <= args.duration <= 15:
        raise KinoMimicRenderError("--duration must be -1 or an integer from 4 to 15.")
    if not 0 <= args.priority <= 9:
        raise KinoMimicRenderError("--priority must be from 0 to 9.")
    if not 3600 <= args.execution_expires_after <= 259200:
        raise KinoMimicRenderError(
            "--execution-expires-after must be from 3600 to 259200."
        )
    if len(args.image) > 9:
        raise KinoMimicRenderError("At most 9 reference images are supported.")
    if len(args.video) > 3:
        raise KinoMimicRenderError("At most 3 reference videos are supported.")
    if len(args.audio) > 3:
        raise KinoMimicRenderError("At most 3 reference audio files are supported.")
    if args.resolution in {"1080p", "4k"} and args.model in {
        "doubao-seedance-2-0-fast-260128",
        "doubao-seedance-2-0-mini-260615",
    }:
        raise KinoMimicRenderError("Fast and Mini support only 480p and 720p.")
    if args.resolution == "4k" and args.model != DEFAULT_MODEL:
        raise KinoMimicRenderError("4k is supported only by the full Seedance 2.0 model.")
    if args.safety_identifier:
        try:
            args.safety_identifier.encode("ascii")
        except UnicodeEncodeError:
            raise KinoMimicRenderError("--safety-identifier must be ASCII.") from None
        if len(args.safety_identifier) > 64:
            raise KinoMimicRenderError("--safety-identifier must be at most 64 characters.")


def build_payload(args: argparse.Namespace) -> Dict[str, Any]:
    if args.request_json:
        payload = json.loads(Path(args.request_json).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise KinoMimicRenderError("Request JSON must contain an object.")
        return payload

    content: List[Dict[str, Any]] = []
    if args.prompt:
        content.append({"type": "text", "text": args.prompt})
    if args.first_frame:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": media_source(args.first_frame, "image")},
                "role": "first_frame",
            }
        )
    if args.last_frame:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": media_source(args.last_frame, "image")},
                "role": "last_frame",
            }
        )
    for source in args.image:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": media_source(source, "image")},
                "role": "reference_image",
            }
        )
    for source in args.video:
        content.append(
            {
                "type": "video_url",
                "video_url": {"url": media_source(source, "video")},
                "role": "reference_video",
            }
        )
    for source in args.audio:
        content.append(
            {
                "type": "audio_url",
                "audio_url": {"url": media_source(source, "audio")},
                "role": "reference_audio",
            }
        )

    payload: Dict[str, Any] = {
        "model": args.model,
        "content": content,
        "resolution": args.resolution,
        "ratio": args.ratio,
        "duration": args.duration,
        "generate_audio": args.generate_audio,
        "watermark": args.watermark,
        "return_last_frame": args.return_last_frame,
        "execution_expires_after": args.execution_expires_after,
        "priority": args.priority,
    }
    optional = {
        "callback_url": args.callback_url,
        "safety_identifier": args.safety_identifier,
    }
    payload.update({key: value for key, value in optional.items() if value is not None})
    encoded_size = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    if encoded_size > 64 * 1024 * 1024:
        raise KinoMimicRenderError("Encoded request exceeds the 64 MB request-body limit.")
    return payload


def safe_task_id(task_id: str) -> str:
    if not task_id or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for ch in task_id):
        raise KinoMimicRenderError("Invalid task ID.")
    return task_id


def get_task(task_id: str) -> Dict[str, Any]:
    return request_json("GET", f"{TASKS_PATH}/{safe_task_id(task_id)}")


def download_url(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "kinomimic-render/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            with destination.open("wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
    except (urllib.error.URLError, OSError) as exc:
        raise KinoMimicRenderError(f"Download failed for {destination.name}: {exc}") from None


def save_result(result: Dict[str, Any], output_dir: str) -> Dict[str, Any]:
    task_id = safe_task_id(str(result.get("id", "unknown")))
    root = Path(output_dir).expanduser().resolve() / task_id
    root.mkdir(parents=True, exist_ok=True)
    (root / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    files: Dict[str, str] = {"result": str(root / "result.json")}
    content = result.get("content") or {}
    if content.get("video_url"):
        download_url(content["video_url"], root / "video.mp4")
        files["video"] = str(root / "video.mp4")
    if content.get("last_frame_url"):
        download_url(content["last_frame_url"], root / "last-frame.png")
        files["last_frame"] = str(root / "last-frame.png")
    return files


def wait_task(
    task_id: str,
    interval: int,
    timeout: int,
    download: bool,
    output_dir: str,
) -> Dict[str, Any]:
    deadline = time.monotonic() + timeout
    while True:
        result = get_task(task_id)
        status = result.get("status")
        if status in TERMINAL_STATUSES:
            if status == "succeeded" and download:
                result["_local_files"] = save_result(result, output_dir)
            return result
        if time.monotonic() >= deadline:
            raise KinoMimicRenderError(
                f"Timed out waiting for {task_id}; last status was {status}."
            )
        print(
            json.dumps({"id": task_id, "status": status}, ensure_ascii=False),
            file=sys.stderr,
            flush=True,
        )
        time.sleep(interval)


def command_auth_store(_: argparse.Namespace) -> Dict[str, Any]:
    if sys.platform != "darwin":
        raise KinoMimicRenderError("Keychain storage is currently supported only on macOS.")
    key = getpass.getpass("KINOMIMIC_API_KEY: ").strip()
    if not key:
        raise KinoMimicRenderError("Empty API key.")
    subprocess.run(
        [
            "security",
            "add-generic-password",
            "-U",
            "-s",
            KEYCHAIN_SERVICE,
            "-a",
            KEYCHAIN_ACCOUNT,
            "-w",
            key,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    return {"stored": True, "service": KEYCHAIN_SERVICE, "account": KEYCHAIN_ACCOUNT}


def command_auth_status(_: argparse.Namespace) -> Dict[str, Any]:
    source = api_key_source()
    redacted = {key: value for key, value in source.items() if key != "value"}
    redacted["provider"] = PROVIDER
    redacted["base_url"] = BASE_URL
    redacted["model"] = DEFAULT_MODEL
    redacted["key_is_redacted"] = bool(source.get("value"))
    return redacted


def command_create(args: argparse.Namespace) -> Dict[str, Any]:
    if PROVIDER != "volcengine-ark":
        raise KinoMimicRenderError(
            f"Unsupported provider: {PROVIDER}. Install or add a provider adapter."
        )
    validate_create(args)
    payload = build_payload(args)
    result = request_json("POST", TASKS_PATH, payload)
    if args.wait:
        result = wait_task(
            result["id"],
            args.poll_interval,
            args.timeout,
            True,
            args.output_dir,
        )
    return result


def command_get(args: argparse.Namespace) -> Dict[str, Any]:
    result = get_task(args.task_id)
    if args.download:
        if result.get("status") != "succeeded":
            raise KinoMimicRenderError("Only a succeeded task can be downloaded.")
        result["_local_files"] = save_result(result, args.output_dir)
    return result


def command_wait(args: argparse.Namespace) -> Dict[str, Any]:
    return wait_task(
        args.task_id,
        args.poll_interval,
        args.timeout,
        args.download,
        args.output_dir,
    )


def command_list(args: argparse.Namespace) -> Dict[str, Any]:
    query: List[tuple] = [
        ("page_num", args.page_num),
        ("page_size", args.page_size),
    ]
    if args.status:
        query.append(("filter.status", args.status))
    if args.model:
        query.append(("filter.model", args.model))
    for task_id in args.task_id:
        query.append(("filter.task_ids", safe_task_id(task_id)))
    return request_json("GET", TASKS_PATH, query=query)


def command_delete(args: argparse.Namespace) -> Dict[str, Any]:
    request_json("DELETE", f"{TASKS_PATH}/{safe_task_id(args.task_id)}")
    return {"id": args.task_id, "deleted_or_cancelled": True}


def command_render_plan(args: argparse.Namespace) -> Dict[str, Any]:
    plan_path = Path(args.plan).expanduser().resolve()
    if not plan_path.is_file():
        raise KinoMimicRenderError(f"Plan not found: {plan_path}")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if plan.get("schema") != "kinomimic.plan/v1":
        raise KinoMimicRenderError("Plan schema must be kinomimic.plan/v1.")
    generation = plan.get("generation") or {}
    inputs = plan.get("inputs") or {}
    namespace = argparse.Namespace(
        prompt=generation.get("prompt"),
        model=generation.get("model", DEFAULT_MODEL),
        image=list(inputs.get("reference_images", [])),
        video=list(inputs.get("reference_videos", [])),
        audio=list(inputs.get("reference_audio", [])),
        first_frame=inputs.get("first_frame"),
        last_frame=inputs.get("last_frame"),
        resolution=generation.get("resolution", "720p"),
        ratio=generation.get("ratio", "adaptive"),
        duration=int(generation.get("duration", 5)),
        generate_audio=bool(generation.get("generate_audio", True)),
        watermark=bool(generation.get("watermark", False)),
        return_last_frame=bool(generation.get("return_last_frame", False)),
        callback_url=generation.get("callback_url"),
        execution_expires_after=int(generation.get("execution_expires_after", 172800)),
        priority=int(generation.get("priority", 0)),
        safety_identifier=generation.get("safety_identifier"),
        request_json=None,
        wait=not args.no_wait,
        poll_interval=args.poll_interval,
        timeout=args.timeout,
        output_dir=args.output_dir,
    )
    result = command_create(namespace)
    result["_kinomimic"] = {
        "schema": plan["schema"],
        "provider": PROVIDER,
        "plan": str(plan_path),
    }
    return result


def add_output_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output-dir", default="./kinomimic-output")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description="Render KinoMimic plans through an asynchronous video provider."
    )
    sub = root.add_subparsers(dest="command", required=True)

    auth = sub.add_parser(
        "auth-store", help="Store KINOMIMIC_API_KEY in macOS Keychain."
    )
    auth.set_defaults(handler=command_auth_store)

    auth_status = sub.add_parser(
        "auth-status", help="Report where the API key will be read from without printing it."
    )
    auth_status.set_defaults(handler=command_auth_status)

    render = sub.add_parser(
        "render-plan", help="Render a versioned kinomimic.plan/v1 file."
    )
    render.add_argument("plan")
    render.add_argument("--output-dir", default="./kinomimic-output")
    render.add_argument("--poll-interval", type=int, default=30)
    render.add_argument("--timeout", type=int, default=7200)
    render.add_argument("--no-wait", action="store_true")
    render.set_defaults(handler=command_render_plan)

    create = sub.add_parser("create", help="Create a billable video-generation task.")
    create.add_argument("--prompt")
    create.add_argument("--model", default=DEFAULT_MODEL)
    create.add_argument("--image", action="append", default=[], metavar="SOURCE")
    create.add_argument("--video", action="append", default=[], metavar="URL_OR_ASSET")
    create.add_argument("--audio", action="append", default=[], metavar="SOURCE")
    create.add_argument("--first-frame")
    create.add_argument("--last-frame")
    create.add_argument("--resolution", choices=RESOLUTIONS, default="720p")
    create.add_argument("--ratio", choices=RATIOS, default="adaptive")
    create.add_argument("--duration", type=int, default=5)
    audio_group = create.add_mutually_exclusive_group()
    audio_group.add_argument(
        "--generate-audio", dest="generate_audio", action="store_true"
    )
    audio_group.add_argument(
        "--no-generate-audio", dest="generate_audio", action="store_false"
    )
    create.set_defaults(generate_audio=True)
    create.add_argument("--watermark", action="store_true")
    create.add_argument("--return-last-frame", action="store_true")
    create.add_argument("--callback-url")
    create.add_argument("--execution-expires-after", type=int, default=172800)
    create.add_argument("--priority", type=int, default=0)
    create.add_argument("--safety-identifier")
    create.add_argument("--request-json", help="Advanced: submit a complete request JSON.")
    create.add_argument("--wait", action="store_true")
    create.add_argument("--poll-interval", type=int, default=30)
    create.add_argument("--timeout", type=int, default=7200)
    add_output_options(create)
    create.set_defaults(handler=command_create)

    get = sub.add_parser("get", help="Get one task.")
    get.add_argument("task_id")
    get.add_argument("--download", action="store_true")
    add_output_options(get)
    get.set_defaults(handler=command_get)

    wait = sub.add_parser("wait", help="Poll until a task reaches a terminal state.")
    wait.add_argument("task_id")
    wait.add_argument("--poll-interval", type=int, default=30)
    wait.add_argument("--timeout", type=int, default=7200)
    wait.add_argument("--download", action="store_true")
    add_output_options(wait)
    wait.set_defaults(handler=command_wait)

    list_parser = sub.add_parser("list", help="List tasks from the last seven days.")
    list_parser.add_argument("--page-num", type=int, default=1)
    list_parser.add_argument("--page-size", type=int, default=20)
    list_parser.add_argument(
        "--status",
        choices=("queued", "running", "cancelled", "succeeded", "failed", "expired"),
    )
    list_parser.add_argument("--model", help="Endpoint ID filter.")
    list_parser.add_argument("--task-id", action="append", default=[])
    list_parser.set_defaults(handler=command_list)

    delete = sub.add_parser(
        "delete", help="Cancel a queued task or delete a completed task record."
    )
    delete.add_argument("task_id")
    delete.set_defaults(handler=command_delete)
    return root


def main() -> int:
    try:
        args = parser().parse_args()
        result = args.handler(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (
        KinoMimicRenderError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
