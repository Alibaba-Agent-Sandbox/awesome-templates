"""Download a pandas summary and a matplotlib chart from Express."""
import asyncio
import json
import os
from pathlib import Path

from agent_sandbox.code_interpreter import AsyncSandbox

CODE = '''import json
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

frame = pd.DataFrame({"month": ["Jan", "Feb", "Mar"], "cents": [1250, 1880, 2000]})
summary = {"rows": len(frame), "total_cents": int(frame["cents"].sum()),
           "total": format(frame["cents"].sum() / 100, ".2f")}
Path("/tmp/expenses-summary.json").write_text(json.dumps(summary, sort_keys=True) + "\\n")
fig, ax = plt.subplots(figsize=(6, 3), dpi=100)
ax.bar(frame["month"], frame["cents"] / 100)
ax.set_ylabel("Amount")
fig.tight_layout()
fig.savefig("/tmp/expenses.png")
plt.close(fig)
summary
'''


async def main():
    # Explicitly use the same account as the CLI, including its region.
    options = {
        "api_key": os.environ["ABX_SANDBOX_API_KEY"],
        "api_url": os.environ["ABX_SANDBOX_BASE_URL"],
        "domain": os.environ["ABX_SANDBOX_DOMAIN"],
    }
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy:
        options["proxy"] = proxy
    sb = await AsyncSandbox.create(template="code-interpreter-v1", timeout=180, **options)
    try:
        execution = await sb.run_code(CODE)
        if execution.error:
            raise RuntimeError(execution.error.value)
        summary = await sb.files.read("/tmp/expenses-summary.json")
        chart = await sb.files.read("/tmp/expenses.png", format="bytes")
        Path("expenses-summary.json").write_text(summary)
        Path("expenses.png").write_bytes(chart)
        print(json.dumps(json.loads(summary), sort_keys=True))
    finally:
        await sb.kill()


if __name__ == "__main__":
    asyncio.run(main())
