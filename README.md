# CacheHandler Lens

Offline, read-only inspection of `CFBundleDocumentTypes` in macOS `.app` bundles under a directory you explicitly select. Shows handler rank and safe filename extensions without printing private paths or app names.

## Run

Requires Python 3.9+; no third-party packages. On macOS or Linux:

```sh
python3 cachehandler-lens --root /path/to/a/cache-directory
python3 -m unittest discover -s tests -v
```

To install locally, download the single-file release asset and run `python3 cachehandler-lens --root /path/to/directory` (inspect the file before use). No sudo required. For a local synthetic demonstration, run the bundled tests.

## Safety and limitations

- Reads only the selected directory's app-bundle Info.plist files. No writes, subprocesses, uploads, network access, telemetry, registry resets, or handler changes.
- Scans up to 10,000 directory entries and 100 app bundles; reports incomplete scans with exit status 2. App names and paths are not printed; manually review the chosen directory before scanning. Unknown/unsafe extension strings are suppressed.
- A declaration of `Owner` or `Default` is **not** proof that LaunchServices registered it or that Finder's effective default changed. Registration and actual default remain **UNKNOWN**. No `lsregister` query is made in this version.
- A plist can be stale or malformed, and this tool does not diagnose the originating app or repair macOS. Symlinked directories/plists are skipped; races with concurrent writes may affect results. Keep local paths and raw plists private.

MIT licensed. Security reports: see [SECURITY.md](SECURITY.md).
