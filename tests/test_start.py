import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from padforge import cli

CATALOG = {
    "kartpad": {"id": "kartpad", "repo_url": "https://github.com/example/kartpad",
                "player_targets": ["android", "ios"], "manifest": {"name": "KartPad"}},
    "other": {"id": "other", "repo_url": "https://github.com/example/other"},
}


class StartTests(unittest.TestCase):
    def run_start(self, answers, host):
        replies = iter(answers)
        with mock.patch.object(cli, "catalog", return_value=CATALOG), \
                mock.patch.object(cli, "host_id", return_value=host), \
                mock.patch.object(cli, "make", return_value=0) as make:
            code = cli.start(lambda _prompt: next(replies), io.StringIO())
        return code, make

    def test_asks_only_for_the_game_file_and_folder_when_one_choice_remains(self):
        with tempfile.TemporaryDirectory() as folder:
            disc = Path(folder) / "My Disc.wbfs"
            disc.write_bytes(b"x")
            code, make = self.run_start([f"'{disc}'", folder], "linux-x86_64")
        self.assertEqual(code, 0)
        self.assertEqual(make.call_args.args[:3], ("kartpad", "android", disc.resolve()))
        self.assertEqual(make.call_args.args[3], Path(folder).resolve())

    def test_mac_also_offers_iphone(self):
        with tempfile.TemporaryDirectory() as folder:
            disc = Path(folder) / "disc.wbfs"
            disc.write_bytes(b"x")
            _code, make = self.run_start(["2", str(disc), folder], "macos-arm64")
        self.assertEqual(make.call_args.args[1], "ios")

    def test_dragged_paths_lose_quotes_and_escapes(self):
        self.assertEqual(cli.dropped_path('"C:/Games/My Disc.wbfs"'), Path("C:/Games/My Disc.wbfs"))
        if cli.os.name != "nt":
            self.assertEqual(cli.dropped_path("/tmp/My\\ Disc.wbfs "), Path("/tmp/My Disc.wbfs"))


if __name__ == "__main__":
    unittest.main()
