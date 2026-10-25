import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("manage", Path(__file__).resolve().parents[1] / "scripts" / "manage.py")
manage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manage)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.home = Path(self.directory.name)
        self.config_path = self.home / "omarchy" / "shell.json"
        self.config_path.parent.mkdir()
        self.original = {"version": 1, "idle": {"lock": 300}, "plugins": [{"id": "other.service"}],
                         "bar": {"layout": {"center": [{"id": "omarchy.clock"}, {"id": "omarchy.keyboard-layout"}],
                                            "right": [{"id": "other.widget", "custom": 7}]}}}
        self.config_path.write_text(json.dumps(self.original))

    def tearDown(self):
        self.directory.cleanup()

    def config(self):
        return json.loads(self.config_path.read_text())

    def test_install_update_uninstall_preserve_other_settings(self):
        result = manage.manage(self.home)
        target = Path(result["target"])
        self.assertTrue((target / "Service.qml").is_file())
        self.assertFalse((target / ".git").exists())
        self.assertEqual(self.config()["bar"]["layout"]["center"][-1]["id"], manage.PLUGIN_ID)
        changed = self.config()
        changed["idle"]["lock"] = 900
        self.config_path.write_text(json.dumps(changed))
        manage.manage(self.home)
        self.assertEqual(sum(entry["id"] == manage.PLUGIN_ID for entry in self.config()["bar"]["layout"]["center"]), 1)
        removed = manage.manage(self.home, uninstall=True)
        self.assertFalse(target.exists())
        self.assertTrue((Path(removed["backup"]) / "plugin.before").exists())
        expected = self.original.copy()
        expected["idle"] = {"lock": 900}
        self.assertEqual(self.config(), expected)

    def test_dry_run_writes_nothing(self):
        original = self.config_path.read_bytes()
        manage.manage(self.home, dry_run=True)
        self.assertEqual(self.config_path.read_bytes(), original)
        self.assertFalse((self.config_path.parent / "plugins").exists())

    def test_refuses_unmanaged_target(self):
        target = self.config_path.parent / "plugins" / manage.PLUGIN_ID
        target.mkdir(parents=True)
        (target / "mine").write_text("keep")
        with self.assertRaises(RuntimeError):
            manage.manage(self.home)
        self.assertEqual((target / "mine").read_text(), "keep")

    def test_config_failure_rolls_back_previous_plugin(self):
        result = manage.manage(self.home)
        target = Path(result["target"])
        (target / "local-file").write_text("keep")
        original = self.config_path.read_bytes()
        with patch.object(manage, "write_config", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                manage.manage(self.home)
        self.assertEqual((target / "local-file").read_text(), "keep")
        self.assertEqual(self.config_path.read_bytes(), original)

    def test_user_moved_entry_and_options_are_retained_on_update(self):
        changed = self.original.copy()
        changed = json.loads(json.dumps(changed))
        entry = {"id": manage.PLUGIN_ID, "showOsd": False}
        changed["bar"]["layout"]["right"].append(entry)
        self.config_path.write_text(json.dumps(changed))
        manage.manage(self.home)
        self.assertEqual(self.config(), changed)

    def test_failed_staging_does_not_delete_existing_plugin(self):
        result = manage.manage(self.home)
        target = Path(result["target"])
        (target / "local-file").write_text("keep")
        with patch.object(manage.shutil, "copytree", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                manage.manage(self.home)
        self.assertEqual((target / "local-file").read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
