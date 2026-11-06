#!/usr/bin/env python3
"""Actual Gateway file/Agent/continuation/close task with independent CSV checks.

Use only the business Gateway. This script never connects to a Sandbox endpoint,
prints secrets/raw model output, or executes generated code on the host.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time
from typing import Callable
from urllib.parse import urlsplit
import uuid

import httpx

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "csv-analysis"
INPUT = (FIXTURES / "sales.csv").read_bytes()
SEED_PROGRAM = (FIXTURES / "aggregate.py").read_bytes()
SEED_PROGRAM_SHA256 = hashlib.sha256(SEED_PROGRAM).hexdigest()
ORIGINAL_TESTS_SHA256 = hashlib.sha256((FIXTURES / "tests" / "test_aggregate.py").read_bytes()).hexdigest()
DEMO = "/workspace/agents-api-demo"
TurnInspector = Callable[[str, str, str, dict[str, bytes]], None]


class SmokeFailure(Exception):
    """A controlled check label, never a raw remote exception or response."""


def require(condition: bool, label: str) -> None:
    if not condition:
        raise SmokeFailure(label)


def request(client: httpx.Client, method: str, path: str, expected: int, **kwargs) -> httpx.Response:
    require(path.startswith("/") and not path.startswith("//"), "same_gateway_path")
    try:
        response = client.request(method, path, **kwargs)
    except httpx.HTTPError:
        raise SmokeFailure("gateway_transport") from None
    require(response.status_code == expected, "http_" + str(expected))
    return response


def wait_submission(client: httpx.Client, sid: str, submission: str, deadline: float) -> dict:
    while time.monotonic() < deadline:
        value = request(client, "GET", f"/v1/agent-sandbox/sessions/{sid}/submissions/{submission}", 200).json()
        if value["status"] in {"completed", "failed", "cancelled", "uncertain"}:
            require(value["status"] == "completed", "agent_turn_completed")
            require(bool(value.get("turn_id")), "submission_turn_identity")
            turn = request(client, "GET", f"/v1/agents/sessions/{sid}/turns/{value['turn_id']}", 200).json()
            require(turn["status"] == "completed", "saved_turn_completed")
            return value
        time.sleep(0.5)
    raise SmokeFailure("agent_turn_deadline")


def submit(client: httpx.Client, sid: str, text: str, deadline: float) -> dict:
    response = request(client, "POST", f"/v1/agents/sessions/{sid}/events", 202,
                       headers={"Idempotency-Key": "smoke-input-" + uuid.uuid4().hex},
                       json={"events": [{"type": "agent.session.input.message", "input": text}]})
    require(not response.content, "accepted_empty_body")
    receipt = response.headers.get("X-Agent-Sandbox-Submission-Id", "")
    require(bool(receipt), "durable_submission_receipt")
    return wait_submission(client, sid, receipt, deadline)


def artifact(client: httpx.Client, sid: str, turn: str, name: str) -> bytes:
    cursor = None
    for _ in range(100):
        params = {"limit": 100, "order": "asc"}
        if cursor:
            params["after"] = cursor
        page = request(client, "GET", f"/v1/agents/sessions/{sid}/artifacts", 200, params=params).json()
        for item in page["data"]:
            if item.get("turn_id") == turn and item.get("path", "").endswith("/" + name):
                return request(client, "GET", f"/v1/agents/sessions/{sid}/artifacts/{item['id']}/content", 200).content
        if not page.get("has_more"):
            break
        cursor = page.get("last_id")
        require(bool(cursor), "artifact_pagination_cursor")
    raise SmokeFailure("required_artifact_missing")


def verify_csv(content: bytes, with_share: bool) -> None:
    try:
        reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
        rows = list(reader)
        require(reader.fieldnames == (["month", "total", "share"] if with_share else ["month", "total"]), "csv_columns")
        require([(row["month"], Decimal(row["total"])) for row in rows]
                == [("2026-01", Decimal("30.00")), ("2026-02", Decimal("10.00"))], "independent_csv_totals")
        if with_share:
            require(all(Decimal(row["share"]).is_finite()
                        and abs(Decimal(row["share"]) - Decimal(row["total"]) / Decimal("40.00"))
                        < Decimal("0.000001") for row in rows), "independent_csv_share")
    except (UnicodeError, ValueError, KeyError, csv.Error, InvalidOperation):
        raise SmokeFailure("invalid_csv_artifact") from None


def close(client: httpx.Client, sid: str, deadline: float) -> None:
    operation = request(client, "POST", f"/v1/agent-sandbox/sessions/{sid}/close", 202, json={}).json()
    while time.monotonic() < deadline:
        value = request(client, "GET", f"/v1/agent-sandbox/operations/{operation['id']}", 200).json()
        if value["status"] in {"succeeded", "failed", "requires_reconcile"}:
            require(value["status"] == "succeeded", "owned_compute_released")
            return
        time.sleep(0.5)
    raise SmokeFailure("cleanup_deadline")


def cleanup(client: httpx.Client, sid: str | None, released: bool, source_id: str, deadline: float) -> bool:
    """Attempt independent owned cleanup even after a prior cleanup fails."""
    actions = []
    if sid and not released:
        actions.append(lambda: close(client, sid, max(deadline, time.monotonic() + 60)))
    if sid:
        actions.append(lambda: request(client, "DELETE", f"/v1/agents/sessions/{sid}", 200))
    actions.append(lambda: request(client, "DELETE", f"/v1/files/{source_id}", 200))
    passed = True
    for action in actions:
        try:
            action()
        except (SmokeFailure, httpx.HTTPError, ValueError, KeyError, TypeError):
            passed = False
    return passed


def run(base: str, token: str, model: str | None, timeout: float,
        *, inspect_turn: TurnInspector | None = None) -> None:
    """Verify the business path; an optional trusted controller can inspect each idle turn.

    inspect_turn(stage, public_session_id, public_turn_id, artifacts) is an
    in-process engineering-test callback, never loaded from user input or the
    public API. It must use bounded private checks and return before the next
    managed turn starts. This script never executes generated code on the host.
    """
    target = urlsplit(base)
    require(target.scheme in {"http", "https"} and bool(target.hostname)
            and not target.username and not target.password and not target.query and not target.fragment, "explicit_gateway_url")
    require(bool(token), "business_token_required")
    deadline = time.monotonic() + timeout
    sid = None
    released = False
    with httpx.Client(base_url=base.rstrip("/"), headers={"Authorization": "Bearer " + token},
                      timeout=30, follow_redirects=False, trust_env=False) as client:
        health = request(client, "GET", "/healthz", 200).json()
        require(health.get("protocol") == "agent-sandbox-managed-agents/v1", "gateway_protocol")
        capabilities = request(client, "GET", "/v1/agent-sandbox/capabilities", 200).json()
        require(capabilities.get("protocol") == health["protocol"], "gateway_capabilities")
        models = request(client, "GET", "/v1/models", 200).json()["data"]
        require(bool(models), "deployed_model_available")
        selected = model or models[0]["id"]
        require(any(row["id"] == selected for row in models), "selected_model_allowlist")
        uploaded = request(client, "POST", "/v1/files", 200, data={"purpose": "user_data"},
                           files={"file": ("sales.csv", INPUT, "text/csv")}).json()
        source_id = uploaded["id"]
        try:
            created = request(client, "POST", "/v1/agents/sessions", 201,
                              headers={"Idempotency-Key": "smoke-session-" + uuid.uuid4().hex},
                              json={"agent": {"model": selected},
                                    "input": f"Repair the existing {DEMO}/aggregate.py so repeated months accumulate Decimal amounts. "
                                    f"Preserve its CLI: python {DEMO}/aggregate.py INPUT OUTPUT [--with-share]. "
                                    f"Do not change {DEMO}/tests/test_aggregate.py. Run those original tests. "
                                    f"Read {DEMO}/input/sales.csv and run the repaired program to write "
                                    "/workspace/outputs/summary.csv with exactly month,total, months ascending and totals to two decimals. "
                                    "Do not implement --with-share yet. Preserve the CSV input. "
                                    "Copy the actual repaired source to /workspace/outputs/aggregate.py. "
                                    "Write /workspace/outputs/report.md explaining the repair and both monthly totals.",
                                    "x_agent_sandbox": {"input_files": [
                                        {"file_id": source_id, "path": DEMO + "/input/sales.csv"}]}})
            session = created.json()
            sid = session["id"]
            initial = created.headers.get("X-Agent-Sandbox-Submission-Id", "")
            require(bool(initial), "initial_submission_receipt")
            first = wait_submission(client, sid, initial, deadline)
            first_bytes = artifact(client, sid, first["turn_id"], "summary.csv")
            verify_csv(first_bytes, False)
            first_program = artifact(client, sid, first["turn_id"], "aggregate.py")
            require(bool(first_program) and first_program != SEED_PROGRAM, "existing_source_modified")
            first_report = artifact(client, sid, first["turn_id"], "report.md")
            require(bool(first_report.strip()), "repair_report_saved")
            if inspect_turn:
                inspect_turn("summary", sid, first["turn_id"],
                             {"aggregate.py": first_program, "summary.csv": first_bytes,
                              "report.md": first_report})
            second = submit(client, sid,
                            f"Continue the same workspace and modify the existing {DEMO}/aggregate.py to implement --with-share. "
                            "The share is each total divided by the grand total, at least six decimal places; "
                            "use 0.000000 when the grand total is zero. Preserve the default month,total mode. "
                            f"Do not change {DEMO}/tests/test_aggregate.py; run those original tests again. "
                            f"Run python {DEMO}/aggregate.py {DEMO}/input/sales.csv "
                            "/workspace/outputs/summary-with-share.csv --with-share. "
                            "Preserve summary.csv and copy the actual modified source to /workspace/outputs/aggregate.py.", deadline)
            second_bytes = artifact(client, sid, second["turn_id"], "summary-with-share.csv")
            verify_csv(second_bytes, True)
            second_program = artifact(client, sid, second["turn_id"], "aggregate.py")
            require(bool(second_program) and second_program != first_program, "continuation_source_modified")
            if inspect_turn:
                inspect_turn("share", sid, second["turn_id"],
                             {"aggregate.py": second_program, "summary-with-share.csv": second_bytes})
            close(client, sid, deadline)
            released = True
            require(artifact(client, sid, first["turn_id"], "summary.csv") == first_bytes, "artifact_survives_compute_close")
            request(client, "DELETE", f"/v1/agents/sessions/{sid}", 200)
            request(client, "GET", f"/v1/agents/sessions/{sid}", 404)
            sid = None
        finally:
            primary_failure = sys.exc_info()[0] is not None
            if not cleanup(client, sid, released, source_id, deadline):
                print("FAIL: owned cleanup incomplete; use the private operation record to reconcile")
                if not primary_failure:
                    raise SmokeFailure("owned_cleanup_incomplete")


def hook_result(status: str) -> None:
    context_file, result_file = os.getenv("ABX_HOOK_CONTEXT_FILE"), os.getenv("ABX_HOOK_RESULT_FILE")
    if context_file and result_file:
        context = json.loads(Path(context_file).read_text())
        Path(result_file).write_text(json.dumps({"schemaVersion": 1, "hookId": context["hookId"],
                                                "operationId": context["operationId"], "status": status}) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("ABX_CANDIDATE_ENDPOINT", os.getenv("AGENTS_API_BASE_URL", "")))
    parser.add_argument("--model", default=os.getenv("AGENTS_API_MODEL"))
    parser.add_argument("--timeout-seconds", type=float, default=780)
    args = parser.parse_args()
    token = os.getenv("ABX_CANDIDATE_TOKEN", os.getenv("AGENTS_API_KEY", ""))
    try:
        require(0 < args.timeout_seconds <= 900, "bounded_timeout")
        run(args.base_url, token, args.model, args.timeout_seconds)
    except (SmokeFailure, httpx.HTTPError, ValueError, KeyError, TypeError):
        hook_result("failed")
        print("FAIL: managed Agent business workflow; inspect the private operation record")
        return 1
    hook_result("passed")
    print("PASS: Gateway input, two real Agent turns, independent CSV results and owned compute close")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
