import hashlib
import io
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from padforge import tools


class ToolsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        archive = self.root / "tool.zip"
        with zipfile.ZipFile(archive, "w") as bundle:
            info = zipfile.ZipInfo("tool-1/bin/tool")
            info.external_attr = 0o755 << 16
            bundle.writestr(info, "#!/bin/sh\n")
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        self.lock = {"tool": {"version": "1", "env": {"TOOL_ROOT": "tool-1"}, "hosts": {
            "test-host": {"url": archive.as_uri(), "sha256": digest, "archive": "zip",
                          "bin": ["tool-1/bin"]}}}}
        self.patches = [mock.patch.object(tools, "lock", return_value=self.lock),
                        mock.patch.dict(os.environ, {"PADFORGE_HOME": str(self.root / "home")})]
        for patch in self.patches:
            patch.start()

    def tearDown(self):
        for patch in self.patches:
            patch.stop()
        self.temporary.cleanup()

    def test_install_checks_digest_and_environment_puts_tool_first(self):
        tools.install(["tool"], "test-host", io.StringIO())
        folder = tools.tools_root() / "tool-1"
        self.assertTrue((folder / "tool-1/bin/tool").is_file())
        if os.name != "nt":
            self.assertTrue(os.access(folder / "tool-1/bin/tool", os.X_OK))
        env = tools.environment(["tool"], "test-host", {"PATH": "/usr/bin"})
        self.assertEqual(env["PATH"].split(os.pathsep)[0], str(folder / "tool-1/bin"))
        self.assertEqual(env["TOOL_ROOT"], str(folder / "tool-1"))
        output = io.StringIO()
        tools.install(["tool"], "test-host", output)  # second run keeps the install
        self.assertIn("ok   tool 1", output.getvalue())

    def test_digest_mismatch_installs_nothing(self):
        self.lock["tool"]["hosts"]["test-host"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(RuntimeError, "mismatch"):
            tools.install(["tool"], "test-host", io.StringIO())
        self.assertFalse((tools.tools_root() / "tool-1/.padforge-installed").exists())

    def test_missing_system_git_says_how_to_install_it(self):
        self.lock["git"] = {"version": "2", "hosts": {}}
        with mock.patch.object(tools.shutil, "which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "package manager"):
                tools.install(["git"], "linux-x86_64", io.StringIO())

    def test_lock_pins_every_download_with_a_publisher_digest(self):
        lock = json.loads(tools.LOCK.read_text())["tools"]
        for name, tool in lock.items():
            for host, entry in tool["hosts"].items():
                with self.subTest(tool=name, host=host):
                    self.assertTrue(entry["url"].startswith("https://"))
                    self.assertTrue(any(key in entry for key in tools.DIGESTS))


if __name__ == "__main__":
    unittest.main()
