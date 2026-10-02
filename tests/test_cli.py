import pathlib
import plistlib
import subprocess
import sys
import tempfile
import unittest

CLI = pathlib.Path(__file__).resolve().parents[1] / "cachehandler-lens"


class ScannerTests(unittest.TestCase):
    def test_real_cli_fixture_and_privacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "private-owner-name.app" / "Contents"
            path.mkdir(parents=True)
            (path / "Info.plist").write_bytes(plistlib.dumps({"CFBundleDocumentTypes": [
                {"LSHandlerRank": "Owner", "CFBundleTypeExtensions": ["csv", "/private/path"]},
                {"LSHandlerRank": "Other", "CFBundleTypeExtensions": ["txt"]}
            ]}))
            result = subprocess.run([sys.executable, str(CLI), "--root", tmp], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("rank=Owner extensions=csv", result.stdout)
            self.assertIn("rank=UNKNOWN extensions=txt", result.stdout)
            self.assertIn("registration=UNKNOWN; actual default=UNKNOWN", result.stdout)
            self.assertNotIn(tmp, result.stdout)
            self.assertNotIn("private-owner-name", result.stdout)
            self.assertNotIn("/private/path", result.stdout)

    def test_invalid_plist_and_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "bad.app" / "Contents"
            path.mkdir(parents=True)
            (path / "Info.plist").write_text("not plist")
            result = subprocess.run([sys.executable, str(CLI), "--root", tmp], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertIn("invalid plist", result.stdout)
            bad = subprocess.run([sys.executable, str(CLI), "--root", str(path / "missing")], capture_output=True, text=True)
            self.assertEqual(bad.returncode, 2)


if __name__ == "__main__":
    unittest.main()
