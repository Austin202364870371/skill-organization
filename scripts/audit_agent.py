#!/usr/bin/env python3
"""Locate the installed simplified ReAct implementation without assuming module paths."""

from __future__ import annotations

import importlib
import importlib.util
import inspect
import pkgutil
from pathlib import Path


def main() -> None:
    candidates = []
    for root_name in ("appworld_agents", "experiments"):
        spec = importlib.util.find_spec(root_name)
        if spec is None:
            continue
        module = importlib.import_module(root_name)
        paths = getattr(module, "__path__", [])
        for info in pkgutil.walk_packages(paths, prefix=f"{root_name}."):
            lowered = info.name.casefold()
            if "react" not in lowered or "agent" not in lowered:
                continue
            try:
                child = importlib.import_module(info.name)
            except Exception as exc:
                candidates.append({"module": info.name, "error": f"{type(exc).__name__}: {exc}"})
                continue
            classes = []
            for name, value in inspect.getmembers(child, inspect.isclass):
                if "react" in name.casefold() or name == "Agent":
                    classes.append({"name": name, "signature": str(inspect.signature(value)), "file": inspect.getsourcefile(value)})
            candidates.append({"module": info.name, "file": getattr(child, "__file__", None), "classes": classes})
    lines = ["# Installed simplified ReAct audit", ""]
    if not candidates:
        lines.append("No importable ReAct agent module was found; inspect the pinned source checkout manually.")
    for item in candidates:
        lines.extend([f"## `{item['module']}`", "", f"- File: `{item.get('file')}`"])
        if item.get("error"):
            lines.append(f"- Import error: `{item['error']}`")
        for value in item.get("classes", []):
            lines.append(f"- Class `{value['name']}{value['signature']}` in `{value['file']}`")
        lines.append("")
    output = Path("outputs/audits/agent_structure.md")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()

