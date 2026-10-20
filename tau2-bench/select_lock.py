"""Select Linux CPython3.13 markers from the unchanged frozen upstream export."""
from pathlib import Path
from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parent
PROFILE = {
    "implementation_name": "cpython", "implementation_version": "3.13.0",
    "os_name": "posix", "platform_machine": "x86_64", "platform_release": "",
    "platform_system": "Linux", "platform_version": "", "python_full_version": "3.13.0",
    "platform_python_implementation": "CPython", "python_version": "3.13",
    "sys_platform": "linux", "extra": "",
}


def select():
    selected = []
    pending = []
    for line in (ROOT / "requirements.upstream.lock").read_text().splitlines():
        pending.append(line)
        if line.endswith("\\"):
            continue
        block = "\n".join(pending)
        pending = []
        if not block.strip() or block.lstrip().startswith("#"):
            continue
        lines = block.splitlines()
        requirement = Requirement(lines[0].rstrip().removesuffix("\\").strip())
        if requirement.marker and not requirement.marker.evaluate(PROFILE):
            continue
        if requirement.marker:
            lines[0] = lines[0].split(";", 1)[0].rstrip() + " \\"
        selected.append("\n".join(lines))
    if pending:
        raise ValueError("incomplete frozen lock entry")
    compatibility = (ROOT / "requirements.compat.lock").read_text()
    (ROOT / "requirements.lock").write_text("\n".join(selected) + "\n" + compatibility)


if __name__ == "__main__":
    select()
