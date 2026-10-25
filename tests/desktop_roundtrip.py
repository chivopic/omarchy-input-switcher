#!/usr/bin/env python3
"""Explicit opt-in desktop test. Temporarily switches IM, then restores it."""
import argparse
import asyncio
from dataclasses import asdict
import importlib.util
import json
from pathlib import Path
import sys
import subprocess
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--allow-switch", action="store_true", required=True)
parser.add_argument("--via-shell", action="store_true", help="另外验证已安装插件的共享服务 IPC")
options = parser.parse_args()
path = Path(__file__).resolve().parents[1] / "bridge" / "input_bridge.py"
spec = importlib.util.spec_from_file_location("input_bridge", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
backend = module.FcitxBackend()
before = backend.query()
if not before.preciseRime or not {"rime", "keyboard-us"} <= set(before.engines):
    raise SystemExit("Requires Rime1 and configured rime/keyboard-us engines")
original_ascii = bool(backend.call("IsAsciiMode", rime=True))
timings = []
restored = False


async def external_change_test():
    process = await asyncio.create_subprocess_exec(sys.executable, str(path),
                                                  stdin=asyncio.subprocess.PIPE,
                                                  stdout=asyncio.subprocess.PIPE)
    try:
        initial = json.loads(await asyncio.wait_for(process.stdout.readline(), 3))
        assert initial["effectiveLanguage"] == "zh"
        backend.call("SetAsciiMode", (True,), rime=True, signature="b")
        changed = json.loads(await asyncio.wait_for(process.stdout.readline(), 3))
        assert changed["effectiveLanguage"] == "en"
        assert changed["engine"] == "rime"
        print(json.dumps({"externalChangePolling": "passed"}))
    finally:
        process.stdin.close()
        try:
            await asyncio.wait_for(process.wait(), 3)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()


def ipc(*arguments):
    return subprocess.check_output(["omarchy-shell", "input-switch", *arguments], text=True, timeout=3).strip()


def wait_for_language(language):
    deadline = time.monotonic() + 4
    while time.monotonic() < deadline:
        status = json.loads(ipc("status"))
        if not status["pending"] and not status["error"] and status["state"]["effectiveLanguage"] == language:
            return
        time.sleep(0.05)
    raise AssertionError(f"Shell IPC did not confirm {language}")


try:
    for language in ("en", "zh"):
        start = time.perf_counter()
        result = backend.set_language(language)
        timings.append({"language": language, "confirmed": result.effectiveLanguage,
                        "milliseconds": round((time.perf_counter() - start) * 1000, 2)})
        assert result.effectiveLanguage == language
    # Simulate an external Rime-internal switch without changing the engine.
    backend.call("SetAsciiMode", (True,), rime=True, signature="b")
    assert backend.query().engine == "rime"
    assert backend.query().effectiveLanguage == "en"
    assert backend.set_language("zh").asciiMode is False
    asyncio.run(external_change_test())
    if options.via_shell:
        for language in ("en", "zh"):
            assert ipc("set", language) == "queued"
            wait_for_language(language)
        print(json.dumps({"installedShellIpc": "passed"}))
    print(json.dumps({"roundtrips": timings, "rimeInternalMode": "passed"}, ensure_ascii=False))
finally:
    backend.call("SetAsciiMode", (original_ascii,), rime=True, signature="b")
    backend.call("SetCurrentIM", (before.engine,), signature="s")
    if before.active:
        backend.call("Activate")
    else:
        backend.call("Deactivate")
    after = backend.query()
    restored = (after.engine, after.active, after.asciiMode) == (before.engine, before.active, before.asciiMode)
    print(json.dumps({"restored": restored, "before": asdict(before), "after": asdict(after)}, ensure_ascii=False))
if not restored:
    raise SystemExit("Restored input state differs from the original")
