#!/usr/bin/env python3
"""Load real Omarchy components in an invisible, independent Wayland shell."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

project = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="input-switch-qml-") as temporary:
    root = Path(temporary)
    (root / "shell.qml").write_text((project / "tests" / "qml-smoke.qml").read_text())
    for name in ("Commons", "Ui"):
        (root / name).symlink_to(Path("/usr/share/omarchy/shell") / name, target_is_directory=True)
    environment = os.environ.copy()
    environment["INPUT_SWITCH_PROJECT"] = project.as_uri()
    environment["QT_QPA_PLATFORM"] = "wayland"
    runtime = Path(environment.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
    if not environment.get("WAYLAND_DISPLAY"):
        sockets = [p for p in runtime.glob("wayland-*") if p.is_socket()]
        if len(sockets) != 1:
            raise SystemExit("Set WAYLAND_DISPLAY for the desktop smoke test")
        environment["WAYLAND_DISPLAY"] = sockets[0].name
    if not environment.get("HYPRLAND_INSTANCE_SIGNATURE"):
        candidates = [p.name for p in (runtime / "hypr").iterdir() if p.is_dir()]
        if len(candidates) == 1:
            environment["HYPRLAND_INSTANCE_SIGNATURE"] = candidates[0]
    result = subprocess.run(["quickshell", "-p", str(root), "--no-color"], env=environment,
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=8)
    print(result.stdout)
    if result.returncode or "QML_SMOKE_PASSED" not in result.stdout or "WARN scene" in result.stdout or "ERROR qml" in result.stdout:
        sys.exit(1)
