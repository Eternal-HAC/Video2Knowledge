# DECISIONS

## 2026-07-05

Decision:
Use a Mock-only first stage before integrating real video, transcript, Whisper, LLM, and export providers.

Reason:
The project needs a stable end-to-end pipeline and module boundary before external integrations add operational complexity.

Alternatives:
Start directly with yt-dlp, youtube-transcript-api, faster-whisper, and LLM provider integrations.

Impact:
The first stage can be validated locally without network installs or API credentials.

Follow-up Review:
Revisit when the Mock CLI, Markdown output, and tests are stable.

## 2026-07-05

Decision:
Keep generated knowledge notes as structured Markdown with YAML Frontmatter.

Reason:
Markdown is portable, Git-friendly, Obsidian-friendly, and suitable for later Notion or Feishu export.

Alternatives:
Store data first in a database or a proprietary note format.

Impact:
The core output contract is easy to inspect and test.

Follow-up Review:
Revisit if batch processing requires a richer intermediate data format.

## 2026-07-05

Decision:
Use only Python standard library in the Mock MVP.

Reason:
The current stage must avoid network installation and real external dependencies.

Alternatives:
Use Typer, Jinja2, PyYAML, and Pydantic immediately.

Impact:
The initial implementation is simpler but has a minimal template renderer and manual YAML output.

Follow-up Review:
Revisit when real provider integrations are introduced.

## 2026-07-05

Decision:
Use `app/` as the Stage 1 source directory.

Reason:
The user-provided initialization checklist names files such as `app/cli.py`, and the Mock MVP benefits from a simple, direct structure while the project shape is still early.

Alternatives:
Start immediately with a packaging-oriented `src/video2knowledge/` layout.

Impact:
The initial code is easy to inspect and run with `python -m app.cli`, but the package layout may need revision before distribution.

Follow-up Review:
If Video2Knowledge needs formal packaging or publishing, evaluate migrating to `src/video2knowledge/`.

## 2026-07-05

Decision:
Introduce platform and transcript provider boundaries before real integrations.

Reason:
The next stage needs a stable place to plug in YouTube, local files, subtitle APIs, and Whisper without mixing provider-specific code into the CLI.

Alternatives:
Call real provider libraries directly from the CLI when each feature is added.

Impact:
The CLI remains stable while implementation modules can be replaced incrementally.

Follow-up Review:
Revisit after the first real YouTube metadata and subtitle implementation is added.

## 2026-07-05

Decision:
Expose provider selection flags before implementing real providers.

Reason:
The CLI can keep a stable shape while non-Mock providers fail clearly instead of silently pretending to work.

Alternatives:
Hide provider selection until real integrations are complete.

Impact:
Users and tests can see the planned replacement points, but only `mock` is valid for successful runs right now.

Follow-up Review:
Remove or revise placeholder behavior when `yt-dlp` metadata and the transcript fallback chain are implemented.
