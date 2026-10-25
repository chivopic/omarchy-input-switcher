import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "bridge" / "input_bridge.py"
SPEC = importlib.util.spec_from_file_location("input_bridge", MODULE_PATH)
bridge = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = bridge
SPEC.loader.exec_module(bridge)


class FakeBus:
    def __init__(self):
        self.owned = True
        self.engine = "rime"
        self.active = 2
        self.ascii_mode = False
        self.schema = "rime_ice"
        self.precise = True
        self.engines = ["keyboard-us", "rime"]
        self.calls = []
        self.ignore_set = False
        self.fail_ascii = False

    def name_has_owner(self, name):
        return self.owned

    def call_blocking(self, name, path, interface, method, signature, args, timeout):
        self.calls.append((path, method, signature, args))
        if method == "CurrentInputMethodGroup":
            return "Default"
        if method == "InputMethodGroupInfo":
            return "us", [(engine, "") for engine in self.engines]
        if method == "Introspect":
            methods = ("IsAsciiMode", "SetAsciiMode", "GetCurrentSchema") if self.precise else ()
            return '<node><interface name="org.fcitx.Fcitx.Rime1">' + ''.join(f'<method name="{method}"/>' for method in methods) + '</interface></node>'
        if method == "CurrentInputMethod":
            return self.engine
        if method == "State":
            return self.active
        if method == "GetCurrentSchema":
            return self.schema
        if method == "IsAsciiMode":
            if self.fail_ascii:
                raise RuntimeError("unavailable input context")
            return self.ascii_mode
        if method == "SetCurrentIM":
            if not self.ignore_set:
                self.engine = args[0]
            return
        if method == "Activate":
            self.active = 2
            return
        if method == "SetAsciiMode":
            self.ascii_mode = args[0]
            return
        raise AssertionError(method)

    def writes(self):
        return [call for call in self.calls if call[1] in {"SetCurrentIM", "Activate", "SetAsciiMode"}]


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.bus = FakeBus()
        self.backend = bridge.FcitxBackend(self.bus)

    def test_rime_ascii_mode_is_english_even_when_engine_is_rime(self):
        self.bus.ascii_mode = True
        state = self.backend.query()
        self.assertEqual(state.engine, "rime")
        self.assertEqual(state.effectiveLanguage, "en")

    def test_direct_chinese_clears_rime_ascii_mode_and_verifies(self):
        self.bus.ascii_mode = True
        state = self.backend.set_language("zh")
        self.assertEqual(state.effectiveLanguage, "zh")
        self.assertIn(("/rime", "SetAsciiMode", "b", (False,)), self.bus.writes())

    def test_repeated_selection_is_idempotent(self):
        self.backend.set_language("zh")
        self.assertEqual(self.bus.writes(), [])

    def test_direct_english_selects_keyboard_even_from_rime_ascii(self):
        self.bus.ascii_mode = True
        state = self.backend.set_language("en")
        self.assertEqual(state.engine, "keyboard-us")
        self.assertEqual(state.effectiveLanguage, "en")

    def test_toggle_reads_actual_external_mode(self):
        self.backend.query()
        self.bus.ascii_mode = True
        self.assertEqual(self.backend.toggle().effectiveLanguage, "zh")

    def test_no_rime_interface_never_claims_chinese_or_mutates(self):
        self.bus.precise = False
        self.assertEqual(self.backend.query().effectiveLanguage, "unknown")
        with self.assertRaisesRegex(bridge.BackendError, "精确模式"):
            self.backend.set_language("zh")
        self.assertEqual(self.bus.writes(), [])

    def test_missing_english_engine_does_not_mutate(self):
        self.bus.engines = ["rime"]
        with self.assertRaises(bridge.BackendError):
            self.backend.set_language("en")
        self.assertEqual(self.bus.writes(), [])

    def test_no_schema_is_unknown_rather_than_false_chinese(self):
        self.bus.schema = ""
        self.assertIsNone(self.backend.query().asciiMode)
        self.assertEqual(self.backend.query().effectiveLanguage, "unknown")

    def test_temporarily_unreadable_rime_is_unknown(self):
        self.bus.fail_ascii = True
        state = self.backend.query()
        self.assertTrue(state.available)
        self.assertEqual(state.effectiveLanguage, "unknown")
        self.assertTrue(state.error)

    def test_unconfirmed_set_reports_failure_and_actual_state(self):
        self.bus.ignore_set = True
        output = []
        with patch.object(bridge.time, "sleep"):
            bridge.Bridge(self.backend, output=output.append).handle('{"id":1,"op":"set","language":"en"}')
        self.assertFalse(output[-1]["ok"])
        self.assertEqual(output[-1]["error"]["code"], "unconfirmed")
        self.assertEqual(output[-2]["effectiveLanguage"], "zh")

    def test_invalid_protocol_input_does_not_crash_or_mutate(self):
        output = []
        handler = bridge.Bridge(self.backend, output=output.append)
        for line in ("{", "[]", '{"op":"toggle"}', '{"id":2,"op":"set","language":[]}', '{"id":3,"op":"remove"}'):
            handler.handle(line)
            self.assertFalse(output[-1]["ok"])
        handler.handle('{"id":4,"op":"status"}')
        self.assertTrue(output[-1]["ok"])
        self.assertEqual(self.bus.writes(), [])

    def test_unavailable_service_recovers(self):
        output = []
        handler = bridge.Bridge(self.backend, output=output.append)
        self.bus.owned = False
        handler.handle('{"id":1,"op":"status"}')
        self.assertFalse(output[-2]["available"])
        self.bus.owned = True
        handler.handle('{"id":2,"op":"status"}')
        self.assertTrue(output[-2]["available"])
        self.assertTrue(output[-1]["ok"])

    def test_unchanged_snapshots_are_not_repeated(self):
        output = []
        handler = bridge.Bridge(self.backend, output=output.append)
        handler.publish(self.backend.query())
        handler.publish(self.backend.query())
        self.assertEqual(len(output), 1)


if __name__ == "__main__":
    unittest.main()
