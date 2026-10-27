"""Private worker: real X11 desktop and selected pinned OSWorld handlers.

The named-command parent owns this Linux process group. No HTTP server listens;
Flask's internal test client calls the upstream observation handlers directly.
"""
from __future__ import annotations

import ast
import base64
import contextlib
import hashlib
import importlib.util
import io
import json
import logging
import os
from pathlib import Path
import resource
import secrets
import shutil
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
from urllib.parse import unquote, urlsplit

SOURCE = Path(__file__).with_name("upstream")
STATE = Path(sys.argv[1]) if __name__ == "__main__" else None


class InitializationError(RuntimeError):
    def __init__(self, stage: str, cause: str):
        super().__init__("desktop initialization failed")
        self.stage = stage
        self.cause = cause


def load_functions(filename: str, names: tuple[str, ...]) -> dict:
    """Compile only named, unchanged upstream definitions, not dependency imports.

    This avoids the upstream metric registry's PDF/Office/cloud dependencies.
    Input is the packaged, pinned source, never a submitted task or script.
    """
    source = ast.parse((SOURCE / filename).read_text())
    functions = [node for node in source.body if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in functions} != set(names):
        raise RuntimeError("pinned upstream functions are missing")
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *functions], type_ignores=[])
    namespace = {"logger": logging.getLogger("osworld.slice")}
    exec(compile(ast.fix_missing_locations(module), filename, "exec"), namespace)
    return {name: namespace[name] for name in names}


def task_configuration(path: str) -> dict:
    target = Path(path).resolve(strict=True)
    root = Path(os.environ["WORKSPACE"]).resolve(strict=True)
    if not target.is_relative_to(root) or not target.is_file() or target.stat().st_size > 65536:
        raise ValueError("task must be a file of at most 64 KiB inside WORKSPACE")
    task = json.loads(target.read_text())
    if not isinstance(task, dict):
        raise ValueError("task must be an object")
    allowed = {"id", "instruction", "snapshot", "config", "evaluator", "related_apps", "trajectory", "source", "possibility_of_env_change", "proxy", "fixed_ip"}
    if set(task) - allowed or task.get("proxy") or task.get("fixed_ip"):
        raise ValueError("unsupported task fields or proxy/network identity requirements")
    if task.get("snapshot", "chrome") not in ("chrome", "browser"):
        raise ValueError("only the browser snapshot slice is supported")
    if set(task.get("related_apps", ["chrome"])) - {"chrome", "browser"}:
        raise ValueError("only browser tasks are supported")
    config = task.get("config", [])
    if not isinstance(config, list) or len(config) > 8:
        raise ValueError("config must contain at most 8 supported setup steps")
    for step in config:
        if not isinstance(step, dict) or set(step) != {"type", "parameters"} or not isinstance(step["parameters"], dict):
            raise ValueError("invalid setup step")
        params = step["parameters"]
        if step["type"] == "chrome_open_tabs":
            if set(params) != {"urls_to_open"} or not isinstance(params["urls_to_open"], list) or not 1 <= len(params["urls_to_open"]) <= 4:
                raise ValueError("chrome_open_tabs requires 1..4 URLs")
            for url in params["urls_to_open"]:
                validate_url(url)
        elif step["type"] == "sleep":
            if set(params) != {"seconds"} or type(params["seconds"]) not in (int, float) or not 0 <= params["seconds"] <= 5:
                raise ValueError("sleep must be 0..5 seconds")
        else:
            raise ValueError("unsupported setup type; launch, shell, VM and Office setup are disabled")
    evaluator = task.get("evaluator")
    if not isinstance(evaluator, dict) or set(evaluator) != {"func", "result", "expected"}:
        raise ValueError("evaluator requires exactly func, result and expected; postconfig/options are unsupported")
    if evaluator["func"] not in ("check_include_exclude", "exact_match") or evaluator["result"] != {"type": "accessibility_tree"}:
        raise ValueError("unsupported evaluator or getter")
    expected = evaluator["expected"]
    if not isinstance(expected, dict) or set(expected) != {"type", "rules"} or expected["type"] != "rule" or not isinstance(expected["rules"], dict):
        raise ValueError("expected must be an OSWorld rule getter")
    rules = expected["rules"]
    if evaluator["func"] == "exact_match":
        if set(rules) != {"expected"} or not isinstance(rules["expected"], str) or not rules["expected"]:
            raise ValueError("exact_match requires a nonempty expected string")
    else:
        if set(rules) - {"include", "exclude"} or not rules.get("include"):
            raise ValueError("check_include_exclude requires a nonempty include list")
        for key, values in rules.items():
            if not isinstance(values, list) or len(values) > 32 or any(not isinstance(v, str) or not v or len(v) > 4096 for v in values):
                raise ValueError("include/exclude rules must be bounded lists of nonempty strings")
    return task


def validate_url(url: str) -> str:
    if not isinstance(url, str) or len(url) > 2048:
        raise ValueError("URL must be a string of at most 2048 characters")
    parsed = urlsplit(url)
    if parsed.username or parsed.password:
        raise ValueError("embedded URL credentials are disabled")
    if parsed.scheme in ("http", "https") and parsed.hostname:
        return url
    if parsed.scheme == "file" and not parsed.netloc and not parsed.query and not parsed.fragment:
        target = Path(unquote(parsed.path)).resolve(strict=True)
        if target.is_file() and target.is_relative_to(Path(os.environ["WORKSPACE"]).resolve(strict=True)):
            return url
    raise ValueError("only HTTP(S) URLs and files inside WORKSPACE are supported")


class Desktop:
    def __init__(self, directory: Path):
        self.directory = directory
        self.children = []
        self.playwright = None
        self.browser = None
        self.accessibility_thread = None
        self.stage = "initialization"
        try:
            self.start()
        except Exception as exc:
            raise InitializationError(self.stage, type(exc).__name__) from None

    def spawn(self, argv, **kwargs):
        process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   stdout=kwargs.pop("stdout", subprocess.DEVNULL), **kwargs)
        self.children.append(process)
        return process

    def start(self):
        self.stage = "x11-display"
        authority = self.directory / "Xauthority"
        # Never remove or adopt another session's X socket/lock.
        for _ in range(100):
            number = 1000 + secrets.randbelow(50000)
            if not Path(f"/tmp/.X{number}-lock").exists() and not Path(f"/tmp/.X11-unix/X{number}").exists():
                break
        else:
            raise RuntimeError("no unused X display was found")
        os.environ["DISPLAY"] = f":{number}"
        os.environ["XAUTHORITY"] = str(authority)
        subprocess.run(["xauth", "-f", str(authority), "add", os.environ["DISPLAY"], ".", secrets.token_hex(16)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        authority.chmod(0o600)
        self.spawn(["Xvfb", os.environ["DISPLAY"], "-screen", "0", "1024x768x24", "-nolisten", "tcp", "-auth", str(authority)])
        for _ in range(100):
            if Path(f"/tmp/.X11-unix/X{number}").exists():
                break
            time.sleep(.05)
        else:
            raise RuntimeError("Xvfb failed to become ready")
        self.stage = "private-dbus"
        bus = self.spawn(["dbus-daemon", "--session", "--nofork", "--print-address=1"], stdout=subprocess.PIPE)
        os.environ["DBUS_SESSION_BUS_ADDRESS"] = bus.stdout.readline().decode().strip()
        bus.stdout.close()
        if not os.environ["DBUS_SESSION_BUS_ADDRESS"].startswith("unix:"):
            raise RuntimeError("private DBus session did not start")
        # Own the accessibility bus explicitly, rather than delegating its
        # lifetime to an inherited desktop session or D-Bus auto-activation.
        accessibility_bus = self.spawn(["dbus-daemon", "--session", "--nofork", "--print-address=1"], stdout=subprocess.PIPE)
        os.environ["AT_SPI_BUS_ADDRESS"] = accessibility_bus.stdout.readline().decode().strip()
        accessibility_bus.stdout.close()
        registry = shutil.which("at-spi2-registryd") or "/usr/libexec/at-spi2-registryd"
        registry_env = os.environ.copy()
        registry_env["DBUS_SESSION_BUS_ADDRESS"] = os.environ["AT_SPI_BUS_ADDRESS"]
        self.spawn([registry], env=registry_env)
        from Xlib import display as xdisplay, Xatom
        connection = xdisplay.Display()
        connection.screen().root.change_property(connection.intern_atom("AT_SPI_BUS"),
                                                  Xatom.STRING, 8, os.environ["AT_SPI_BUS_ADDRESS"].encode())
        connection.sync()
        connection.close()
        self.stage = "window-manager"
        config = self.directory / "openbox.xml"
        config.write_text('<openbox_config xmlns="http://openbox.org/3.4/rc"><applications><application class="*"><decor>no</decor></application></applications></openbox_config>')
        self.spawn(["openbox", "--sm-disable", "--config-file", str(config)])
        connection = xdisplay.Display()
        wm_atom = connection.intern_atom("_NET_SUPPORTING_WM_CHECK")
        for _ in range(100):
            if connection.screen().root.get_full_property(wm_atom, 0) is not None:
                break
            time.sleep(.05)
        else:
            raise RuntimeError("window manager did not become ready")
        connection.close()
        self.stage = "upstream-observations"
        upstream = self.directory / "upstream"
        upstream.mkdir()
        for name in ("main.py", "pyxcursor.py"):
            shutil.copy2(SOURCE / name, upstream / name)
        sys.path.insert(0, str(upstream))
        spec = importlib.util.spec_from_file_location("osworld_desktop_server", upstream / "main.py")
        self.server = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.server)
        self.accessibility_thread = threading.Thread(target=self.server.pyatspi.Registry.start,
                                                       kwargs={"gil": True}, daemon=True)
        self.accessibility_thread.start()
        # Upstream probes LibreOffice before every Linux accessibility request.
        # This browser-only image has no Office. Unknown version is the empty
        # tuple; no executable/version is fabricated. Office tasks are rejected.
        if not shutil.which("libreoffice"):
            self.server._get_libreoffice_version = lambda: ()
        self.client = self.server.app.test_client()
        self.stage = "browser-location"
        from playwright.sync_api import sync_playwright
        self.playwright = sync_playwright().start()
        binary = os.environ.get("OSWORLD_BROWSER") or self.playwright.chromium.executable_path
        if not Path(binary).is_file():
            raise RuntimeError("the pinned browser is missing")
        self.stage = "browser-startup"
        self.browser_process = self.spawn([binary, "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--no-first-run",
                    "--no-default-browser-check", "--password-store=basic", "--force-renderer-accessibility",
                    "--remote-debugging-address=127.0.0.1", "--remote-debugging-port=0", "--kiosk",
                    "--user-data-dir=" + str(self.directory / "browser"), "about:blank"])
        port_file = self.directory / "browser" / "DevToolsActivePort"
        for _ in range(200):
            if port_file.exists():
                break
            time.sleep(.05)
        else:
            raise RuntimeError("browser did not become ready")
        port = int(port_file.read_text().splitlines()[0])
        self.stage = "browser-attachment"
        self.browser = self.playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        self.context = self.browser.contexts[0]
        self.page = self.context.pages[0]
        self.stage = "browser-viewport"
        self.page.wait_for_function("document.visibilityState === 'visible' && innerWidth > 0 && innerHeight > 0",
                                    timeout=10000, polling=50)
        self.geometry()
        self.metrics = load_functions("metrics_general.py", ("check_include_exclude", "exact_match"))
        self.getters = load_functions("getters_misc.py", ("get_rule", "get_accessibility_tree"))

    def geometry(self):
        # Xvfb/screenshot size and the page viewport are different measurements.
        # Read coordinates only; never resize/emulate the page to satisfy a test.
        value = self.page.evaluate("""({screen_width:screen.width,screen_height:screen.height,
            outer_width:outerWidth,outer_height:outerHeight,viewport_width:innerWidth,
            viewport_height:innerHeight,content_x:screenX+(outerWidth-innerWidth)/2,
            content_y:screenY+outerHeight-innerHeight})""")
        names = {"screen_width", "screen_height", "outer_width", "outer_height",
                 "viewport_width", "viewport_height", "content_x", "content_y"}
        if (not isinstance(value, dict) or set(value) != names or
                any(type(v) not in (int, float) or not -65536 <= v <= 65536 for v in value.values()) or
                any(value[k] <= 0 for k in names - {"content_x", "content_y"})):
            raise RuntimeError("invalid browser geometry")
        return value

    def focus_browser(self):
        # Native transient browser/clipboard windows can retain X input focus
        # while document.activeElement still names the page field. Restore only
        # the main window belonging to the exact browser process we launched.
        from Xlib import display as xdisplay, X, Xatom
        connection = xdisplay.Display()
        try:
            clients = connection.screen().root.get_full_property(connection.intern_atom("_NET_CLIENT_LIST"), Xatom.WINDOW)
            if clients is None:
                raise RuntimeError("owned browser window is unavailable")
            for identifier in clients.value:
                window = connection.create_resource_object("window", int(identifier))
                owner = window.get_full_property(connection.intern_atom("_NET_WM_PID"), Xatom.CARDINAL)
                if owner is not None and int(owner.value[0]) == self.browser_process.pid:
                    window.set_input_focus(X.RevertToParent, X.CurrentTime)
                    window.configure(stack_mode=X.Above)
                    connection.sync()
                    return
            raise RuntimeError("owned browser window is unavailable")
        finally:
            connection.close()

    def tree(self):
        response = self.client.get("/accessibility")
        if response.status_code != 200:
            raise RuntimeError("upstream AT-SPI observation failed")
        result = response.get_json()["AT"]
        if len(result.encode()) > 2 * 1024 * 1024:
            raise RuntimeError("accessibility tree exceeds 2 MiB")
        return result

    def screen(self):
        response = self.client.get("/screenshot")
        if response.status_code != 200 or not response.data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise RuntimeError("upstream screenshot observation failed")
        from PIL import Image
        with Image.open(io.BytesIO(response.data)) as image:
            width, height = image.size
        if (width, height) != (1024, 768):
            raise RuntimeError("unexpected desktop dimensions")
        return {"mime": "image/png", "width": width, "height": height,
                "sha256": hashlib.sha256(response.data).hexdigest(),
                "base64": base64.b64encode(response.data).decode()}

    def apply(self, task):
        for step in task.get("config", []):
            params = step["parameters"]
            if step["type"] == "sleep":
                time.sleep(params["seconds"])
            else:
                urls = params["urls_to_open"]
                # Same bounded Playwright tab operation as upstream's setup
                # adapter, without importing its dotenv/proxy/cloud controllers.
                for index, url in enumerate(urls):
                    page = self.page if index == 0 else self.context.new_page()
                    page.goto(url, wait_until="load", timeout=15000)
                self.page.bring_to_front()
                # An earlier observation can retain the previous document's
                # accessible children. Refresh after navigation, retaining the
                # native cache during the upstream's many attribute queries.
                self.server.pyatspi.Registry.getDesktop(0).clearCache()
        return {"applied": len(task.get("config", [])), "supported_slice": "linux-browser",
                "browser_geometry": self.geometry()}

    def evaluate(self, task):
        evaluator = task["evaluator"]
        environment = SimpleNamespace(controller=SimpleNamespace(get_accessibility_tree=self.tree))
        actual = self.getters["get_accessibility_tree"](environment)
        expected = self.getters["get_rule"](environment, evaluator["expected"])
        # Upstream metrics print actual/rules; never forward them to logs/RPC.
        with contextlib.redirect_stdout(io.StringIO()):
            score = self.metrics[evaluator["func"]](actual, expected)
        return {"score": float(score), "metric": evaluator["func"], "getter": "accessibility_tree",
                "upstream_commit": "b138d348256078fa634fc3b73567a7337c793e6b"}

    def dispatch(self, request):
        operation = request["operation"]
        gui = self.server.pyautogui
        if operation == "screenshot":
            return self.screen()
        if operation == "a11y_tree":
            return self.tree()
        if operation == "click":
            gui.click(request["x"], request["y"], button=request["button"])
            time.sleep(.1)
            return "clicked"
        if operation == "type_text":
            self.focus_browser()
            # Paste through the private X11 clipboard and actual keyboard
            # events. Long zero-duration per-key streams lose events in Chrome.
            # Text stays on stdin and never enters argv or a shell command.
            from Xlib import display as xdisplay
            connection = xdisplay.Display()
            clipboard = connection.intern_atom("CLIPBOARD")
            previous = connection.get_selection_owner(clipboard)
            process = subprocess.Popen(["xclip", "-selection", "clipboard", "-in", "-quiet"],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.children.append(process)
            try:
                process.stdin.write(request["text"].encode())
                process.stdin.close()
                deadline = time.monotonic() + 3
                while connection.get_selection_owner(clipboard) == previous:
                    if time.monotonic() >= deadline:
                        raise RuntimeError("private clipboard did not become ready")
                    time.sleep(.02)
                owner = connection.get_selection_owner(clipboard)
                gui.hotkey("ctrl", "v", interval=.05)
                time.sleep(1)
            finally:
                process.terminate()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=1)
                try:
                    if "owner" in locals() and connection.get_selection_owner(clipboard) == owner:
                        raise RuntimeError("owned clipboard selection was not released")
                finally:
                    connection.close()
                    self.children.remove(process)
            return "typed"
        if operation == "hotkey":
            if any(key not in gui.KEYBOARD_KEYS for key in request["keys"]):
                raise ValueError("unsupported PyAutoGUI key name")
            self.focus_browser()
            gui.hotkey(*request["keys"], interval=.05)
            time.sleep(.1)
            return "pressed"
        if operation in ("run_task_config", "evaluate"):
            task = task_configuration(request["task_path"])
            return self.apply(task) if operation == "run_task_config" else self.evaluate(task)
        if operation == "smoke":
            return self.smoke()
        raise ValueError("unsupported desktop operation")

    def smoke(self):
        # Actual file-backed task state, native mouse/keyboard events, fresh
        # observations and upstream evaluator. No marker contributes to score.
        fixture = Path(os.environ["WORKSPACE"]) / (".osworld-smoke-" + secrets.token_hex(8) + ".html")
        try:
            self.stage = "fixture-creation"
            fixture.write_text('<!doctype html><title>OSWorld desktop task</title><label for="entry" style="position:absolute;left:100px;top:100px">Task text</label><input id="entry" aria-label="Task text" style="position:absolute;left:100px;top:180px;width:500px;height:60px;font-size:24px"><button id="apply" style="position:absolute;left:100px;top:300px;width:400px;height:80px" onclick="document.getElementById(\'result\').textContent=\'Completed: \'+document.getElementById(\'entry\').value">Apply task</button><p id="result" role="status" aria-live="polite" style="position:absolute;left:100px;top:450px">Awaiting input</p>')
            task = {"config": [{"type": "chrome_open_tabs", "parameters": {"urls_to_open": [fixture.as_uri()]}}],
                    "evaluator": {"func": "check_include_exclude", "result": {"type": "accessibility_tree"},
                                  "expected": {"type": "rule", "rules": {"include": ["Completed: sandbox-desktop"], "exclude": ["Awaiting input"]}}}}
            self.stage = "task-navigation"
            self.apply(task)
            self.page.wait_for_timeout(700)
            self.stage = "initial-observation"
            before = self.screen()
            if self.evaluate(task)["score"] != 0:
                raise RuntimeError("baseline evaluation must fail before GUI actions")
            if "Task text" not in self.tree():
                raise RuntimeError("real browser accessibility nodes are missing")
            geometry = self.geometry()
            offset = {"x": geometry["content_x"], "y": geometry["content_y"]}
            box = self.page.locator("#entry").bounding_box()
            self.stage = "keyboard-input"
            self.dispatch({"operation": "click", "x": int(offset["x"] + box["x"] + 20), "y": int(offset["y"] + box["y"] + 20), "button": "left"})
            self.page.wait_for_function("document.activeElement.id === 'entry'", timeout=5000, polling=50)
            self.dispatch({"operation": "type_text", "text": "sandbox-desktop"})
            self.page.wait_for_function("document.getElementById('entry').value === 'sandbox-desktop'", timeout=5000, polling=50)
            if self.page.locator("#entry").input_value() != "sandbox-desktop":
                raise RuntimeError("native input state was not observed")
            self.stage = "keyboard-submit"
            self.dispatch({"operation": "hotkey", "keys": ["tab"]})
            self.page.wait_for_function("document.activeElement.id === 'apply'", timeout=5000, polling=50)
            self.dispatch({"operation": "hotkey", "keys": ["enter"]})
            self.stage = "result-observation"
            self.page.wait_for_function("document.getElementById('result').textContent === 'Completed: sandbox-desktop'", timeout=5000, polling=50)
            if self.page.locator("#entry").input_value() != "sandbox-desktop":
                raise RuntimeError("independent browser state did not confirm typed input")
            self.stage = "task-evaluation"
            for _ in range(30):
                if self.evaluate(task)["score"] == 1:
                    break
                time.sleep(.1)
            else:
                raise RuntimeError("upstream evaluation did not observe completed GUI task")
            after = self.screen()
            if before["sha256"] == after["sha256"]:
                raise RuntimeError("desktop pixels did not change after the task")
            # Keep the discovered long-input defect covered by the real image
            # gate. Read back all 4096 Unicode characters independently; no
            # clipboard/process acknowledgment substitutes for destination data.
            self.stage = "unicode-boundary"
            self.dispatch({"operation": "click", "x": int(offset["x"] + box["x"] + 20),
                           "y": int(offset["y"] + box["y"] + 20), "button": "left"})
            self.dispatch({"operation": "hotkey", "keys": ["ctrl", "a"]})
            expected = "雪🙂" * 2048
            self.dispatch({"operation": "type_text", "text": expected})
            self.page.wait_for_function("document.getElementById('entry').value === '雪🙂'.repeat(2048)",
                                        timeout=5000, polling=50)
            if self.page.locator("#entry").input_value() != expected:
                raise RuntimeError("independent 4096-character Unicode paste check failed")
            return "desktop screenshot/click/type/hotkey/AT-SPI/evaluation OK"
        finally:
            fixture.unlink(missing_ok=True)

    def close(self):
        if self.browser is not None:
            with contextlib.suppress(Exception):
                self.browser.close()
        if self.playwright is not None:
            with contextlib.suppress(Exception):
                self.playwright.stop()
        if self.accessibility_thread is not None:
            self.server.pyatspi.Registry.stop()
            self.accessibility_thread.join(timeout=1)


def main():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    desktop = None
    protocol = sys.stdout
    try:
        # Libraries must not corrupt or leak into the one-line RPC stream.
        with contextlib.redirect_stdout(io.StringIO()):
            desktop = Desktop(STATE)
        protocol.write(json.dumps({"result": {"running": True, "width": 1024, "height": 768,
                                               "browser_geometry": desktop.geometry()}}) + "\n")
        protocol.flush()
        for line in sys.stdin:
            if len(line.encode()) > 32768:
                raise ValueError("request is too large")
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    result = desktop.dispatch(json.loads(line))
                reply = {"result": result}
            except Exception as exc:
                # Never reflect private text, URLs, task bodies or environment.
                reply = {"error": "desktop operation failed: " + type(exc).__name__ + " (" + desktop.stage + ")"}
            protocol.write(json.dumps(reply) + "\n")
            protocol.flush()
    except Exception as exc:
        detail = (exc.cause + " (" + exc.stage + ")") if isinstance(exc, InitializationError) else type(exc).__name__
        protocol.write(json.dumps({"error": "desktop initialization failed: " + detail}) + "\n")
        protocol.flush()
    finally:
        if desktop is not None:
            desktop.close()


if __name__ == "__main__":
    main()
