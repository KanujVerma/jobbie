"""Fail-closed Seatbelt profile for the temporary synthetic macOS pilot."""
from __future__ import annotations

import json
from pathlib import Path
import sys

SANDBOX = "/usr/bin/sandbox-exec"


def sandbox_command(arguments: list[str], *, worker: Path | None = None) -> list[str]:
    """Expose the interpreter, packages and parser entrypoint, without private data."""
    if sys.platform != "darwin" or not Path(SANDBOX).is_file():
        raise ValueError("macOS parser sandbox unavailable")
    runtime = Path(sys.base_prefix).resolve()
    prefix = Path(sys.prefix).resolve()
    programs = [Path(sys.executable).resolve()]
    bundled = runtime / "Resources/Python.app/Contents/MacOS/Python"
    if bundled.is_file():
        programs.append(bundled)
    runtime_dirs = (Path("/System/Library"), Path("/usr/lib"), Path("/Library/Apple/System/Library"),
                    Path("/usr/share/icu"), Path("/private/var/db/timezone"), runtime, prefix / "lib")
    files = [prefix / "pyvenv.cfg", Path("/dev/urandom"), Path("/dev/null")]
    if worker is not None:
        files.append(worker.resolve(strict=True))

    def selectors(kind: str, paths) -> str:
        return " ".join(f"({kind} {json.dumps(str(path))})" for path in paths)

    allowed = selectors("subpath", runtime_dirs)
    profile = "\n".join((
        "(version 1)", "(deny default)", '(import "system.sb")', "(deny network*)",
        "(allow sysctl-read)", "(allow file-read-metadata)",
        f"(allow process-exec {selectors('literal', programs)})",
        f"(allow file-read* {allowed} {selectors('literal', files)})",
        f"(allow file-map-executable {allowed})",
    ))
    return [SANDBOX, "-p", profile, *arguments]
