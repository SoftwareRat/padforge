import hashlib
import tempfile
import unittest
from pathlib import Path

from padforge.cli import published_app


class PublishedAppTests(unittest.TestCase):
    def test_download_is_checked_against_sha256sums(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            app = root / "Game-v1.0.0-android.apk"
            app.write_bytes(b"empty app")
            sums = root / "SHA256SUMS"
            sums.write_text(f"{hashlib.sha256(b'empty app').hexdigest()}  {app.name}\n")
            assets = {app.name: app.as_uri(), "SHA256SUMS": sums.as_uri()}
            path = published_app(app.name, assets, root / "cache")
            self.assertEqual(path.read_bytes(), b"empty app")
            app.write_bytes(b"tampered")
            (root / "cache" / app.name).unlink()
            with self.assertRaisesRegex(ValueError, "does not match"):
                published_app(app.name, assets, root / "cache")
            self.assertFalse((root / "cache" / app.name).exists())


if __name__ == "__main__":
    unittest.main()
