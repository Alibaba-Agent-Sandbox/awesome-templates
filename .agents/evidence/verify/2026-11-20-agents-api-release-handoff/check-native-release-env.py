#!/usr/bin/env python3
"""Verify the actual named-resource parser and local release init for all six recipes."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[4]
INPUTS = {
    "AGENTS_SERVER_IMAGE": "registry.example/team/server:unique",
    "ABX_MANAGED_DATABASE_URL": "postgresql://user:placeholder@database.example/db",
    "SANDBOX_API_KEY": "placeholder-platform-key",
    "SANDBOX_BASE_URL": "https://sandbox.example",
    "SANDBOX_DOMAIN": "sandbox.example",
    "AGENTS_FC_ROLE_ARN": "acs:ram::123:role/fc",
}

PROBE = """
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {loadResourceProject} from './dist/providers/alicloud_express/resource_executor.js';

const [file, phase] = process.argv.slice(1);
const project = loadResourceProject(file, process.env);
const region = project.sandbox.agent.template.region;
const state = phase === 'prepared'
  ? JSON.parse(fs.readFileSync(path.join(path.dirname(file), '.abx/agents-api/release.json'), 'utf8'))
  : null;
const credentials = phase === 'prepared'
  ? JSON.parse(fs.readFileSync(path.join(path.dirname(file), '.abx/agents-api/credentials.json'), 'utf8'))
  : null;
for (const [role, resource] of Object.entries(project.serving)) {
  const env = resource.props.environmentVariables;
  assert.ok(resource.props.region === region, 'Serving region differs from the prepared template region');
  if (role === 'worker' || role === 'dispatcher') {
    assert.ok(env.SANDBOX_REGION === region, 'Sandbox runtime region differs from the prepared template region');
  }
  if (state) {
    // Report predicates only. These values include a fresh temporary business token.
    assert.ok(resource.props.functionName === state.functions[role], 'function name mismatch');
    assert.ok(env.AGENTS_REVISION === state.revision, 'revision mismatch');
    assert.ok(env.ABX_MANAGED_INTERNAL_TOKEN === credentials.internalToken, 'private token mismatch');
    assert.ok(JSON.stringify(JSON.parse(env.AGENTS_POLICY_JSON)) === JSON.stringify(project.vars.policy), 'policy mismatch');
    assert.ok(JSON.parse(env.AGENTS_WORKERS_JSON)[state.revision] === state.functions.worker, 'Worker route mismatch');
  } else {
    assert.ok(env.AGENTS_REVISION === 'pending', 'expected unresolved release');
    assert.ok(env.AGENTS_POLICY_JSON === '' && env.AGENTS_WORKERS_JSON === '', 'invalid initial generated values');
  }
}
"""


def check(cli: Path, recipe: Path, working: Path, source: str) -> None:
    project = working / f"{recipe.name}-{source}"
    shutil.copytree(recipe, project, ignore=shutil.ignore_patterns(".env*", ".abx", "__pycache__"))
    profile = json.loads((project / "server/harness.json").read_text())
    values = {**INPUTS, profile["keyEnv"]: "placeholder-model-key", profile["modelEnv"]: "test-model"}
    if profile["baseUrlEnv"]:
        values[profile["baseUrlEnv"]] = "https://model.example/v1"
    home = working / "home"
    home.mkdir(exist_ok=True)
    environment = {"HOME": str(home), "PATH": os.environ["PATH"]}
    if source == "dotenv":
        (project / ".env").write_text("".join(f"{key}={value}\n" for key, value in values.items()))
    else:
        environment.update(values)
    node = ["node", "--input-type=module", "-e", PROBE, str(project / "template.yaml")]
    subprocess.run([*node, "initial"], env=environment, cwd=cli, check=True, timeout=35)
    subprocess.run(
        [sys.executable, str(project / "scripts/release.py"), "init", "--name", recipe.name, "--region", "cn-hangzhou"],
        env=environment, cwd=project, check=True, timeout=15, stdout=subprocess.DEVNULL,
    )
    subprocess.run([*node, "prepared"], env=environment, cwd=cli, check=True, timeout=35)
    print(f"PASS {recipe.name} with {source} inputs and native parsing before/after init")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", required=True, type=Path, help="Matching CLI checkout after npm ci and npm run build")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="abx-release-env-") as directory:
        for recipe in sorted(ROOT.glob("agents-api-*/server/harness.json")):
            for source in ("process", "dotenv"):
                check(args.cli.resolve(), recipe.parents[1], Path(directory), source)
