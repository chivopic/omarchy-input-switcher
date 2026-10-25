#!/usr/bin/env python3
"""Persistent Fcitx5 connection, verified Rime switching and an NDJSON protocol.

The Controller does not emit a signal for every language/submode change. One
shared 500ms poll catches changes made by Fcitx hotkeys and other applications.
No input text, window titles, or candidate contents are inspected.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from typing import Any
from xml.etree import ElementTree

SERVICE = "org.fcitx.Fcitx5"
CONTROLLER = "org.fcitx.Fcitx.Controller1"
RIME = "org.fcitx.Fcitx.Rime1"
TIMEOUT = 0.5


class BackendError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass
class Snapshot:
    backend: str = "fcitx5"
    available: bool = False
    engine: str = ""
    active: bool = False
    asciiMode: bool | None = None
    effectiveLanguage: str = "unknown"
    schema: str = ""
    engines: list[str] = field(default_factory=list)
    preciseRime: bool = False
    error: str = ""


class FcitxBackend:
    def __init__(self, bus: Any = None):
        self.bus = bus
        self._metadata_at = 0.0
        self.engines: list[str] = []
        self.precise_rime = False

    def connect(self) -> None:
        if self.bus is None:
            try:
                import dbus
            except ImportError as exc:
                raise BackendError("missing-dependency", "需要 python-dbus：omarchy pkg add python-dbus") from exc
            try:
                self.bus = dbus.SessionBus(private=True)
            except Exception as exc:
                raise BackendError("session-unavailable", "无法连接桌面会话 D-Bus") from exc
        try:
            owned = self.bus.name_has_owner(SERVICE)
        except Exception as exc:
            self.bus = None
            raise BackendError("session-unavailable", "桌面会话 D-Bus 已断开") from exc
        if not owned:
            self._metadata_at = 0.0
            self.precise_rime = False
            raise BackendError("fcitx-unavailable", "Fcitx5 未运行")

    def call(self, method: str, args: tuple = (), *, rime: bool = False, signature: str = "") -> Any:
        try:
            return self.bus.call_blocking(
                SERVICE, "/rime" if rime else "/controller",
                RIME if rime else CONTROLLER, method, signature, args, timeout=TIMEOUT,
            )
        except Exception as exc:
            raise BackendError("dbus-error", f"输入法接口 {method} 调用失败") from exc

    def metadata(self) -> None:
        if time.monotonic() - self._metadata_at < 10:
            return
        group = str(self.call("CurrentInputMethodGroup"))
        _layout, entries = self.call("InputMethodGroupInfo", (group,), signature="s")
        self.engines = [str(entry[0]) for entry in entries]
        self.precise_rime = False
        if "rime" in self.engines:
            try:
                xml = self.bus.call_blocking(
                    SERVICE, "/rime", "org.freedesktop.DBus.Introspectable",
                    "Introspect", "", (), timeout=TIMEOUT,
                )
                interface = ElementTree.fromstring(str(xml)).find(f"interface[@name='{RIME}']")
                methods = {m.get("name") for m in interface.findall("method")} if interface is not None else set()
                self.precise_rime = {"IsAsciiMode", "SetAsciiMode", "GetCurrentSchema"} <= methods
            except Exception:
                # Older Rime builds still work as engine indicators, never fake 中.
                pass
        self._metadata_at = time.monotonic()

    def query(self) -> Snapshot:
        self.connect()
        self.metadata()
        engine = str(self.call("CurrentInputMethod"))
        state = int(self.call("State"))
        snapshot = Snapshot(available=True, engine=engine, active=state == 2,
                            engines=list(self.engines), preciseRime=self.precise_rime)
        if engine == "keyboard-us":
            snapshot.effectiveLanguage = "en"
        elif engine == "rime" and state == 2 and self.precise_rime:
            try:
                schema = str(self.call("GetCurrentSchema", rime=True))
                ascii_mode = bool(self.call("IsAsciiMode", rime=True))
                # Empty schema can mean no usable Rime context or maintenance.
                if schema:
                    snapshot.schema = schema
                    snapshot.asciiMode = ascii_mode
                    snapshot.effectiveLanguage = "en" if ascii_mode else "zh"
            except BackendError:
                snapshot.error = "Rime 模式暂不可读"
        return snapshot

    def unavailable_snapshot(self, error: BackendError) -> Snapshot:
        return Snapshot(error=str(error))

    def set_language(self, language: str) -> Snapshot:
        if not isinstance(language, str) or language not in {"zh", "en"}:
            raise BackendError("invalid-language", "语言必须是 zh 或 en")
        before = self.query()
        if before.effectiveLanguage == language and (language != "en" or before.engine == "keyboard-us"):
            return before
        target = "rime" if language == "zh" else "keyboard-us"
        if target not in before.engines:
            raise BackendError("engine-missing", f"当前输入法组未配置 {target}")
        if language == "zh" and not before.preciseRime:
            raise BackendError("unsupported-rime", "此 Rime 未提供精确模式接口，无法确认中文状态")
        self.call("SetCurrentIM", (target,), signature="s")
        if language == "zh":
            self.call("Activate")
            self.call("SetAsciiMode", (False,), rime=True, signature="b")
        for attempt in range(6):
            after = self.query()
            if after.effectiveLanguage == language:
                return after
            if attempt < 5:
                time.sleep(0.03)
        raise BackendError("unconfirmed", "切换结果未确认；请聚焦输入框后重试")

    def toggle(self) -> Snapshot:
        current = self.query()
        # Unknown is not English: ask explicitly for Chinese, then verify it.
        return self.set_language("en" if current.effectiveLanguage == "zh" else "zh")

    def execute(self, request: dict) -> Snapshot:
        operation = request.get("op")
        if operation == "status":
            return self.query()
        if operation == "toggle":
            return self.toggle()
        if operation == "set":
            return self.set_language(request.get("language"))
        raise BackendError("invalid-operation", "不支持的操作")


class Bridge:
    def __init__(self, backend: FcitxBackend, interval: float = 0.5, output=None):
        self.backend = backend
        self.interval = interval
        self.output = output or self.write
        self.previous: dict | None = None

    @staticmethod
    def write(message: dict) -> None:
        print(json.dumps(message, ensure_ascii=False, separators=(",", ":")), flush=True)

    def publish(self, snapshot: Snapshot, force: bool = False) -> None:
        state = asdict(snapshot)
        if force or state != self.previous:
            self.output({"type": "state", **state})
            self.previous = state

    def handle(self, line: str) -> None:
        request_id = None
        try:
            request = json.loads(line)
            if not isinstance(request, dict):
                raise BackendError("invalid-request", "请求必须是 JSON 对象")
            request_id = request.get("id")
            if not isinstance(request_id, (str, int)) or isinstance(request_id, bool):
                raise BackendError("invalid-request", "请求需要字符串或整数 id")
            snapshot = self.backend.execute(request)
            self.publish(snapshot, force=True)
            self.output({"type": "result", "id": request_id, "ok": True})
        except json.JSONDecodeError:
            self.output({"type": "result", "id": None, "ok": False,
                         "error": {"code": "invalid-json", "message": "无效的 JSON 请求"}})
        except BackendError as exc:
            # A setter may partially succeed before verification fails. Publish
            # what is actually observable, rather than retaining the old label.
            try:
                self.publish(self.backend.query(), force=True)
            except BackendError as query_error:
                self.publish(self.backend.unavailable_snapshot(query_error), force=True)
            self.output({"type": "result", "id": request_id, "ok": False,
                         "error": {"code": exc.code, "message": str(exc)}})

    async def poll(self) -> None:
        failures = 0
        while True:
            try:
                self.publish(self.backend.query())
                failures = 0
            except BackendError as exc:
                self.publish(self.backend.unavailable_snapshot(exc))
                failures += 1
            await asyncio.sleep(min(10, self.interval * 2 ** min(failures, 5)))

    async def run(self) -> None:
        reader = asyncio.StreamReader(limit=65536)
        protocol = asyncio.StreamReaderProtocol(reader)
        transport, _ = await asyncio.get_running_loop().connect_read_pipe(lambda: protocol, sys.stdin)
        task = asyncio.create_task(self.poll())
        try:
            while True:
                try:
                    line = await reader.readline()
                except ValueError:
                    self.output({"type": "fatal", "error": "请求超过 64 KiB"})
                    break
                if not line:
                    break
                try:
                    self.handle(line.decode("utf-8"))
                except UnicodeDecodeError:
                    self.output({"type": "result", "id": None, "ok": False,
                                 "error": {"code": "invalid-encoding", "message": "请求需要 UTF-8 编码"}})
        finally:
            task.cancel()
            transport.close()
            try:
                await task
            except asyncio.CancelledError:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--status", action="store_true", help="读取实际输入法状态")
    action.add_argument("--doctor", action="store_true", help="检查连接和精确 Rime 能力")
    action.add_argument("--set", choices=("zh", "en"), help="指定中文或英文并验证")
    action.add_argument("--toggle", action="store_true", help="切换中文与英文并验证")
    parser.add_argument("--poll-ms", type=int, default=500)
    options = parser.parse_args()
    backend = FcitxBackend()
    if options.status or options.doctor or options.set or options.toggle:
        try:
            state = (backend.set_language(options.set) if options.set else
                     backend.toggle() if options.toggle else backend.query())
            print(json.dumps(asdict(state), ensure_ascii=False))
            return 0
        except BackendError as exc:
            try:
                state = backend.query()
            except BackendError as query_error:
                state = backend.unavailable_snapshot(query_error)
            print(json.dumps({**asdict(state), "operationError": str(exc), "code": exc.code}, ensure_ascii=False))
            return 2
    try:
        asyncio.run(Bridge(backend, max(250, min(options.poll_ms, 10000)) / 1000).run())
    except (BrokenPipeError, KeyboardInterrupt):
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
