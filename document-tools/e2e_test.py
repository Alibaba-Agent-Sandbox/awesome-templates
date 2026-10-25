#!/usr/bin/env python3
"""Actual HTTP file upload/conversion/download with independent text and DOCX XML checks."""
import base64
import hashlib
import io
import os
import secrets
import sys
import uuid
import zipfile
from xml.etree import ElementTree

import httpx
from pypdf import PdfReader

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
    token = os.environ.get("E2E_SERVER_TOKEN") or os.environ.get("ABX_SERVER_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    root = (os.environ.get("E2E_WORKSPACE") or os.environ.get("E2E_BASE_DIR") or "/home/user/app").rstrip("/")
    owned = []
    with httpx.Client(base_url=os.environ.get("E2E_BASE_URL", "http://127.0.0.1:9000"), headers={**(headers), **_GATEWAY_HEADERS, **_APPLICATION_HEADERS}, timeout=90) as client:
        def call(name, **arguments):
            response = client.post("/commands/" + name, json=arguments)
            response.raise_for_status()
            return response.json()["result"]

        def download(path):
            response = client.get("/files/download-stream", params={"path": path})
            response.raise_for_status()
            return base64.b64decode(response.json()["content_base64"], validate=True)

        try:
            check(client.get("/health").status_code == 200, "server health")
            response = client.get("/commands")
            names = {item["name"] for item in response.json().get("commands", [])}
            check(response.status_code == 200 and {"document_version", "document_setup_check", "convert", "document_smoke", "office_version", "document_extended_smoke"} <= names,
                  "typed document commands registered")
            check(client.post("/commands/convert", json={}).status_code == 400, "required path arguments enforced")
            check(client.post("/commands/convert", json={"input_path": "in.md", "output_name": "out.docx", "command_timeout": "oops"}).status_code == 400,
                  "operation timeout type enforced")
            for path in ("../secret.md", "https://example.com/in.md"):
                response = client.post("/commands/convert", json={"input_path": path, "output_name": "out.docx"})
                check(response.status_code == 500 and response.json().get("type") == "ValueError", "outside-workspace/network input rejected")
            available = call("document_setup_check")["available"] is True
            if not available:
                if os.environ.get("E2E_REQUIRE_DOCUMENT") == "1":
                    check(False, "required pinned Pandoc is installed")
                print("[SKIP] pinned Pandoc unavailable; HTTP validation does not prove document/image/cloud acceptance", flush=True)
                return 0
            check(call("document_version") == "pandoc 3.1.11.1", "actual pinned Pandoc version")
            check(call("document_smoke") == "Pandoc Markdown DOCX/TXT artifacts OK", "actual native DOCX/TXT self-test and cleanup")
            check(call("office_version") == "LibreOffice 4:25.2.3-2+deb13u8", "exact native headless Writer package and binary")
            check(call("document_extended_smoke") == "Pandoc HTML/PPTX and LibreOffice PDF artifacts OK", "native HTML, slides, PDF and owned cleanup")
            name = "document-controller-" + uuid.uuid4().hex
            nonce = secrets.token_hex(12)
            source = f"# Independent {nonce}\n\nOriginal **strong content** 世界.\n\n- Alpha\n- Beta\n".encode()
            input_path = root + "/" + name + ".md"
            response = client.post("/files/upload-stream", json={"path": input_path, "content_base64": base64.b64encode(source).decode()})
            response.raise_for_status()
            owned.append(input_path)
            check(download(input_path) == source, "out-of-band unique Markdown upload verified")
            for output_format in ("docx", "txt", "pptx", "pdf"):
                filename = name + "." + output_format
                result = call("convert", input_path=name + ".md", output_name=filename, output_format=output_format)
                path = root + "/" + filename
                owned.append(path)
                check(result["output_path"] == path and result["output_format"] == output_format, "result stays inside owned workspace")
                data = download(path)
                check(len(data) == result["bytes"] and hashlib.sha256(data).hexdigest() == result["sha256"], "independent full artifact bytes and SHA256")
                if output_format == "docx":
                    with zipfile.ZipFile(io.BytesIO(data)) as archive:
                        tree = ElementTree.fromstring(archive.read("word/document.xml"))
                        text = "".join(tree.itertext())
                        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                        check(tree.find(".//w:b", ns) is not None and tree.find(".//w:pStyle[@w:val='Heading1']", ns) is not None,
                              "independent DOCX XML heading and bold structure")
                elif output_format == "pptx":
                    with zipfile.ZipFile(io.BytesIO(data)) as archive:
                        slides = [n for n in archive.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
                        check(bool(slides), "independent native PPTX slide XML exists")
                        text = " ".join("".join(ElementTree.fromstring(archive.read(n)).itertext()) for n in slides)
                elif output_format == "pdf":
                    reader = PdfReader(io.BytesIO(data))
                    check(len(reader.pages) >= 1, "independent PDF parser reads native Writer pages")
                    text = "\n".join(page.extract_text() for page in reader.pages)
                else:
                    text = data.decode("utf-8")
                check(all(marker in text for marker in (nonce, "strong content", "世界", "Alpha", "Beta")), "independent document content and fresh nonce preserved")
            html_name = name + ".html"
            html_path = root + "/" + html_name
            html = f"<h1>HTML {nonce}</h1><h2>First slide</h2><p><strong>HTML strong content</strong> 世界.</p><h2>Second slide</h2><ul><li>Alpha</li><li>Beta</li></ul>".encode()
            response = client.post("/files/upload-stream", json={"path": html_path, "content_base64": base64.b64encode(html).decode()})
            response.raise_for_status()
            owned.append(html_path)
            result = call("convert", input_path=html_name, output_name=name + "-html.docx", input_format="html", output_format="docx")
            html_output = root + "/" + name + "-html.docx"
            owned.append(html_output)
            data = download(html_output)
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                text = "".join(ElementTree.fromstring(archive.read("word/document.xml")).itertext())
            check(nonce in text and "HTML strong content" in text and hashlib.sha256(data).hexdigest() == result["sha256"], "independent HTML DOCX content and complete bytes")
            check(download(html_path) == html, "original HTML remains byte-identical")
            check(download(input_path) == source, "original input remains byte-identical")
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
