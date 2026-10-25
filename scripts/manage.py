#!/usr/bin/env python3
"""Install a local copy with narrow config edits, backups and rollback."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

PLUGIN_ID = "io.github.chivopic.input-switch"
SOURCE = Path(__file__).resolve().parents[1]
MARKER = ".install-state.json"


def with_plugin(config: dict, section: str = "center") -> dict:
    result = deepcopy(config)
    layout = result.setdefault("bar", {}).setdefault("layout", {})
    if any(isinstance(entry, dict) and entry.get("id") == PLUGIN_ID
           for entries in layout.values() if isinstance(entries, list) for entry in entries):
        return result
    entries = layout.setdefault(section, [])
    anchor = next((i for i, entry in enumerate(entries)
                   if isinstance(entry, dict) and entry.get("id") == "omarchy.keyboard-layout"), None)
    entries.insert(anchor + 1 if anchor is not None else len(entries), {"id": PLUGIN_ID})
    return result


def without_plugin(config: dict) -> dict:
    result = deepcopy(config)
    layout = result.get("bar", {}).get("layout", {})
    for section, entries in layout.items():
        if isinstance(entries, list):
            layout[section] = [entry for entry in entries
                               if not isinstance(entry, dict) or entry.get("id") != PLUGIN_ID]
    if isinstance(result.get("plugins"), list):
        result["plugins"] = [entry for entry in result["plugins"]
                             if not (isinstance(entry, dict) and entry.get("id") == PLUGIN_ID)
                             and entry != PLUGIN_ID]
    return result


def read_config(path: Path) -> tuple[dict, bytes | None]:
    if path.is_symlink():
        raise RuntimeError("shell.json 是符号链接，请通过 Omarchy 插件命令手动启用，避免替换链接")
    raw = path.read_bytes() if path.exists() else None
    defaults = Path("/usr/share/omarchy/config/omarchy/shell.json")
    config = json.loads(raw if raw is not None else defaults.read_bytes() if defaults.exists() else b'{"version":1}')
    if not isinstance(config, dict):
        raise RuntimeError("shell.json 必须是 JSON 对象")
    return config, raw


def write_config(path: Path, config: dict, expected: bytes | None) -> None:
    if (path.read_bytes() if path.exists() else None) != expected:
        raise RuntimeError("shell.json 在安装过程中发生变化，请重试")
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o600
    fd, temporary = tempfile.mkstemp(prefix=".input-switch-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(config, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def manage(config_home: Path, *, uninstall: bool = False, section: str = "center", dry_run: bool = False) -> dict:
    config_home = config_home.expanduser().resolve()
    base = config_home / "omarchy"
    config_path = base / "shell.json"
    target = base / "plugins" / PLUGIN_ID
    if target.is_symlink() or target.resolve() == SOURCE:
        raise RuntimeError("安装目标不能是符号链接或开发源码目录")
    config, original = read_config(config_path)
    if target.exists():
        marker = target / MARKER
        if not marker.is_file() or json.loads(marker.read_text()).get("pluginId") != PLUGIN_ID or (target / ".git").exists():
            raise RuntimeError("已有非本安装器管理的插件目录，拒绝覆盖；请使用 omarchy plugin 命令管理")
    elif uninstall:
        return {"action": "not-installed", "target": str(target)}
    updated = without_plugin(config) if uninstall else with_plugin(config, section)
    result = {"action": "uninstall" if uninstall else "install", "target": str(target),
              "config": str(config_path), "dryRun": dry_run}
    if dry_run:
        result["layout"] = updated.get("bar", {}).get("layout", {})
        return result
    base.mkdir(parents=True, exist_ok=True)
    with (base / ".input-switch-install.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        # Reload after locking rather than overwrite a concurrent installation.
        config, original = read_config(config_path)
        updated = without_plugin(config) if uninstall else with_plugin(config, section)
        backup = base / "input-switch-backups" / datetime.now().strftime("%Y%m%dT%H%M%S.%f")
        backup.mkdir(parents=True, mode=0o700)
        if original is not None:
            (backup / "shell.json.before").write_bytes(original)
        result["backup"] = str(backup)
        target.parent.mkdir(parents=True, exist_ok=True)
        staging = None
        had_target = target.exists()
        moved_old = False
        placed_new = False
        try:
            if not uninstall:
                staging = Path(tempfile.mkdtemp(prefix=".input-switch-stage-", dir=base))
                shutil.copytree(SOURCE, staging, dirs_exist_ok=True,
                                ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", ".pytest_cache", MARKER))
                (staging / MARKER).write_text(json.dumps({"pluginId": PLUGIN_ID, "source": str(SOURCE), "backup": str(backup)}) + "\n")
            if had_target:
                target.rename(backup / "plugin.before")
                moved_old = True
            if staging is not None:
                staging.rename(target)
                staging = None
                placed_new = True
            write_config(config_path, updated, original)
        except Exception:
            if placed_new and target.exists():
                shutil.rmtree(target)
            if moved_old and (backup / "plugin.before").exists():
                (backup / "plugin.before").rename(target)
            raise
        finally:
            if staging is not None and staging.exists():
                shutil.rmtree(staging)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "uninstall"))
    parser.add_argument("--config-home", type=Path, default=Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")))
    parser.add_argument("--section", choices=("left", "center", "right"), default="center")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-reload", action="store_true")
    options = parser.parse_args()
    try:
        result = manage(options.config_home, uninstall=options.action == "uninstall", section=options.section, dry_run=options.dry_run)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Input Switch: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    actual_home = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser().resolve()
    if not options.dry_run and not options.no_reload and options.config_home.expanduser().resolve() == actual_home:
        executable = shutil.which("omarchy-shell")
        if executable:
            for method in ("rescanPlugins", "reloadConfig"):
                try:
                    subprocess.run([executable, "shell", method], check=True, timeout=10, capture_output=True)
                except (subprocess.SubprocessError, OSError):
                    print("配置已保存；Shell 暂不可达，插件将在下次启动时加载。")
                    break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
