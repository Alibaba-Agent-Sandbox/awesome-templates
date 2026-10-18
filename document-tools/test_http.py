"""Real authenticated typed SDK upload/convert/download and independently parsed DOCX."""
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
import zipfile
from xml.etree import ElementTree

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
    env.update(WORKSPACE=str(tmp_path), ABX_SERVER_BASE_DIR=str(tmp_path), ABX_SERVER_PORT=str(port), ABX_SERVER_TOKEN=token, ABX_PTY_PORT="0")
    process = subprocess.Popen([sys.executable, str(Path(__file__).with_name("commands.py"))], env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    try:
        with httpx.Client(headers={"Authorization": "Bearer " + token}) as client:
            for _ in range(100):
                if process.poll() is not None:
                    pytest.fail("actual document server exited before readiness")
                try:
                    if client.get(url + "/health", timeout=.5).status_code == 200:
                        break
                except httpx.TransportError:
                    pass
                time.sleep(.05)
            else:
                pytest.fail("actual document server did not become healthy")
        yield url, token, tmp_path
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        assert not list(tmp_path.iterdir()), "SDK cleanup must remove all owned input/output"


def test_authenticated_sdk_docx_and_text_artifacts(server):
    url, token, root = server
    assert httpx.get(url + "/commands").status_code == 401
    nonce = secrets.token_hex(12)
    original = f"# Fresh {nonce}\n\nOriginal **strong content** 世界.\n".encode()

    async def run():
        owned = []
        async with ServerClient(url, token=token, timeout=90) as client:
            try:
                assert await client.health()
                assert (await client.commands.run("document_setup_check"))["available"] is True
                with pytest.raises(CommandArgumentError):
                    await client.commands.run("convert")
                with pytest.raises(CommandExecutionError):
                    await client.commands.run("convert", input_path="../secret.md", output_name="bad.docx")
                path = str(root / "source.md")
                await client.files.upload(path, original)
                owned.append(path)
                for output_format in ("docx", "txt"):
                    output_name = "output." + output_format
                    result = await client.commands.run("convert", input_path="source.md", output_name=output_name, output_format=output_format)
                    expected = str(root / output_name)
                    owned.append(expected)
                    assert result["output_path"] == expected
                    data = await client.files.download(expected)
                    assert result["bytes"] == len(data) and result["sha256"] == hashlib.sha256(data).hexdigest()
                    if output_format == "docx":
                        with zipfile.ZipFile(io.BytesIO(data)) as archive:
                            tree = ElementTree.fromstring(archive.read("word/document.xml"))
                            text = "".join(tree.itertext())
                            assert tree.find(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}b") is not None
                    else:
                        text = data.decode()
                    assert nonce in text and "strong content" in text and "世界" in text
                assert await client.files.download(path) == original
            finally:
                for path in reversed(owned):
                    await client.files.delete(path)
                    assert not await client.files.exists(path)
    asyncio.run(run())
