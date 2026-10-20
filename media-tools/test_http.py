"""Actual authenticated server and typed Python SDK file/command contracts."""
import asyncio
import hashlib
import io
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
import wave

import httpx
import pytest

from agent_sandbox.api.server_client import ServerClient
from agent_sandbox.models.errors import CommandArgumentError, CommandExecutionError


@pytest.fixture
def server(tmp_path):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    token = secrets.token_hex(16)
    env = {k: v for k, v in os.environ.items() if not any(word in k.upper() for word in ("TOKEN", "SECRET", "API_KEY", "PASSWORD"))}
    env.update(WORKSPACE=str(tmp_path), ABX_SERVER_BASE_DIR=str(tmp_path), ABX_SERVER_PORT=str(port),
               ABX_SERVER_TOKEN=token, ABX_PTY_PORT="0")
    process = subprocess.Popen([sys.executable, str(Path(__file__).with_name("commands.py"))], env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    try:
        with httpx.Client(headers={"Authorization": "Bearer " + token}) as client:
            for _ in range(100):
                if process.poll() is not None:
                    pytest.fail("actual media server exited before readiness")
                try:
                    if client.get(url + "/health", timeout=.5).status_code == 200:
                        break
                except httpx.TransportError:
                    pass
                time.sleep(.05)
            else:
                pytest.fail("actual media server did not become healthy")
        yield url, token, tmp_path
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        assert not list(tmp_path.iterdir()), "SDK cleanup must remove every owned upload/output"


def test_authenticated_sdk_random_pcm_roundtrip_and_error_types(server):
    url, token, root = server
    assert httpx.get(url + "/commands").status_code == 401
    pcm = secrets.token_bytes(32000)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as source:
        source.setnchannels(1)
        source.setsampwidth(2)
        source.setframerate(16000)
        source.writeframes(pcm)

    async def run():
        owned = []
        async with ServerClient(url, token=token, timeout=150) as client:
            try:
                assert await client.health()
                assert (await client.commands.run("media_setup_check"))["available"] is True
                with pytest.raises(CommandArgumentError):
                    await client.commands.run("transcode")
                with pytest.raises(CommandExecutionError):
                    await client.commands.run("media_probe", input_path="../forbidden")
                source = str(root / "source.wav")
                await client.files.upload(source, buffer.getvalue())
                owned.append(source)
                for input_name, output_name, preset in (("source.wav", "compressed.flac", "flac"),
                                                         ("compressed.flac", "decoded.wav", "wav")):
                    result = await client.commands.run("transcode", input_path=input_name, output_name=output_name,
                                                       preset=preset, max_seconds=1)
                    expected = str(root / output_name)
                    owned.append(expected)
                    assert result["output_path"] == expected
                    data = await client.files.download(expected)
                    assert len(data) == result["bytes"] and hashlib.sha256(data).hexdigest() == result["sha256"]
                    if preset == "wav":
                        with wave.open(io.BytesIO(data), "rb") as decoded:
                            assert (decoded.getnchannels(), decoded.getsampwidth(), decoded.getframerate(), decoded.getnframes()) == (1, 2, 16000, 16000)
                            assert decoded.readframes(16000) == pcm
                catalogue = {item.name: item for item in await client.commands.list()}
                assert catalogue["transcode_args"].args[0].type == "string_array"
                with pytest.raises(CommandArgumentError):
                    await client.commands.run("transcode_args", args='["-i","source.wav","x.wav"]')
                with pytest.raises(CommandArgumentError):
                    await client.commands.run("transcode_args", args=["-i", 3, "x.wav"])
                result = await client.commands.run("transcode_args", args=["-i", "source.wav", "-c:a", "flac", "-vn", "args.flac"], max_seconds=1)
                owned.append(str(root / "args.flac"))
                assert result["exit_code"] == 0 and isinstance(result["stdout"], str) and isinstance(result["stderr"], str)
                data = await client.files.download(result["output_path"])
                assert data.startswith(b"fLaC") and hashlib.sha256(data).hexdigest() == result["sha256"]
                assert await client.files.download(source) == buffer.getvalue()
            finally:
                for path in reversed(owned):
                    await client.files.delete(path)
                    assert not await client.files.exists(path)
    asyncio.run(run())
