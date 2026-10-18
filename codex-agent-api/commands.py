"""Project session HTTP adapter backed exclusively by pinned Codex exec JSONL."""
from __future__ import annotations

import atexit
import base64
import json
import os
import re
import selectors
import signal
from collections import deque
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Iterator

from agent_sandbox.server import (
    CapabilityGroup,
    SSEResponse,
    ServerRequest,
    ServerResponse,
    command,
    default_table,
    start,
)

# ── Configuration ──────────────────────────────────────────────────────

PINNED_VERSION = "0.162.1"
DEFAULT_MODEL = os.environ.get("CODEX_MODEL") or os.environ.get("ABX_LLM_MODEL", "")
MAX_SESSIONS = int(os.environ.get("AGENT_MAX_SESSIONS", "20"))
SESSION_TTL = int(os.environ.get("AGENT_SESSION_TTL", "1800"))  # seconds
TURN_TIMEOUT = 300  # seconds per turn
WORKSPACE = os.environ.get("WORKSPACE", "/home/user/workspace")
MAX_EVENTS = 1000
MAX_REPLAY_BYTES = 2_000_000
MAX_EVENT_BYTES = 256_000
MAX_TURNS = 100
MAX_AGENTS = 200
_ACTIVE: set = set()
_ACTIVE_LOCK = threading.Lock()


def _redact(text: str, extra_secrets: tuple = ()) -> str:
    secrets = list(extra_secrets) + [value for name, value in os.environ.items()
                                   if value and re.search(r"KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL", name, re.I)]
    for value in sorted(set(secrets), key=len, reverse=True):
        if value:
            text = text.replace(value, "[REDACTED]")
    return re.sub(r"(?i)(Bearer\s+)[^\s\"\']+", r"\1[REDACTED]", text)


def _redact_event(value: Any, extra_secrets: tuple = ()) -> Any:
    if isinstance(value, str):
        return _redact(value, extra_secrets)
    if isinstance(value, list):
        return [_redact_event(item, extra_secrets) for item in value]
    if isinstance(value, dict):
        return {_redact(str(key), extra_secrets): ("[REDACTED]" if re.search(
            r"(?i)(?:authorization|headers|api_key|secret|password|credential|private_key|access_token|refresh_token)$", key
        ) else _redact_event(item, extra_secrets)) for key, item in value.items()}
    return value

def _session_secrets(session: Any) -> tuple:
    values = []
    for tool in session.tools:
        transport = tool.get("transport", {})
        for headers in (tool.get("headers"), transport.get("headers") if isinstance(transport, dict) else None):
            if isinstance(headers, dict):
                for value in headers.values():
                    if isinstance(value, str) and value:
                        values.append(value)
                        if value.lower().startswith("bearer "):
                            values.append(value[7:])
    return tuple(values)


class EventBuffer(list):
    """Bounded list with incremental byte accounting, avoiding quadratic JSON work."""

    def __init__(self) -> None:
        super().__init__()
        self._sizes: deque = deque()
        self.byte_size = 0

    def append(self, event: dict) -> None:
        size = len(json.dumps(event).encode())
        super().append(event)
        self._sizes.append(size)
        self.byte_size += size
        while len(self) > MAX_EVENTS or (self.byte_size > MAX_REPLAY_BYTES and len(self) > 1):
            super().__delitem__(0)
            self.byte_size -= self._sizes.popleft()

    def clear(self) -> None:
        super().clear()
        self._sizes.clear()
        self.byte_size = 0


def _append_bounded(items: EventBuffer, event: dict) -> None:
    items.append(event)


def _validate_body(body: Any) -> str:
    if not isinstance(body, dict):
        return "JSON body must be an object"
    for name in ("stream", "background"):
        if name in body and not isinstance(body[name], bool):
            return f"{name} must be a boolean"
    if body.get("stream") and body.get("background"):
        return "stream and background cannot both be true"
    if len(json.dumps(body).encode()) > 1_000_000:
        return "Request body exceeds 1000000 bytes"
    config = body.get("agent", body)
    if isinstance(config, str):
        return ""
    if not isinstance(config, dict):
        return "agent must be an object or saved agent id"
    for name in ("model", "instructions", "name"):
        if name in config and not isinstance(config[name], str):
            return f"{name} must be a string"
    if "metadata" in config and not isinstance(config["metadata"], dict):
        return "metadata must be an object"
    tools = config.get("tools", [])
    if not isinstance(tools, list):
        return "tools must be a list"
    if len(tools) > 50:
        return "At most 50 MCP servers are supported"
    for tool in tools:
        if not isinstance(tool, dict) or tool.get("type") != "mcp":
            return "Only URL-based MCP tools are supported"
        transport = tool.get("transport", {})
        if not isinstance(transport, dict):
            return "MCP transport must be an object"
        url = transport.get("server_url") or transport.get("url") or tool.get("server_url") or tool.get("url")
        if not isinstance(url, str) or not url.startswith(("https://", "http://")):
            return "MCP tools require an http(s) server_url"
    return ""


# ── Route table ───────────────────────────────────────────────────────

table = default_table()

# ── Named commands (basic codex command for backward compat) ──────────


@command("codex_version", description="Print the installed Codex CLI version without a model call.")
def codex_version() -> str:
    proc = subprocess.run(["codex", "--version"], capture_output=True, text=True,
                          timeout=20, stdin=subprocess.DEVNULL, check=False)
    match = re.search(r"\d+\.\d+\.\d+", proc.stdout)
    if proc.returncode or not match:
        raise RuntimeError("Unable to determine Codex version")
    return match.group(0)


@command("codex", description="Run one bounded Codex exec turn; return JSON events.")
def codex_cmd(prompt: str, model: str = "", timeout_s: int = 300) -> dict:
    if not prompt.strip():
        raise ValueError("prompt is required")
    if not 1 <= timeout_s <= 3600:
        raise ValueError("timeout_s must be between 1 and 3600")
    session = Session(model=model or DEFAULT_MODEL)
    turn = Turn()
    session.turns.append(turn)
    proc = spawn_codex_turn(session, prompt, timeout=timeout_s)
    events = EventBuffer()
    event_count = 0
    for event in iter_codex_events(proc):
        event_count += 1
        _append_bounded(events, event)
    if turn.status != "completed":
        raise RuntimeError(next((str(e.get("error", {}).get("message", "Codex failed"))
                                 for e in reversed(events) if e.get("type") in ("error", "turn.failed")), "Codex failed"))
    return {"thread_id": session.thread_id, "events": events, "status": turn.status,
            "events_truncated": event_count > len(events)}


# ── Session data model ─────────────────────────────────────────────────


@dataclass
class Turn:
    """A single turn within a session."""

    id: str = field(default_factory=lambda: f"turn_{uuid.uuid4().hex[:24]}")
    status: str = "in_progress"  # in_progress | completed | failed | cancelled
    created_at: int = field(default_factory=lambda: int(time.time()))
    completed_at: int | None = None
    items: list[dict[str, Any]] = field(default_factory=EventBuffer)


@dataclass
class Session:
    """An Agent API session backed by Codex CLI."""

    id: str = field(default_factory=lambda: f"sess_{uuid.uuid4().hex[:24]}")
    object: str = "session"
    status: str = "idle"  # idle | in_progress | completed | failed | cancelled
    model: str = ""
    instructions: str = ""
    tools: list[dict[str, Any]] = field(default_factory=list)
    created_at: int = field(default_factory=lambda: int(time.time()))
    last_active: int = field(default_factory=lambda: int(time.time()))
    turns: list[Turn] = field(default_factory=list)
    items: list[dict[str, Any]] = field(default_factory=EventBuffer)
    # Token usage accumulated from Codex ``turn.completed`` events.
    usage: dict[str, int] = field(
        default_factory=lambda: {"input_tokens": 0, "output_tokens": 0}
    )
    # Codex thread id recorded from the first turn (used for resume).
    thread_id: str = ""
    error: dict | None = None
    _process: subprocess.Popen[bytes] | None = field(default=None, repr=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    def to_dict(self) -> dict[str, Any]:
        """Serialize this adapter's public JSON contract."""
        return _redact_event({
            "id": self.id,
            "object": self.object,
            "status": self.status,
            "model": self.model,
            "instructions": _redact(self.instructions, _session_secrets(self)),
            "tools": _redact_event(self.tools),
            "created_at": self.created_at,
            "metadata": {},
            "error": self.error,
        }, _session_secrets(self))

    def to_dict_with_output(self) -> dict[str, Any]:
        """Serialize with output items (for completed sessions)."""
        d = self.to_dict()
        d["output"] = self.items[-5:] if self.items else []  # last 5 items
        d["usage"] = dict(self.usage)  # real usage accumulated from turn.completed
        return d


# ── Session store (thread-safe) ────────────────────────────────────────


class CapacityError(Exception):
    """Raised when the session store cannot accept new sessions."""


def _kill_process(proc: subprocess.Popen[bytes]) -> None:
    """Reap the CLI and terminate descendants in its dedicated process group."""
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            break
        try:
            proc.wait(timeout=0.3)
        except subprocess.TimeoutExpired:
            continue
        # The parent can exit before a tool child; always signal the group again.
        if sig == signal.SIGTERM:
            continue
    try:
        proc.wait(timeout=1)
    except subprocess.TimeoutExpired:
        pass


class SessionStore:
    """Thread-safe in-memory session store with TTL and capacity limits."""

    def __init__(self, max_sessions: int = MAX_SESSIONS, ttl: int = SESSION_TTL) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()
        self._max = max_sessions
        self._ttl = ttl
        # Start GC daemon thread
        self._gc_thread = threading.Thread(target=self._gc_loop, daemon=True)
        self._gc_thread.start()

    def create(self, model: str, instructions: str, tools: list[dict[str, Any]]) -> Session:
        """Create a new session, evicting expired ones when at capacity."""
        with self._lock:
            if len(self._sessions) >= self._max:
                # Try to evict expired sessions first
                self._evict_expired()
                if len(self._sessions) >= self._max:
                    raise CapacityError("Too many active sessions")
            session = Session(model=model or DEFAULT_MODEL, instructions=instructions, tools=tools)
            self._sessions[session.id] = session
            return session

    def get(self, session_id: str) -> Session | None:
        """Return the session with *session_id*, or ``None``."""
        with self._lock:
            return self._sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        """Delete a session (killing any live turn process)."""
        with self._lock:
            session = self._sessions.pop(session_id, None)
            if session and session._process:
                session.status = "cancelled"
                _kill_process(session._process)
            return session is not None

    def list_all(self) -> list[Session]:
        """Return a snapshot of all sessions."""
        with self._lock:
            return list(self._sessions.values())

    def _evict_expired(self) -> None:
        """Drop sessions idle for longer than the TTL (caller holds the lock)."""
        now = int(time.time())
        expired = [sid for sid, s in self._sessions.items() if now - s.last_active > self._ttl]
        for sid in expired:
            s = self._sessions.pop(sid, None)
            if s and s._process:
                s.status = "cancelled"
                _kill_process(s._process)

    def _gc_loop(self) -> None:
        """Background loop evicting expired sessions every 60 seconds."""
        while True:
            time.sleep(60)
            with self._lock:
                self._evict_expired()


# Global session store
store = SessionStore()


# Cleanup on exit
def _cleanup() -> None:
    """Terminate every active turn, including standalone named command calls."""
    with _ACTIVE_LOCK:
        monitors = list(_ACTIVE)
    for monitor in monitors:
        _kill_process(monitor.proc)


atexit.register(_cleanup)


# ── Agent configuration store (thread-safe) ─────────────────────


@dataclass
class AgentConfig:
    """A saved, reusable Agent configuration."""

    id: str = field(default_factory=lambda: f"agent_{uuid.uuid4().hex[:24]}")
    object: str = "agent"
    model: str = ""
    instructions: str = ""
    tools: list[dict[str, Any]] = field(default_factory=list)
    name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: int = field(default_factory=lambda: int(time.time()))

    def to_dict(self) -> dict[str, Any]:
        """Serialize this adapter's public JSON contract."""
        return _redact_event({
            "id": self.id,
            "object": self.object,
            "model": self.model,
            "instructions": _redact(self.instructions, _session_secrets(self)),
            "tools": _redact_event(self.tools),
            "name": self.name,
            "metadata": _redact_event(self.metadata),
            "created_at": self.created_at,
        }, _session_secrets(self))


class AgentStore:
    """Thread-safe in-memory agent configuration store."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentConfig] = {}
        self._lock = threading.Lock()

    def create(
        self,
        model: str,
        instructions: str = "",
        tools: list[dict[str, Any]] | None = None,
        name: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> AgentConfig:
        """Create and store a new agent configuration."""
        with self._lock:
            if len(self._agents) >= MAX_AGENTS:
                raise CapacityError("Saved agent limit reached")
            agent = AgentConfig(
                model=model,
                instructions=instructions,
                tools=tools or [],
                name=name,
                metadata=metadata or {},
            )
            self._agents[agent.id] = agent
            return agent

    def get(self, agent_id: str) -> AgentConfig | None:
        """Return the agent with *agent_id*, or ``None``."""
        with self._lock:
            return self._agents.get(agent_id)

    def list_all(self) -> list[AgentConfig]:
        """Return a snapshot of all saved agents."""
        with self._lock:
            return list(self._agents.values())

    def update(self, agent_id: str, **kwargs: Any) -> AgentConfig | None:
        """Update mutable fields of an agent.

        The ``id``, ``object`` and ``created_at`` fields are immutable.
        """
        with self._lock:
            agent = self._agents.get(agent_id)
            if not agent:
                return None
            for key, value in kwargs.items():
                if hasattr(agent, key) and key not in ("id", "object", "created_at"):
                    setattr(agent, key, value)
            return agent

    def delete(self, agent_id: str) -> bool:
        """Delete an agent, returning whether it existed."""
        with self._lock:
            return self._agents.pop(agent_id, None) is not None


# Global agent store
agent_store = AgentStore()


# ── Codex CLI adapter ──────────────────────────────────────────────────


def _unique_mcp_label(raw_label: Any, index: int, used: set[str]) -> str:
    """Return a config-safe, unique MCP label without dotted path segments."""
    base = re.sub(r"[^A-Za-z0-9_-]", "_", str(raw_label or "")).strip("_") or f"mcp_{index}"
    label = base
    suffix = 2
    while label in used:
        label = f"{base}_{suffix}"
        suffix += 1
    used.add(label)
    return label


def _mcp_server_overrides(tools: list[dict[str, Any]]) -> list[str]:
    """Translate this adapter's remote MCP tools into Codex config overrides."""
    overrides: list[str] = []
    used_labels: set[str] = set()
    for tool in tools:
        if not isinstance(tool, dict) or tool.get("type") != "mcp":
            continue
        # Accept both the flat Responses-API shape and a nested ``transport``.
        transport = tool.get("transport")
        transport = transport if isinstance(transport, dict) else {}
        url = (
            transport.get("server_url")
            or transport.get("url")
            or tool.get("server_url")
            or tool.get("url")
        )
        if not isinstance(url, str) or not url:
            continue
        label = _unique_mcp_label(
            tool.get("server_label") or tool.get("name"), len(used_labels), used_labels
        )
        overrides += ["-c", f"mcp_servers.{label}.url={json.dumps(url)}"]
        headers = tool.get("headers") or transport.get("headers")
        if isinstance(headers, dict) and headers:
            entries = ", ".join(
                f"{json.dumps(str(key))} = {json.dumps(str(value))}"
                for key, value in headers.items()
            )
            overrides += ["-c", f"mcp_servers.{label}.http_headers={{{entries}}}"]
    return overrides


def _provider_overrides() -> list[str]:
    """Use an explicit Responses provider for an OpenAI-compatible gateway.

    ABX_LLM_BASE_URL is the fallback. API keys remain in the child environment.
    """
    base_url = (os.environ.get("OPENAI_BASE_URL") or os.environ.get("ABX_LLM_BASE_URL", "")).strip()
    if not base_url:
        return []
    prefix = "model_providers.openai_compatible"
    return [
        "-c", f"model_provider={json.dumps('openai_compatible')}",
        "-c", f"{prefix}.name={json.dumps('OpenAI-compatible endpoint')}",
        "-c", f"{prefix}.base_url={json.dumps(base_url)}",
        "-c", f"{prefix}.env_key={json.dumps('OPENAI_API_KEY')}",
        "-c", f"{prefix}.wire_api={json.dumps('responses')}",
        # Custom gateways serve the Responses HTTP API only; skip websockets.
        "-c", f"{prefix}.supports_websockets=false",
    ]


def _track_codex_event(session: Session, event: dict[str, Any], turn: Turn | None = None) -> None:
    """Fold a Codex JSONL event into session state.

    - ``item.started`` / ``item.completed`` events are accumulated as items.
    - ``thread.started`` records the Codex thread id so later turns can resume
      the exact thread instead of relying on ``resume --last`` (which picks the
      most recent thread in the workspace and can collide when several Agent
      API sessions share one sandbox).
    - ``turn.completed`` accumulates the token usage reported by Codex.
    """
    event_type = event.get("type")
    if event_type in ("item.started", "item.completed"):
        _append_bounded(session.items, event)
        if turn is not None:
            _append_bounded(turn.items, event)
    elif event_type == "thread.started":
        thread_id = event.get("thread_id")
        if isinstance(thread_id, str) and thread_id:
            session.thread_id = thread_id
    elif event_type == "turn.completed":
        event_usage = event.get("usage")
        if isinstance(event_usage, dict):
            for key in ("input_tokens", "output_tokens"):
                value = event_usage.get(key, 0)
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    session.usage[key] += int(value)


def spawn_codex_turn(session: Session, input_text: str, timeout: float = TURN_TIMEOUT) -> subprocess.Popen[bytes]:
    """Start pinned upstream Codex and an independent bounded output monitor.

    First turns never use resume --last. Subsequent turns require their exact
    thread id so concurrent sessions cannot accidentally share a conversation.
    """
    cmd = ["codex", "exec", "--json", "--color", "never", "--skip-git-repo-check"]
    # This mode is opt-in. Container isolation must be an explicit deployment choice.
    mode = os.environ.get("CODEX_SANDBOX", "workspace-write")
    if mode == "bypass":
        cmd.append("--dangerously-bypass-approvals-and-sandbox")
    elif mode in ("read-only", "workspace-write", "danger-full-access"):
        cmd.extend(["--sandbox", mode, "-c", 'approval_policy="never"'])
    else:
        raise ValueError("Invalid CODEX_SANDBOX")
    if session.model:
        cmd.extend(["--model", session.model])
    cmd.extend(_provider_overrides())
    cmd.extend(_mcp_server_overrides(session.tools))
    if session.instructions:
        cmd.extend(["-c", f"developer_instructions={json.dumps(session.instructions)}"])
    if len(session.turns) > 1:
        if not session.thread_id:
            raise RuntimeError("Previous turn has no Codex thread id; create a new session")
        cmd.extend(["resume", session.thread_id])
    cmd.extend(["--", input_text])
    env = os.environ.copy()
    if not env.get("OPENAI_API_KEY") and env.get("ABX_LLM_API_KEY"):
        env["OPENAI_API_KEY"] = env["ABX_LLM_API_KEY"]
    if not (env.get("OPENAI_BASE_URL") or env.get("ABX_LLM_BASE_URL")) and not env.get("CODEX_API_KEY") and env.get("OPENAI_API_KEY"):
        env["CODEX_API_KEY"] = env["OPENAI_API_KEY"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            stdin=subprocess.DEVNULL, cwd=WORKSPACE, env=env,
                            start_new_session=True)
    session._process = proc
    # Exactly one background reader drains both pipes even after HTTP disconnect.
    monitor = TurnMonitor(proc, session, session.turns[-1], timeout)
    proc._turn_monitor = monitor
    monitor.start()
    return proc


class TurnMonitor:
    """Own both pipes, a deadline and a bounded replay buffer for subscribers."""

    def __init__(self, proc: subprocess.Popen[bytes], session: Session, turn: Turn, timeout: float):
        self.proc, self.session, self.turn = proc, session, turn
        self.timeout = timeout
        self.events: deque = deque(maxlen=MAX_EVENTS)
        self.condition = threading.Condition()
        self.buffer_bytes = 0
        self.sequence = 0
        self.done = False
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self) -> None:
        with _ACTIVE_LOCK:
            _ACTIVE.add(self)
        self.thread.start()

    def emit(self, event: dict) -> None:
        event = _redact_event(event, _session_secrets(self.session))
        size = len(json.dumps(event).encode())
        if size > MAX_REPLAY_BYTES:
            raise RuntimeError("Codex event exceeds bounded replay size after redaction")
        with self.session._lock:
            _track_codex_event(self.session, event, self.turn)
            if event.get("type") in ("error", "turn.failed"):
                detail = event.get("error") or {"message": event.get("message", "Codex failed")}
                self.session.error = detail if isinstance(detail, dict) else {"message": str(detail)}
        with self.condition:
            if len(self.events) == MAX_EVENTS:
                self.buffer_bytes -= len(json.dumps(self.events.popleft()[1]).encode())
            while self.events and self.buffer_bytes + size > MAX_REPLAY_BYTES:
                self.buffer_bytes -= len(json.dumps(self.events.popleft()[1]).encode())
            self.events.append((self.sequence, event))
            self.buffer_bytes += size
            self.sequence += 1
            self.condition.notify_all()

    def run(self) -> None:
        proc = self.proc
        deadline = time.monotonic() + self.timeout
        stdout = bytearray()
        stderr = bytearray()
        failed = False
        completed = False
        completion_event = None
        secret_overlap = max([len(value.encode()) for key, value in os.environ.items()
                              if re.search(r"KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL", key, re.I)]
                             + [len(value.encode()) for value in _session_secrets(self.session)] or [0])
        def consume_line(raw: bytes) -> None:
            nonlocal failed, completed, completion_event
            if time.monotonic() >= deadline:
                raise TimeoutError("Turn timeout exceeded")
            if len(raw) > MAX_EVENT_BYTES:
                raise RuntimeError("Codex JSONL event exceeds 256000 bytes")
            try:
                event = json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError):
                return
            if isinstance(event, dict):
                failed |= event.get("type") in ("error", "turn.failed")
                completed |= event.get("type") == "turn.completed"
                if event.get("type") == "turn.completed":
                    completion_event = event
                else:
                    self.emit(event)

        selector = selectors.DefaultSelector()
        try:
            for name, pipe in (("stdout", proc.stdout), ("stderr", proc.stderr)):
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, name)
            while selector.get_map() or proc.poll() is None:
                if time.monotonic() >= deadline:
                    failed = True
                    self.emit({"type": "error", "error": {"message": "Turn timeout exceeded"}})
                    break
                for key, _ in selector.select(min(0.1, max(0, deadline - time.monotonic()))):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    if key.data == "stderr":
                        stderr.extend(chunk)
                        del stderr[:-(8192 + secret_overlap)]
                        continue
                    stdout.extend(chunk)
                    while b"\n" in stdout:
                        raw, _, rest = stdout.partition(b"\n")
                        stdout[:] = rest
                        consume_line(raw)
                    if len(stdout) > MAX_EVENT_BYTES:
                        raise RuntimeError("Codex JSONL event exceeds 256000 bytes")
            if stdout.strip():
                consume_line(bytes(stdout))
            if not failed and proc.wait(timeout=1) != 0:
                failed = True
                # Redact the whole bounded tail before truncation to avoid exposing a
                # credential straddling the truncation boundary.
                detail = _redact(stderr.decode("utf-8", "replace"), _session_secrets(self.session)).strip()[-2000:]
                self.emit({"type": "error", "error": {"message": f"codex exec failed: {detail or 'non-zero exit'}"}})
            if not failed and not completed:
                failed = True
                self.emit({"type": "error", "error": {"message": "Codex exited without turn.completed"}})
            if not failed and completion_event is not None:
                self.emit(completion_event)
        except Exception as exc:
            failed = True
            self.emit({"type": "error", "error": {"message": _redact(str(exc))}})
        finally:
            _kill_process(proc)
            selector.close()
            for pipe in (proc.stdout, proc.stderr):
                if pipe is not None:
                    pipe.close()
            with self.session._lock:
                cancelled = self.session.status == "cancelled"
                self.turn.status = "cancelled" if cancelled else ("failed" if failed else "completed")
                self.turn.completed_at = int(time.time())
                self.session.status = "cancelled" if cancelled else ("failed" if failed else "idle")
                self.session._process = None
                self.session.last_active = int(time.time())
            with _ACTIVE_LOCK:
                _ACTIVE.discard(self)
            with self.condition:
                self.done = True
                self.condition.notify_all()

    def iterate(self) -> Iterator[dict[str, Any]]:
        cursor = 0
        while True:
            with self.condition:
                while cursor >= self.sequence and not self.done:
                    self.condition.wait(0.2)
                gap = bool(self.events and cursor < self.events[0][0])
                batch = [(index, event) for index, event in self.events if index >= cursor]
                done = self.done
            if gap:
                yield {"type": "events.truncated", "message": "Replay buffer limited to last 1000 events"}
            for index, event in batch:
                cursor = index + 1
                yield event
            if done:
                return


def iter_codex_events(proc: subprocess.Popen[bytes], timeout: float = TURN_TIMEOUT) -> Iterator[dict[str, Any]]:
    """Subscribe without reading pipes or taking ownership from another client."""
    yield from proc._turn_monitor.iterate()


# Codex event type -> OpenAI Agents API event type
_EVENT_TYPE_MAP = {
    "thread.started": "agent.session.created",
    "turn.started": "agent.session.turn.started",
    "turn.completed": "agent.session.turn.completed",
    "item.started": "agent.session.output_item.added",
    "item.completed": "agent.session.output_item.done",
    "message.delta": "agent.session.output_text.delta",
    "message.completed": "agent.session.output_text.done",
    "error": "agent.session.turn.failed",
    "turn.failed": "agent.session.turn.failed",
}


def map_event(event: dict[str, Any], session_id: str, turn_id: str) -> str | None:
    """Map a Codex JSONL event to this adapter's documented SSE contract.

    Returns a formatted SSE string like::

        event: agent.session.turn.started
        data: {...}

    Returns ``None`` for events that should be skipped.
    """
    etype = event.get("type", "")

    api_event_type = _EVENT_TYPE_MAP.get(etype)
    if not api_event_type:
        # Pass through unknown events with a generic type
        if not etype:
            return None
        api_event_type = f"agent.session.{etype}"

    # Build the data payload
    data: dict[str, Any] = {
        "type": api_event_type,
        "session_id": session_id,
    }

    if "turn" in api_event_type:
        data["turn_id"] = turn_id

    # Include original event data
    if "item" in event:
        data["item"] = event["item"]
    if "message" in event:
        data["message"] = event["message"]
    if "delta" in event:
        data["delta"] = event["delta"]
    if "content" in event:
        data["content"] = event["content"]
    if "error" in event:
        data["error"] = event["error"]
    if "status" in event:
        data["status"] = event["status"]

    # Copy over any additional fields from the original event
    for key in ("result", "output", "text", "code", "tool_call", "function_call", "usage", "thread_id"):
        if key in event:
            data[key] = event[key]

    return f"event: {api_event_type}\ndata: {json.dumps(data)}\n\n"


def _extract_input_text(body: dict[str, Any]) -> str:
    """Extract user input text from a request body.

    Supports the plain string form (``{"input": "..."}``), the structured
    content-array form, and the ``agent.session.input.message`` event form
    used by the events endpoint.
    """
    input_text = body.get("input", "")
    if isinstance(input_text, str) and input_text:
        return input_text
    # input may be a structured content array: [{"type": "input_text", ...}]
    if isinstance(input_text, list):
        for part in input_text:
            if isinstance(part, dict) and part.get("type") == "input_text":
                return str(part.get("text", ""))
        return ""
    # "type": "agent.session.input.message" format
    if body.get("type") == "agent.session.input.message":
        content = body.get("content", [])
        if content and isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "input_text":
                    return str(c.get("text", ""))
    return ""


def _sse(event_type: str, payload: dict[str, Any]) -> str:
    """Format a single SSE event."""
    return f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"


def _turn_response(session: Session, turn: Turn, proc: subprocess.Popen, stream: bool,
                   created: bool = False, background: bool = False) -> SSEResponse | ServerResponse:
    if background:
        return ServerResponse.ok(session.to_dict_with_output())
    if not stream:
        for _ in iter_codex_events(proc):
            pass
        return ServerResponse.ok(session.to_dict_with_output())

    def event_gen() -> Iterator[str]:
        if created:
            yield _sse("agent.session.created", session.to_dict())
        yield _sse("agent.session.turn.started", {"turn_id": turn.id, "session_id": session.id})
        for event in iter_codex_events(proc):
            mapped = map_event(event, session.id, turn.id)
            if mapped:
                yield mapped
        # Completed/failed events originate from upstream or monitor, never fake PASS.
    return SSEResponse(event_iterator=event_gen())


# ── Agent API routes ───────────────────────────────────────────────────


# POST /v1/agents/sessions — Create session
@table.route("POST", "/v1/agents/sessions", group=CapabilityGroup.COMMANDS, streaming=True)
def create_session(request: ServerRequest) -> SSEResponse | ServerResponse:
    """Create a session and optionally run a first turn."""
    body = request.body if request.body is not None else {}
    invalid = _validate_body(body)
    if invalid:
        return ServerResponse.error(400, invalid, "ValueError")
    agent_config = body.get("agent", {})
    if isinstance(agent_config, str):
        # `agent` may reference a saved agent by ID instead of an inline dict.
        saved_agent = agent_store.get(agent_config)
        if not saved_agent:
            return ServerResponse.error(404, f"Agent {agent_config} not found", "NotFoundError")
        # Internal execution must retain MCP headers; public serialization redacts them.
        agent_config = {"model": saved_agent.model, "instructions": saved_agent.instructions,
                        "tools": saved_agent.tools}
    if not isinstance(agent_config, dict):
        agent_config = {}
    model = agent_config.get("model", DEFAULT_MODEL)
    instructions = agent_config.get("instructions", "")
    tools = agent_config.get("tools", [])
    input_text = _extract_input_text(body)
    stream = body.get("stream", False)

    try:
        session = store.create(model=model, instructions=instructions, tools=tools)
    except CapacityError:
        return ServerResponse.error(429, "Too many active sessions", "CapacityError")

    if not input_text:
        # No input — just create the session and return
        return ServerResponse.ok(session.to_dict())

    # Start a turn — turn creation, status update and process spawn happen
    # atomically under the session lock so concurrent requests cannot
    # interleave state transitions on this session.
    with session._lock:
        if len(session.turns) >= MAX_TURNS:
            return ServerResponse.error(429, "Session turn limit reached", "CapacityError")
        for previous in session.turns:
            previous.items.clear()
        turn = Turn()
        session.turns.append(turn)
        session.status = "in_progress"
        session.error = None
        session.last_active = int(time.time())

        try:
            proc = spawn_codex_turn(session, input_text)
            session._process = proc
        except Exception as exc:  # noqa: BLE001
            session.status = "failed"
            turn.status = "failed"
            return ServerResponse.error(500, _redact(str(exc)), "SpawnError")

    return _turn_response(session, turn, proc, stream, created=True, background=body.get("background", False))


# GET /v1/agents/sessions — List sessions
@table.route("GET", "/v1/agents/sessions", group=CapabilityGroup.COMMANDS)
def list_sessions(request: ServerRequest) -> ServerResponse:
    """List all sessions."""
    sessions = store.list_all()
    return ServerResponse.ok(
        {
            "object": "list",
            "data": [s.to_dict() for s in sessions],
        }
    )


# GET /v1/agents/sessions/{session_id} — Get session
@table.route("GET", "/v1/agents/sessions/{session_id}", group=CapabilityGroup.COMMANDS)
def get_session(request: ServerRequest) -> ServerResponse:
    """Retrieve a session by ID."""
    session_id = request.path_params.get("session_id", "")
    session = store.get(session_id)
    if not session:
        return ServerResponse.error(404, f"Session {session_id} not found", "NotFoundError")
    return ServerResponse.ok(session.to_dict_with_output())


# POST /v1/agents/sessions/{session_id} — Update session
@table.route("POST", "/v1/agents/sessions/{session_id}", group=CapabilityGroup.COMMANDS)
def update_session(request: ServerRequest) -> ServerResponse:
    """Update session configuration (model / instructions)."""
    session_id = request.path_params.get("session_id", "")
    session = store.get(session_id)
    if not session:
        return ServerResponse.error(404, f"Session {session_id} not found", "NotFoundError")

    body = request.body if request.body is not None else {}
    invalid = _validate_body(body)
    if invalid:
        return ServerResponse.error(400, invalid, "ValueError")
    if "model" in body:
        session.model = body["model"]
    if "instructions" in body:
        session.instructions = body["instructions"]
    session.last_active = int(time.time())

    return ServerResponse.ok(session.to_dict())


# DELETE /v1/agents/sessions/{session_id} — Delete session
@table.route("DELETE", "/v1/agents/sessions/{session_id}", group=CapabilityGroup.COMMANDS)
def delete_session(request: ServerRequest) -> ServerResponse:
    """Delete a session."""
    session_id = request.path_params.get("session_id", "")
    if store.delete(session_id):
        return ServerResponse.ok({"id": session_id, "object": "session", "deleted": True})
    return ServerResponse.error(404, f"Session {session_id} not found", "NotFoundError")


# POST /v1/agents/sessions/{session_id}/events — Send input
@table.route(
    "POST",
    "/v1/agents/sessions/{session_id}/events",
    group=CapabilityGroup.COMMANDS,
    streaming=True,
)
def send_event(request: ServerRequest) -> SSEResponse | ServerResponse:
    """Send user input to a session, starting a new turn."""
    session_id = request.path_params.get("session_id", "")
    session = store.get(session_id)
    if not session:
        return ServerResponse.error(404, f"Session {session_id} not found", "NotFoundError")

    # Conflict check, turn creation, status update and process spawn must
    # happen atomically under the session lock — otherwise two concurrent
    # requests can both pass the status check and start competing Codex
    # subprocesses.
    with session._lock:
        if session.status == "in_progress":
            return ServerResponse.error(409, "Session has an active turn", "ConflictError")

        body = request.body if request.body is not None else {}
        invalid = _validate_body(body)
        if invalid:
            return ServerResponse.error(400, invalid, "ValueError")
        input_text = _extract_input_text(body)

        if not input_text:
            return ServerResponse.error(400, "Missing input text", "ValueError")

        stream = body.get("stream", not body.get("background", False))  # default to streaming for events endpoint

        if len(session.turns) >= MAX_TURNS:
            return ServerResponse.error(429, "Session turn limit reached", "CapacityError")
        for previous in session.turns:
            previous.items.clear()
        turn = Turn()
        session.turns.append(turn)
        session.status = "in_progress"
        session.error = None
        session.last_active = int(time.time())

        try:
            proc = spawn_codex_turn(session, input_text)
            session._process = proc
        except Exception as exc:  # noqa: BLE001
            session.status = "failed"
            turn.status = "failed"
            return ServerResponse.error(500, _redact(str(exc)), "SpawnError")

    return _turn_response(session, turn, proc, stream, background=body.get("background", False))


# GET /v1/agents/sessions/{session_id}/events — SSE subscribe
@table.route(
    "GET",
    "/v1/agents/sessions/{session_id}/events",
    group=CapabilityGroup.COMMANDS,
    streaming=True,
)
def subscribe_events(request: ServerRequest) -> SSEResponse | ServerResponse:
    """Subscribe to the SSE event stream of the active turn."""
    session_id = request.path_params.get("session_id", "")
    session = store.get(session_id)
    if not session:
        return ServerResponse.error(404, f"Session {session_id} not found", "NotFoundError")

    if session.status != "in_progress" or not session._process:
        return ServerResponse.ok({"status": session.status, "message": "No active turn"})

    return _turn_response(session, session.turns[-1], session._process, True)


# GET /v1/agents/sessions/{session_id}/items — List items
@table.route("GET", "/v1/agents/sessions/{session_id}/items", group=CapabilityGroup.COMMANDS)
def list_items(request: ServerRequest) -> ServerResponse:
    """List the output items of a session."""
    session_id = request.path_params.get("session_id", "")
    session = store.get(session_id)
    if not session:
        return ServerResponse.error(404, f"Session {session_id} not found", "NotFoundError")
    return ServerResponse.ok(
        {
            "object": "list",
            "data": session.items,
        }
    )


# ── Artifacts helpers ──────────────────────────────────────────


def _decode_artifact_path(artifact_id: str) -> str:
    """Decode an artifact ID into a workspace-relative file path.

    Artifact IDs are URL-safe base64-encoded paths (e.g. ``cmVwb3J0Lm1k``
    for ``report.md``).  Values that fail to decode are used as-is so
    plain relative paths also work.
    """
    padded = artifact_id + "=" * (-len(artifact_id) % 4)
    try:
        return base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
    except Exception:  # noqa: BLE001
        return artifact_id


def _resolve_artifact_path(file_path: str) -> str | None:
    """Resolve *file_path* against the workspace root, safely.

    Returns the normalised absolute path, or ``None`` when the path escapes
    the workspace (e.g. ``../../etc/passwd`` or an absolute foreign path).
    """
    root = os.path.realpath(WORKSPACE)
    full_path = os.path.realpath(os.path.join(root, file_path))
    resolved_relative = os.path.relpath(full_path, root)
    path_parts = file_path.split("/") + resolved_relative.split(os.sep)
    if any(part in (".env", ".aws", ".codex", ".ssh") or part.startswith(".env.") for part in path_parts):
        return None
    if full_path == root or full_path.startswith(root + os.sep):
        return full_path
    return None


# GET /v1/agents/sessions/{session_id}/artifacts/{artifact_id} — Get artifact
@table.route(
    "GET",
    "/v1/agents/sessions/{session_id}/artifacts/{artifact_id}",
    group=CapabilityGroup.COMMANDS,
)
def get_artifact(request: ServerRequest) -> ServerResponse:
    """Download a workspace file artifact produced during a session."""
    session_id = request.path_params.get("session_id", "")
    artifact_id = request.path_params.get("artifact_id", "")

    session = store.get(session_id)
    if not session:
        return ServerResponse.error(404, f"Session {session_id} not found", "NotFoundError")

    file_path = _decode_artifact_path(artifact_id)
    full_path = _resolve_artifact_path(file_path)
    if full_path is None:
        return ServerResponse.error(403, "Access denied: path outside workspace", "ForbiddenError")

    if not os.path.isfile(full_path):
        return ServerResponse.error(404, _redact(f"Artifact not found: {file_path}", _session_secrets(session)), "NotFoundError")

    try:
        if os.path.getsize(full_path) > 1_000_000:
            return ServerResponse.error(413, "Artifact exceeds 1000000 bytes", "ValueError")
        with open(full_path, encoding="utf-8", errors="replace") as f:
            content = _redact(f.read(), _session_secrets(session))
        return ServerResponse.ok(
            {
                "id": artifact_id,
                "object": "artifact",
                "session_id": session_id,
                "file_path": _redact(file_path, _session_secrets(session)),
                "content": content,
                "size": os.path.getsize(full_path),
            }
        )
    except Exception as exc:  # noqa: BLE001
        return ServerResponse.error(500, _redact(str(exc), _session_secrets(session)), "ReadError")


# DELETE /v1/agents/sessions/{session_id}/artifacts/{artifact_id} — Delete artifact
@table.route(
    "DELETE",
    "/v1/agents/sessions/{session_id}/artifacts/{artifact_id}",
    group=CapabilityGroup.COMMANDS,
)
def delete_artifact(request: ServerRequest) -> ServerResponse:
    """Delete a workspace file artifact."""
    session_id = request.path_params.get("session_id", "")
    artifact_id = request.path_params.get("artifact_id", "")

    session = store.get(session_id)
    if not session:
        return ServerResponse.error(404, f"Session {session_id} not found", "NotFoundError")

    file_path = _decode_artifact_path(artifact_id)
    full_path = _resolve_artifact_path(file_path)
    if full_path is None:
        return ServerResponse.error(403, "Access denied: path outside workspace", "ForbiddenError")

    if not os.path.isfile(full_path):
        return ServerResponse.error(404, _redact(f"Artifact not found: {file_path}", _session_secrets(session)), "NotFoundError")

    try:
        os.remove(full_path)
        return ServerResponse.ok({"id": artifact_id, "object": "artifact", "deleted": True})
    except Exception as exc:  # noqa: BLE001
        return ServerResponse.error(500, _redact(str(exc), _session_secrets(session)), "DeleteError")


# ── Saved agents CRUD routes ─────────────────────────────────────
#
# NOTE: these generic ``/v1/agents/{agent_id}`` routes are deliberately
# registered AFTER the session routes above — RouteTable matches in
# registration order (linear scan), so the literal ``/v1/agents/sessions``
# paths win over the ``{agent_id}`` placeholder.


# POST /v1/agents — Create agent
@table.route("POST", "/v1/agents", group=CapabilityGroup.COMMANDS)
def create_agent(request: ServerRequest) -> ServerResponse:
    """Create a reusable agent configuration."""
    body = request.body if request.body is not None else {}
    invalid = _validate_body(body)
    if invalid:
        return ServerResponse.error(400, invalid, "ValueError")
    try:
        agent = agent_store.create(
            model=body.get("model", DEFAULT_MODEL),
            instructions=body.get("instructions", ""),
            tools=body.get("tools", []),
            name=body.get("name", ""),
            metadata=body.get("metadata", {}),
        )
    except CapacityError:
        return ServerResponse.error(429, "Saved agent limit reached", "CapacityError")
    return ServerResponse.ok(agent.to_dict())


# GET /v1/agents — List agents
@table.route("GET", "/v1/agents", group=CapabilityGroup.COMMANDS)
def list_agents(request: ServerRequest) -> ServerResponse:
    """List all saved agents."""
    agents = agent_store.list_all()
    return ServerResponse.ok({"object": "list", "data": [a.to_dict() for a in agents]})


# GET /v1/agents/{agent_id} — Get agent
@table.route("GET", "/v1/agents/{agent_id}", group=CapabilityGroup.COMMANDS)
def get_agent(request: ServerRequest) -> ServerResponse:
    """Retrieve a saved agent by ID."""
    agent_id = request.path_params.get("agent_id", "")
    agent = agent_store.get(agent_id)
    if not agent:
        return ServerResponse.error(404, f"Agent {agent_id} not found", "NotFoundError")
    return ServerResponse.ok(agent.to_dict())


# POST /v1/agents/{agent_id} — Update agent
@table.route("POST", "/v1/agents/{agent_id}", group=CapabilityGroup.COMMANDS)
def update_agent(request: ServerRequest) -> ServerResponse:
    """Update a saved agent's model / instructions / tools / name / metadata."""
    agent_id = request.path_params.get("agent_id", "")
    body = request.body if request.body is not None else {}
    invalid = _validate_body(body)
    if invalid:
        return ServerResponse.error(400, invalid, "ValueError")
    updates = {
        k: v for k, v in body.items() if k in ("model", "instructions", "tools", "name", "metadata")
    }
    agent = agent_store.update(agent_id, **updates)
    if not agent:
        return ServerResponse.error(404, f"Agent {agent_id} not found", "NotFoundError")
    return ServerResponse.ok(agent.to_dict())


# DELETE /v1/agents/{agent_id} — Delete agent
@table.route("DELETE", "/v1/agents/{agent_id}", group=CapabilityGroup.COMMANDS)
def delete_agent(request: ServerRequest) -> ServerResponse:
    """Delete a saved agent."""
    agent_id = request.path_params.get("agent_id", "")
    if agent_store.delete(agent_id):
        return ServerResponse.ok({"id": agent_id, "object": "agent", "deleted": True})
    return ServerResponse.error(404, f"Agent {agent_id} not found", "NotFoundError")


# The server SDK registers its own /v1/agents routes in the AGENTS group,
# which is off by default. A disabled route still matches first and answers
# 404, hiding the handlers below. This template owns those paths.
table._routes[:] = [route for route in table._routes if route.group is not CapabilityGroup.AGENTS]

# ── Serve ──────────────────────────────────────────────────────────


@command("agent_status", description="List active Agent API sessions.")
def agent_status() -> str:
    """List active Agent API sessions."""
    sessions = [
        {"id": session.id, "status": session.status, "model": session.model}
        for session in store.list_all()
    ]
    return _redact(json.dumps(sessions))


if __name__ == "__main__":
    import os

    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
