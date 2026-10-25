#!/usr/bin/env python3
"""Remote-capable HTTP checks; a missing pinned engine is never media acceptance."""
import base64
import hashlib
import io
import os
import secrets
import sys
import uuid
import wave

import httpx

# The host runner passes provider gateway authentication separately from app auth.
import json as _e2e_json
_GATEWAY_HEADERS = _e2e_json.loads(os.environ.get("E2E_GATEWAY_HEADERS_JSON", "{}"))
if not isinstance(_GATEWAY_HEADERS, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in _GATEWAY_HEADERS.items()):
    raise ValueError("E2E_GATEWAY_HEADERS_JSON must be an object of string headers")
_APPLICATION_HEADERS = {"Authorization": "Bearer " + os.environ["ABX_SERVER_TOKEN"]} if os.environ.get("ABX_SERVER_TOKEN") else {}


def check(condition, label):
    print(f"[{'PASS' if condition else 'FAIL'}] {label}", flush=True)
    if not condition:
        raise AssertionError(label)


def main():
    headers = {}
    if os.environ.get("E2E_TOKEN"):
        headers["X-Access-Token"] = os.environ["E2E_TOKEN"]
    if os.environ.get("ABX_SERVER_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["ABX_SERVER_TOKEN"]
    if os.environ.get("E2E_SERVER_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["E2E_SERVER_TOKEN"]
    with httpx.Client(base_url=os.environ.get("E2E_BASE_URL", "http://127.0.0.1:9000"), headers={**(headers), **_GATEWAY_HEADERS, **_APPLICATION_HEADERS}, timeout=150) as client:
        health = client.get("/health")
        check(health.status_code == 200 and health.json().get("status") == "ok", "server health")
        listed = client.get("/commands")
        names = {item["name"] for item in listed.json().get("commands", [])}
        check(listed.status_code == 200 and {"media_version", "media_setup_check", "media_probe", "transcode", "transcode_args", "media_args_smoke", "media_smoke"} <= names,
              "typed media commands registered")
        args_metadata = next(item for item in listed.json()["commands"] if item["name"] == "transcode_args")
        check(args_metadata["args"][0]["type"] == "string_array", "native JSON array metadata")
        for invalid in ['["-i","x.wav","y.wav"]', ["-i", 1, "y.wav"], None]:
            check(client.post("/commands/transcode_args", json={"args": invalid}).status_code == 400, "invalid native argv type rejected before invocation")
        response = client.post("/commands/transcode", json={})
        check(response.status_code == 400, "required paths enforced")
        response = client.post("/commands/transcode", json={"input_path": "in.wav", "output_name": "out.wav", "command_timeout": "oops"})
        check(response.status_code == 400, "timeout argument type enforced")
        response = client.post("/commands/transcode", json={"input_path": "in.wav", "output_name": "../out.wav", "preset": "wav"})
        check(response.status_code == 500 and response.json().get("type") == "ValueError", "output traversal rejected")
        response = client.post("/commands/media_probe", json={"input_path": "https://example.com/in.mp4"})
        check(response.status_code == 500 and response.json().get("type") == "ValueError", "network input rejected")
        response = client.post("/commands/media_setup_check", json={})
        check(response.status_code == 200, "read-only engine inspection")
        available = response.json()["result"].get("available") is True
        if not available:
            if os.environ.get("E2E_REQUIRE_MEDIA") == "1":
                check(False, "required pinned media runtime is installed")
            print("[SKIP] pinned FFmpeg unavailable; HTTP validation is not media/image/cloud acceptance", flush=True)
        else:
            response = client.post("/commands/media_version", json={})
            check(response.status_code == 200 and response.json().get("result") == "FFmpeg 7.1.5-0+deb13u1", "actual pinned FFmpeg and ffprobe")
            response = client.post("/commands/media_smoke", json={})
            check(response.status_code == 200 and response.json().get("result") == "FFmpeg CPU audio transcode OK",
                  "actual lossless conversion and independent PCM decode; owned files cleaned")
            response = client.post("/commands/media_video_smoke", json={})
            check(response.status_code == 200 and response.json().get("result") == "FFmpeg CPU H.264 video transcode OK",
                  "actual MP4 H.264 video, dimensions and owned cleanup")
            root = (os.environ.get("E2E_WORKSPACE") or os.environ.get("E2E_BASE_DIR") or "/home/user/app").rstrip("/")
            name = "media-controller-" + uuid.uuid4().hex
            owned = []

            def read(path):
                response = client.get("/files/download-stream", params={"path": path})
                response.raise_for_status()
                return base64.b64decode(response.json()["content_base64"], validate=True)

            try:
                pcm = secrets.token_bytes(32000)
                buffer = io.BytesIO()
                with wave.open(buffer, "wb") as source:
                    source.setnchannels(1)
                    source.setsampwidth(2)
                    source.setframerate(16000)
                    source.writeframes(pcm)
                original = buffer.getvalue()
                path = root + "/" + name + ".wav"
                response = client.post("/files/upload-stream", json={"path": path, "content_base64": base64.b64encode(original).decode()})
                response.raise_for_status()
                owned.append(path)
                check(read(path) == original, "out-of-band upload preserves controller-generated random PCM")
                for input_name, output_name, preset in ((name + ".wav", name + ".flac", "flac"),
                                                         (name + ".flac", name + "-roundtrip.wav", "wav")):
                    response = client.post("/commands/transcode", json={"input_path": input_name, "output_name": output_name,
                                                                         "preset": preset, "max_seconds": 1})
                    response.raise_for_status()
                    result = response.json()["result"]
                    expected_path = root + "/" + output_name
                    owned.append(expected_path)
                    check(result["output_path"] == expected_path, "artifact stays in owned workspace")
                    data = read(expected_path)
                    check(result["bytes"] == len(data) and result["sha256"] == hashlib.sha256(data).hexdigest(),
                          "independently downloaded artifact length and complete SHA256")
                    if preset == "flac":
                        check(data.startswith(b"fLaC"), "actual FLAC container bytes")
                    else:
                        with wave.open(io.BytesIO(data), "rb") as decoded:
                            check((decoded.getnchannels(), decoded.getsampwidth(), decoded.getframerate(), decoded.getnframes()) == (1, 2, 16000, 16000)
                                  and decoded.readframes(16000) == pcm, "external WAV parser verifies every random PCM sample after FLAC roundtrip")
                response = client.post("/commands/transcode_args", json={"args": ["-i", name + ".wav", "-c:a", "flac", "-vn", name + "-argv.flac"], "max_seconds": 1})
                response.raise_for_status()
                result = response.json()["result"]
                owned.append(root + "/" + name + "-argv.flac")
                data = read(owned[-1])
                check(result["exit_code"] == 0 and isinstance(result["stdout"], str) and isinstance(result["stderr"], str), "native FFmpeg result includes actual stdout/stderr/exit_code")
                check(data.startswith(b"fLaC") and result["sha256"] == hashlib.sha256(data).hexdigest(), "native argv HTTP artifact independently downloaded and checked")
                check(read(path) == original, "original upload remains byte-identical after both conversions")
            finally:
                for path in reversed(owned):
                    response = client.delete("/files", params={"path": path})
                    check(response.status_code in (200, 404), "owned controller artifact cleanup")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"[FAIL] {type(exc).__name__}: {exc}", flush=True)
        sys.exit(1)
