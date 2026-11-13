# Verification: Agents API native-resource recipe

- Date: 2026-11-13.
- Result: PARTIAL — recorded local behavior passes; no new hosted application/upgrade claim.
- Scope: agents-api template, registry form, Server bootstrap, release script, bilingual
  documentation, docs/managed-agent-applications in both languages and scripts/test_managed_application.py.
- Environment: Python 3.13.13; isolated /tmp/abx-yaml-final-20261113/agents-release-venv and
  /tmp/abx-yaml-final-20261113/registry-venv.

## Dependencies and checks

Installed scripts/requirements.txt and the actual SDK source archive pinned in
agents-api/server/Dockerfile: b988d2a76057b6202d836ec329cc0bd90a572b26, SHA256
abefcb1f16d7c87089d9d560d4f8ebd5787a140351553b84f970a171fdd18f68. Installation succeeded;
this is an isolated source dependency test, not a PyPI release.

| Command, from repository root | Result | Scope |
| --- | --- | --- |
| `<agents-release-venv>/bin/python agents-api/scripts/test_release.py` | 12 passed | Token generation/reuse and explicit-override non-persistence; budgets; role secret isolation; actual pinned SDK bootstrap/signature; official SDK request shape; failed candidate leaves prod unchanged while new dispatcher owns routing; ownership and replacement drain refusal; actual SDK create/env/start order; three real local role subprocesses with health, Gateway authentication and signed empty drain against temporary SQLite. |
| `<registry-venv>/bin/python -m unittest discover -s scripts -p test_managed_application.py` | 10 passed | Schema and real business consumer separation; startup selection/refusal; duplicate YAML and independent import boundaries; native role shape and secret placement. |
| `<registry-venv>/bin/python scripts/check_template.py agents-api` | Conformant | Full recipe/document checker. |
| `python -m py_compile agents-api/scripts/release.py agents-api/server/bootstrap.py` | Passed | Python syntax. |

Initial tests exposed and corrected an invalid region regex, test-only SDK alias import, and
host-only FC endpoint requirement. Parent adversarial review exposed the old-timer candidate
race and stale-drain authorization; regression cases now cover their corrected behavior.
A later review corrected the mistaken transfer of dynamic authenticated startup into native snapshot preparation. The pinned SDK already owns creation plus explicit authenticated bridge startup, now covered by a regression.
A mistaken working directory caused one attempted edit/test command to fail before editing;
the intended operation was rerun in the owning repository. No failed test was relabeled a pass.

Local logs: /tmp/abx-yaml-final-20261113/agents-release-install.log,
agents-sdk-install.log, agents-native-validation.log. The complete Registry site was also
built from these coordinated sources; its results are recorded in the Registry repository.

## Not exercised

Docker command discovery returned exit 127 (`docker: command not found`); no Docker installation was attempted. No fresh Docker build of the changed Server bootstrap, FC-hosted candidate model task,
production alias switch, timer delivery, historical-session continuation or full cloud cleanup
was performed in this subtask. SDK method/model validation is not a cloud API acceptance test.
Existing image and business evidence remains historical and does not qualify these changes.
