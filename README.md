# CacheHandler Lens

Offline, read-only inspection of `CFBundleDocumentTypes` in macOS `.app` bundles under a directory you explicitly select. Shows handler rank, safe filename extensions and UTI declarations without printing paths or app names.

## Run / install

Requires Python 3.9+; no third-party packages. On macOS or Linux:

```sh
git clone https://github.com/00xmorty/cachehandler-lens.git
cd cachehandler-lens
python3 cachehandler-lens --root /path/to/a/cache-directory
python3 cachehandler-lens --root /path/to/a/cache-directory --json
python3 -m unittest discover -s tests -v
```

Alternatively download the single-file release asset, inspect it, then run `python3 cachehandler-lens --root /path/to/directory --json`. No sudo required. The tests create synthetic app bundles and exercise the real CLI without requiring macOS.

## v0.2.0: UTI declarations and structured output

UTI-only declarations now appear even when there are no filename extensions. `--json` provides schema version 1, a `complete` scan flag and numbered `apps` with `status`, `declared_count`, `truncated` and `document_types`. Each document type contains `rank`, `extensions`, and `utis`. No bundle names or identifiers are emitted. App numbers are report-local, not stable identities across scans.

Example document type: `{"rank":"Owner","extensions":[],"utis":["public.text"]}`.

- Exit 0: directory traversal completed within bounds. Individual apps can still be UNKNOWN and their declarations may be truncated.
- Exit 2: invalid root, directory traversal error or scan bound exceeded. JSON still contains `complete: false`; never interpret a partial scan as proof of absence.
- `status: UNKNOWN`: missing, unreadable, oversized, malformed or symlink-redirected plist; not evidence of no handlers.
- `truncated: true`: only the first 100 document types are reported. Extension/UTI lists show at most 20 filtered unique values each; this is not an exhaustive inventory.

## Safety and limitations

- Reads selected app-bundle Info.plist files only. No writes, subprocesses, uploads, network access, telemetry, registry resets or handler changes.
- Scans up to 10,000 directory entries and 100 app bundles; reads at most 1 MiB + 1 byte per plist. Names and paths are not printed, including errors. Manually review the chosen directory before scanning. Unknown/unsafe extension and UTI strings are suppressed, but custom valid strings can still reveal business vocabulary: manually review reports before sharing.
- A declaration of `Owner` or `Default` is **not** proof that LaunchServices registered it or that Finder's effective default changed. Registration and actual default remain **UNKNOWN**. No `lsregister` query is made.
- Symlinked directories and plist path components are skipped, including `Contents` redirects and root ancestors. Use a canonical non-symlink path. Non-regular plist files are skipped. This is not a sandbox: concurrent filesystem changes can race checks; do not scan hostile or actively changing trees.
- A plist can be stale or malformed. This tool does not identify the originating app, repair macOS or guarantee a safe cleanup. No app names are emitted, so locating a bundle requires your separate local inspection.

MIT licensed. Security reports: see [SECURITY.md](SECURITY.md).
