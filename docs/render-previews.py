#!/usr/bin/env python3
"""Generate real QML component previews with sample state and a sample theme."""
import os
from pathlib import Path
import subprocess
import tempfile

project = Path(__file__).resolve().parents[1]
output = project / "docs" / "assets"
output.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix="input-switch-docs-") as directory:
    root = Path(directory)
    (root / "shell.qml").write_text((project / "docs" / "render-preview.qml").read_text())
    for name in ("Ui", "Commons"):
        (root / name).symlink_to(Path("/usr/share/omarchy/shell") / name, target_is_directory=True)
    environment = {**os.environ, "INPUT_SWITCH_PROJECT": project.as_uri(),
                   "INPUT_SWITCH_ASSETS": str(output), "QT_QPA_PLATFORM": "offscreen",
                   "QT_QUICK_BACKEND": "software"}
    result = subprocess.run(["quickshell", "-p", str(root), "--no-color"], env=environment,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=12)
    print(result.stdout)
    if result.returncode or "DOC_PREVIEWS_SAVED 2" not in result.stdout:
        raise SystemExit("Native component preview rendering failed")
