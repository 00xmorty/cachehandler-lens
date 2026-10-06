import json
import importlib.machinery
import importlib.util
import pathlib
from unittest.mock import patch
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


class StructuredTests(unittest.TestCase):
    def run_cli(self, root):
        result = subprocess.run([sys.executable, str(CLI), "--root", str(root), "--json"],
                                capture_output=True, text=True)
        return result, json.loads(result.stdout)

    def test_uti_only_and_filtered_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            contents = pathlib.Path(tmp) / "synthetic-name.app" / "Contents"
            contents.mkdir(parents=True)
            (contents / "Info.plist").write_bytes(plistlib.dumps({
                "CFBundleIdentifier": "private-identifier",
                "CFBundleDocumentTypes": [{"LSHandlerRank": "Owner",
                    "LSItemContentTypes": ["public.text", "public.text", "/private/path", "\u001b[31m"]}]},
                fmt=plistlib.FMT_BINARY))
            result, data = self.run_cli(tmp)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(data["schema_version"], 1)
            self.assertEqual(data["apps"][0]["document_types"][0],
                             {"rank": "Owner", "extensions": [], "utis": ["public.text"]})
            for private in (tmp, "synthetic-name", "private-identifier", "/private/path"):
                self.assertNotIn(private, result.stdout + result.stderr)

    def test_symlink_contents_never_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / "root"
            bundle = root / "linked.app"
            bundle.mkdir(parents=True)
            outside = pathlib.Path(tmp) / "outside"
            outside.mkdir()
            (outside / "Info.plist").write_bytes(plistlib.dumps({"CFBundleDocumentTypes": []}))
            (bundle / "Contents").symlink_to(outside, target_is_directory=True)
            result, data = self.run_cli(root)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(data["apps"][0]["status"], "UNKNOWN")
            self.assertIsNone(data["apps"][0]["declared_count"])

    def test_invalid_root_private_error_is_suppressed(self):
        result, data = self.run_cli("/nonexistent/synthetic-private-name")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(data["complete"])
        self.assertNotIn("synthetic-private-name", result.stdout + result.stderr)

    def test_output_truncation_and_malformed_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            contents = pathlib.Path(tmp) / "many.app" / "Contents"
            contents.mkdir(parents=True)
            (contents / "Info.plist").write_bytes(plistlib.dumps({
                "CFBundleDocumentTypes": ["invalid"] + [{"LSHandlerRank": "Default"}] * 100}))
            result, data = self.run_cli(tmp)
            self.assertEqual(result.returncode, 0)
            app = data["apps"][0]
            self.assertEqual(app["declared_count"], 101)
            self.assertTrue(app["truncated"])
            self.assertEqual(len(app["document_types"]), 100)
            self.assertEqual(app["document_types"][0]["rank"], "UNKNOWN")

    def test_walk_errors_mark_incomplete_without_paths(self):
        loader = importlib.machinery.SourceFileLoader("lens", str(CLI))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        assert spec is not None
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            def broken_walk(root, followlinks, onerror):
                onerror(PermissionError("synthetic-private-path"))
                return iter([])
            with patch.object(module.os, "walk", side_effect=broken_walk):
                data = module.scan(tmp)
            self.assertFalse(data["complete"])
            self.assertNotIn("synthetic-private-path", json.dumps(data))

    def test_scan_app_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            for index in range(101):
                (pathlib.Path(tmp) / f"fixture-{index}.app").mkdir()
            result, data = self.run_cli(tmp)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(data["complete"])
            self.assertEqual(len(data["apps"]), 100)


if __name__ == "__main__":
    unittest.main()
