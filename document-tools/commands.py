"""Bounded text document conversion using pinned Pandoc and headless LibreOffice."""
from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import zipfile
from xml.etree import ElementTree

from agent_sandbox.server import command, start

VERSION = "3.1.11.1"
OFFICE_DEBIAN_VERSION = "4:25.2.3-2+deb13u8"
MAX_FILE = 1024 * 1024
MAX_DIAGNOSTICS = 1024 * 1024
_LOCK = threading.Lock()
_LIMIT_EXEC = ("import os,resource,sys;resource.setrlimit(resource.RLIMIT_CORE,(0,0));"
               "resource.setrlimit(resource.RLIMIT_STACK,(8388608,8388608));"
               "resource.setrlimit(resource.RLIMIT_AS,(1073741824,1073741824));"
               "resource.setrlimit(resource.RLIMIT_CPU,(30,31));"
               "resource.setrlimit(resource.RLIMIT_FSIZE,(8388608,8388608));"
               "os.execve(sys.argv[1],sys.argv[1:],os.environ)")


def _process(argv: list[str], *, cwd: str, timeout: float, owned_env: dict | None = None) -> bytes:
    """Drain bounded output and kill the owned group before reaping its leader."""
    env = {key: os.environ[key] for key in ("HOME", "PATH", "LD_LIBRARY_PATH") if key in os.environ}
    env.update(LANG="C.UTF-8", LC_ALL="C.UTF-8", OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2", MALLOC_ARENA_MAX="2")
    env["pandoc_datadir"] = os.environ.get("DOCUMENT_PANDOC_DATA_DIR", "/usr/share/pandoc")
    if owned_env:
        env.update(owned_env)
    process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    parts: list[list[bytes]] = [[], []]
    overflow = threading.Event()

    def drain(stream, output):
        size = 0
        try:
            while chunk := stream.read(65536):
                if size + len(chunk) <= MAX_DIAGNOSTICS:
                    output.append(chunk)
                    size += len(chunk)
                else:
                    overflow.set()
        finally:
            stream.close()

    readers = [threading.Thread(target=drain, args=(stream, output), daemon=True)
               for stream, output in zip((process.stdout, process.stderr), parts)]
    for reader in readers:
        reader.start()
    deadline = time.monotonic() + timeout
    timed_out = False
    try:
        while os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None:
            if overflow.is_set():
                break
            if time.monotonic() >= deadline:
                timed_out = True
                break
            time.sleep(.01)
    finally:
        # WNOWAIT anchors the group identity even if the leader already exited.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            raise RuntimeError("owned document process cleanup exceeded its deadline") from None
        for reader in readers:
            reader.join(timeout=2)
    if timed_out:
        raise RuntimeError("document operation exceeded its wall-clock deadline")
    if overflow.is_set():
        raise RuntimeError("document diagnostics exceeded the byte limit")
    if process.returncode:
        raise RuntimeError(f"document tool failed (exit {process.returncode}); native diagnostics omitted")
    return b"".join(parts[0])


def _timeout(command_timeout: int) -> float:
    if type(command_timeout) is not int or not 1 <= command_timeout <= 60:
        raise ValueError("command_timeout must be an integer from 1 to 60 seconds")
    return time.monotonic() + command_timeout


def _root() -> tuple[Path, int]:
    try:
        root = Path(os.environ.get("WORKSPACE") or "/home/user/app").resolve(strict=True)
        descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        if os.fstat(descriptor).st_uid != os.geteuid():
            os.close(descriptor)
            raise ValueError("WORKSPACE must belong to the runtime user")
        return root, descriptor
    except OSError:
        raise ValueError("WORKSPACE must be an existing owned directory") from None


def _snapshot(descriptor: int, input_path: str, destination: Path) -> None:
    if (not isinstance(input_path, str) or not input_path or len(input_path) > 1024
            or "\x00" in input_path or ":" in input_path):
        raise ValueError("input_path must be a relative workspace document file")
    path = Path(input_path)
    if path.is_absolute() or not path.parts or ".." in path.parts or len(path.parts) > 16:
        raise ValueError("input_path must stay inside WORKSPACE without symlinks")
    parent = os.dup(descriptor)
    source = None
    try:
        for part in path.parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            os.close(parent)
            parent = child
        source = os.open(path.parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        details = os.fstat(source)
        if not stat.S_ISREG(details.st_mode) or not 0 < details.st_size <= MAX_FILE:
            raise ValueError("input must be a regular file of at most 1 MiB")
        with os.fdopen(source, "rb") as stream:
            source = None
            data = stream.read(MAX_FILE + 1)
        if not 0 < len(data) <= MAX_FILE:
            raise ValueError("input exceeds the byte limit")
        destination.write_bytes(data)
    except OSError:
        raise ValueError("input_path must identify a readable workspace file without symlinks") from None
    finally:
        if source is not None:
            os.close(source)
        os.close(parent)


def _pandoc(arguments: list[str], *, cwd: Path, deadline: float) -> bytes:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise RuntimeError("document operation exceeded its wall-clock deadline")
    binary = Path(os.environ.get("DOCUMENT_PANDOC_BINARY", "/usr/bin/pandoc"))
    if not binary.is_absolute() or not binary.is_file() or not os.access(binary, os.X_OK):
        raise RuntimeError("the pinned Pandoc executable is unavailable")
    return _process([sys.executable, "-I", "-c", _LIMIT_EXEC, str(binary),
                     "--data-dir", str(cwd / "empty-data"), *arguments,
                     "+RTS", "-N2", "-M256M", "-RTS"], cwd=str(cwd), timeout=remaining)


def _guard_html(text: str) -> None:
    """Reject resource-bearing HTML before even the sandboxed native reader."""
    class TextHTML(HTMLParser):
        allowed = set("html head title body h1 h2 h3 h4 h5 h6 p strong em b i ul ol li blockquote code pre hr br a table thead tbody tr th td span div s del sub sup dl dt dd".split())
        void = {"hr", "br"}
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.stack = []
            self.nodes = 0
        def handle_starttag(self, tag, attrs):
            self.nodes += 1
            if tag not in self.allowed or self.nodes > 20000:
                raise ValueError("HTML must contain only bounded text markup; resources/scripts are unsupported")
            for key, value in attrs:
                if key not in {"lang", "title", "id", "class", "href", "colspan", "rowspan", "start"}:
                    raise ValueError("HTML resource/style/event attributes are unsupported")
                if key == "href" and (not value or not value.startswith(("https://", "http://", "mailto:", "#"))):
                    raise ValueError("HTML links must be web, mail or fragment references")
                if key in {"colspan", "rowspan", "start"} and (not value or not value.isdecimal() or not 1 <= int(value) <= 100):
                    raise ValueError("HTML numeric attributes must be integers1..100")
            if tag not in self.void:
                self.stack.append(tag)
                if len(self.stack) > 100:
                    raise ValueError("HTML nesting exceeds100")
        def handle_startendtag(self, tag, attrs):
            self.handle_starttag(tag, attrs)
            if tag not in self.void:
                self.stack.pop()
        def handle_endtag(self, tag):
            if tag in self.void:
                return
            if not self.stack or self.stack.pop() != tag:
                raise ValueError("HTML text markup must use balanced explicit tags")
        def handle_decl(self, decl):
            if decl.strip().lower() != "doctype html":
                raise ValueError("only a plain HTML doctype is accepted")
    parser = TextHTML()
    parser.feed(text)
    parser.close()
    if parser.stack:
        raise ValueError("HTML text markup must use balanced explicit tags")


def _office(arguments: list[str], *, cwd: Path, deadline: float) -> bytes:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise RuntimeError("document operation exceeded its wall-clock deadline")
    binary = Path("/usr/lib/libreoffice/program/soffice")
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise RuntimeError("the pinned headless LibreOffice executable is unavailable")
    home, temporary, profile = cwd / "office-home", cwd / "office-tmp", cwd / "office-profile"
    for path in (home, temporary, profile):
        path.mkdir(mode=0o700, exist_ok=True)
    limit = _LIMIT_EXEC.replace("1073741824", "2147483648").replace("(30,31)", "(60,61)")
    return _process([sys.executable, "-I", "-c", limit, str(binary),
                     "-env:UserInstallation=" + profile.as_uri(), "--headless", "--nologo",
                     "--nodefault", "--nofirststartwizard", *arguments], cwd=str(cwd), timeout=remaining,
                    owned_env={"HOME": str(home), "TMPDIR": str(temporary),
                               "XDG_CONFIG_HOME": str(home / "config"), "XDG_CACHE_HOME": str(home / "cache")})


def _assert_office(job: Path, deadline: float) -> str:
    package = _process(["/usr/bin/dpkg-query", "-W", "-f=${Version}", "libreoffice-writer-nogui"],
                       cwd=str(job), timeout=max(.1, deadline - time.monotonic())).decode().strip()
    if package != OFFICE_DEBIAN_VERSION:
        raise RuntimeError("installed LibreOffice does not match the pinned Debian package")
    actual = _office(["--version"], cwd=job, deadline=deadline).decode("utf-8", "replace")
    if not actual.startswith("LibreOffice 25.2.3."):
        raise RuntimeError("actual LibreOffice executable differs from the pinned release")
    return "LibreOffice " + OFFICE_DEBIAN_VERSION


def _validated_ast(raw: bytes) -> dict:
    """Keep the DOCX writer away from images, includes, raw content and unsafe links."""
    try:
        document = json.loads(raw)
        if not isinstance(document, dict) or not isinstance(document["blocks"], list) or "pandoc-api-version" not in document:
            raise ValueError
        stack = [(document["blocks"], 0)]
        nodes = 0
        while stack:
            value, depth = stack.pop()
            nodes += 1
            if nodes > 50000 or depth > 100:
                raise ValueError
            if isinstance(value, dict):
                if value.get("t") in {"Image", "RawBlock", "RawInline"}:
                    raise ValueError
                if value.get("t") == "Link":
                    target = value["c"][-1][0]
                    if not isinstance(target, str) or not target.startswith(("https://", "http://", "mailto:", "#")):
                        raise ValueError
                stack.extend((child, depth + 1) for child in value.values())
            elif isinstance(value, list):
                stack.extend((child, depth + 1) for child in value)
        document["meta"] = {}
        return document
    except (KeyError, IndexError, TypeError, ValueError):
        raise ValueError("document must contain bounded text markup without images, raw nodes or non-web links") from None


def _output_bytes(path: Path, output_format: str) -> bytes:
    data = path.read_bytes()
    if not 0 < len(data) <= 8 * 1024 * 1024:
        raise RuntimeError("document output exceeded the byte limit")
    if output_format == "txt":
        data.decode("utf-8")
    elif output_format == "pdf":
        if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-1024:]:
            raise RuntimeError("LibreOffice did not produce a bounded PDF")
    else:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                entries = archive.infolist()
                if len(entries) > 256 or sum(item.file_size for item in entries) > 16 * 1024 * 1024:
                    raise ValueError
                if "[Content_Types].xml" not in archive.namelist():
                    raise ValueError
                for item in entries:
                    if item.filename.startswith("/") or ".." in Path(item.filename).parts:
                        raise ValueError
                if output_format == "pptx":
                    ElementTree.fromstring(archive.read("ppt/presentation.xml"))
                    slides = [name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide[0-9]+\.xml", name)]
                    if not 1 <= len(slides) <= 100:
                        raise ValueError
                    for name in slides:
                        ElementTree.fromstring(archive.read(name))
                else:
                    xml = archive.read("word/document.xml")
                    ElementTree.fromstring(xml)
        except (ValueError, KeyError, zipfile.BadZipFile, ElementTree.ParseError):
            raise RuntimeError("Pandoc did not produce a valid bounded DOCX document") from None
    return data


def _assert_version(deadline: float) -> str:
    output = _pandoc(["--version"], cwd=Path("/tmp"), deadline=deadline).decode("utf-8", "replace")
    if not output.startswith("pandoc " + VERSION + "\n"):
        raise RuntimeError("installed Pandoc does not match the pinned version")
    return "pandoc " + VERSION


@command("document_version", description="Inspect the fixed official Pandoc version without processing documents.")
def document_version() -> str:
    return _assert_version(_timeout(10))


@command("document_setup_check", description="Report whether the pinned Pandoc program is installed.")
def document_setup_check() -> dict:
    try:
        return {"available": True, "version": document_version()}
    except RuntimeError:
        return {"available": False, "pinned_version": VERSION}


@command("convert", description="Convert bounded Markdown/HTML to DOCX, TXT, PPTX or native headless Writer PDF.")
def convert(input_path: str, output_name: str, output_format: str = "docx", command_timeout: int = 30, input_format: str = "markdown") -> dict:
    deadline = _timeout(command_timeout)
    if input_format not in {"markdown", "html"}:
        raise ValueError("input_format must be markdown or html")
    if output_format not in {"docx", "txt", "pdf", "pptx"}:
        raise ValueError("output_format must be docx, txt, pdf or pptx")
    if not isinstance(output_name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,119}\." + output_format, output_name):
        raise ValueError("output_name must be a plain filename with the output_format extension")
    if not _LOCK.acquire(blocking=False):
        raise RuntimeError("another document operation is active")
    try:
        root, descriptor = _root()
        try:
            with tempfile.TemporaryDirectory(prefix=".document-", dir=root) as directory:
                job = Path(directory)
                source, validated, output = job / "input.md", job / "validated.json", job / ("output." + output_format)
                _snapshot(descriptor, input_path, source)
                try:
                    text = source.read_bytes().decode("utf-8-sig")
                    if "\x00" in text or not text.strip():
                        raise ValueError
                except (UnicodeError, ValueError):
                    raise ValueError("input must be nonempty UTF-8 Markdown without NUL bytes") from None
                if input_format == "html":
                    _guard_html(text)
                source.write_text(text, encoding="utf-8")
                _assert_version(deadline)
                raw = _pandoc(["--sandbox", "--fail-if-warnings", "--from=" + ("html" if input_format == "html" else "gfm-raw_html"), "--to=json", str(source)], cwd=job, deadline=deadline)
                document = _validated_ast(raw)
                if not document["blocks"]:
                    raise ValueError("input must contain visible document content")
                validated.write_text(json.dumps(document), encoding="utf-8")
                # Debian's non-embedded-data binary cannot write DOCX in --sandbox.
                # Only the validated, metadata-free, image/raw-free AST reaches
                # that fixed writer. PDF uses only this generated, validated DOCX.
                writer = {"txt": "plain", "docx": "docx", "pptx": "pptx", "pdf": "docx"}[output_format]
                intermediate = job / "render.docx" if output_format == "pdf" else output
                arguments = ["--from=json", "--to=" + writer,
                             "--fail-if-warnings", "--output", str(intermediate), str(validated)]
                if output_format == "pptx":
                    arguments.insert(0, "--slide-level=2")
                if output_format == "txt":
                    arguments.insert(0, "--sandbox")
                _pandoc(arguments, cwd=job, deadline=deadline)
                if output_format == "pdf":
                    _output_bytes(intermediate, "docx")
                    _assert_office(job, deadline)
                    _office(["--convert-to", "pdf:writer_pdf_Export", "--outdir", str(job), str(intermediate)], cwd=job, deadline=deadline)
                    produced = job / "render.pdf"
                    if not produced.is_file() or produced.is_symlink():
                        raise RuntimeError("native LibreOffice did not create its expected PDF")
                    produced.rename(output)
                data = _output_bytes(output, output_format)
                try:
                    os.link(output, output_name, dst_dir_fd=descriptor, follow_symlinks=False)
                except FileExistsError:
                    raise ValueError("output_name already exists; choose a new artifact name") from None
                return {"output_path": str(root / output_name), "output_format": output_format,
                        "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        finally:
            os.close(descriptor)
    finally:
        _LOCK.release()


@command("office_version", description="Verify the exact Debian headless LibreOffice Writer package and actual binary.")
def office_version() -> str:
    with tempfile.TemporaryDirectory(prefix="abx-office-version-") as directory:
        return _assert_office(Path(directory), _timeout(15))


@command("document_smoke", description="Convert owned original Markdown to DOCX/TXT, inspect document XML/text, and clean up.")
def document_smoke() -> str:
    document_version()
    root, descriptor = _root()
    name = "document-smoke-" + uuid.uuid4().hex
    source = root / (name + ".md")
    owned = []
    try:
        with source.open("x", encoding="utf-8") as file:
            owned.append(source.name)
            file.write("# Sandbox document\n\nOriginal **bounded conversion** text.\n\n- First item\n- Second item\n")
        for output_format in ("docx", "txt"):
            output_name = name + "." + output_format
            convert(source.name, output_name, output_format=output_format)
            owned.append(output_name)
            data = (root / output_name).read_bytes()
            if output_format == "docx":
                with zipfile.ZipFile(io.BytesIO(data)) as archive:
                    text = "".join(ElementTree.fromstring(archive.read("word/document.xml")).itertext())
            else:
                text = data.decode("utf-8")
            if not all(marker in text for marker in ("Sandbox document", "bounded conversion", "First item", "Second item")):
                raise RuntimeError("document content self-test failed")
        return "Pandoc Markdown DOCX/TXT artifacts OK"
    finally:
        cleanup_failed = False
        try:
            for filename in reversed(owned):
                try:
                    os.unlink(filename, dir_fd=descriptor)
                except FileNotFoundError:
                    pass
                except OSError:
                    cleanup_failed = True
        finally:
            os.close(descriptor)
        if cleanup_failed:
            raise RuntimeError("owned document smoke artifact cleanup failed")


@command("document_extended_smoke", description="Generate owned HTML/DOCX, native PPTX and headless Writer PDF, validate containers and clean up.")
def document_extended_smoke() -> str:
    root, descriptor = _root()
    name = "document-extended-" + uuid.uuid4().hex
    marker = "Extended document " + name
    owned = []
    try:
        inputs = {name + ".html": "<h1>" + marker + "</h1><p><strong>Native HTML</strong> 世界.</p>",
                  name + ".md": "# " + marker + "\n\n## Slide One\n\nFirst marker\n\n## Slide Two\n\nSecond marker\n"}
        for filename, text in inputs.items():
            with (root / filename).open("x", encoding="utf-8") as stream:
                owned.append(filename)
                stream.write(text)
        for input_format, output_format in [("html", "docx"), ("markdown", "pptx"), ("markdown", "pdf")]:
            filename = name + "-" + input_format + "." + output_format
            convert(name + (".html" if input_format == "html" else ".md"), filename,
                    output_format=output_format, input_format=input_format, command_timeout=60)
            owned.append(filename)
            data = _output_bytes(root / filename, output_format)
            if output_format in {"docx", "pptx"}:
                with zipfile.ZipFile(io.BytesIO(data)) as archive:
                    paths = (["word/document.xml"] if output_format == "docx" else
                             [n for n in archive.namelist() if re.fullmatch(r"ppt/slides/slide[0-9]+\.xml", n)])
                    text = " ".join("".join(ElementTree.fromstring(archive.read(n)).itertext()) for n in paths)
                if marker not in text:
                    raise RuntimeError("native document text self-test failed")
        return "Pandoc HTML/PPTX and LibreOffice PDF artifacts OK"
    finally:
        failed = False
        for filename in reversed(owned):
            try:
                os.unlink(filename, dir_fd=descriptor)
            except FileNotFoundError:
                pass
            except OSError:
                failed = True
        os.close(descriptor)
        if failed:
            raise RuntimeError("owned extended document cleanup failed")


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
