"""Actual CLI/SDK array transport and independently parsed media artifacts.

Borrows the supplied fresh sandbox and removes only fresh nonce-named files.
The caller owns cloud sandbox/template cleanup and image provenance.
"""
from __future__ import annotations

import asyncio
import hashlib
import io
import json
import secrets
import subprocess
import uuid
import wave


async def verify(sandbox, cli: str) -> dict:
    prefix = 'media-argv-' + uuid.uuid4().hex
    source_name = prefix + ' input.wav'
    compressed, decoded = prefix + '.flac', prefix + '-decoded.wav'
    root = '/home/user/app/'
    paths = [root + name for name in [source_name, compressed, decoded]]
    for path in paths:
        if await sandbox.files.exists(path):
            raise AssertionError('fresh media argv namespace already exists')
    owned = []
    report = {'passed': False, 'verification_type': 'image-backed-cli-sdk-native-json-array'}
    pcm = secrets.token_bytes(32000)
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(pcm)
    server = sandbox.server_at(9000)
    try:
        metadata = {item.name: item for item in await server.commands.list()}
        if metadata['transcode_args'].args[0].type != 'string_array':
            raise AssertionError('actual server lacks native string-array metadata')
        report['native_array_metadata'] = True
        owned.append(paths[0])
        await sandbox.files.write(paths[0], buffer.getvalue())
        owned.append(paths[1])
        result = await asyncio.to_thread(
            subprocess.run,
            [cli, '--json', 'run', sandbox.id, 'transcode_args', '--json-args', json.dumps({
                'args': ['-i', source_name, '-vn', '-c:a', 'flac', '-ac', '1', '-ar', '16000', compressed],
                'max_seconds': 1,
            })],
            capture_output=True, text=True, timeout=150, check=False,
        )
        if result.returncode:
            raise AssertionError('actual native CLI argv conversion failed')
        envelope = json.loads(result.stdout)
        native = envelope.get('result', envelope.get('data', {}).get('result'))
        if not isinstance(native, dict) or native.get('exit_code') != 0:
            raise AssertionError('native CLI did not return actual FFmpeg success')
        data = await sandbox.files.read_bytes(paths[1], max_bytes=64 * 1024**2)
        if not data.startswith(b'fLaC') or hashlib.sha256(data).hexdigest() != native['sha256']:
            raise AssertionError('independently read native CLI FLAC bytes differ')
        report['cli_native_argv'] = True
        owned.append(paths[2])
        result = await server.commands.run('transcode_args', args=[
            '-i', compressed, '-vn', '-c:a', 'pcm_s16le', '-ac', '1', '-ar', '16000', decoded,
        ], max_seconds=1, timeout=150)
        if result['exit_code'] != 0 or not isinstance(result['stdout'], str) or not isinstance(result['stderr'], str):
            raise AssertionError('actual SDK argv conversion did not return native process results')
        data = await sandbox.files.read_bytes(paths[2], max_bytes=64 * 1024**2)
        if hashlib.sha256(data).hexdigest() != result['sha256'] or len(data) != result['bytes']:
            raise AssertionError('independently read SDK artifact bytes differ')
        with wave.open(io.BytesIO(data), 'rb') as audio:
            if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate(), audio.getnframes()) != (1, 2, 16000, 16000) or audio.readframes(16000) != pcm:
                raise AssertionError('independent WAV parser found altered random PCM')
        if await sandbox.files.read_bytes(paths[0]) != buffer.getvalue():
            raise AssertionError('original spaced-name upload was changed')
        report.update(sdk_native_argv=True, pcm_samples_verified=16000, original_upload_unchanged=True, passed=True)
    finally:
        await server.aclose()
        cleanup = True
        for path in reversed(owned):
            try:
                if await sandbox.files.exists(path):
                    await sandbox.files.remove(path)
                cleanup = cleanup and not await sandbox.files.exists(path)
            except Exception:
                cleanup = False
        report['owned_files_absent'] = cleanup
        if not cleanup:
            raise RuntimeError('owned argv artifact cleanup not confirmed')
    return report
