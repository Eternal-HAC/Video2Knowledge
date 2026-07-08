# PROJECT_STATUS

## 2026-07-05

Status: Stage 1 initialization in progress.

Current goal:

- Establish the Video2Knowledge project structure.
- Implement a standard-library Mock MVP pipeline.
- Validate the CLI and unit tests locally.

Current implementation:

- No real API integrations.
- No external Python dependencies.
- Mock pipeline only.

Known constraints:

- `output/` is generated runtime data and should not be committed.
- Real video, transcript, Whisper, LLM, Notion, Feishu, MCP, and browser extension work is deferred.

## 2026-07-05

Status: Stage 2 interface groundwork started.

Changes:

- Added a platform adapter boundary for URL/local source classification.
- Added transcript result metadata for future fallback strategy.
- Kept all providers Mock-only.
- Added explicit non-Mock provider placeholders that fail with clear not-implemented errors.

Validation target:

- Unit tests must still pass.
- Existing Mock CLI command must remain compatible.

## 2026-07-05

Status: Architecture correction stage in progress.

Changes:

- Move business orchestration out of CLI and into `app.pipeline`.
- Add platform capabilities before real YouTube metadata work.
- Keep all providers Mock-only or explicitly not implemented.

Validation target:

- CLI remains compatible.
- Mock pipeline still writes Markdown.
- Unit tests pass.

## 2026-07-05

Status: Documentation synchronization stage in progress.

Changes:

- Record the development workflow in existing project memory documents.
- Update roadmap to version-based milestones.
- Update snapshot to `v0.2.0 Architecture Stable`.
- Keep `CODEX_WORKFLOW.md` out of the document set to avoid workflow duplication.

Validation target:

- Only Markdown documents are changed.
- No product code changes.

## 2026-07-05

Status: `v0.3.x Real Metadata` implementation in progress.

Changes:

- Implement YouTube metadata-only provider through the `yt-dlp` Python API.
- Keep transcript, summary, Markdown, and export on the existing Mock/local path.
- Declare `yt-dlp` as a dependency without installing it in this stage.

Validation target:

- Unit tests use mocked `yt_dlp` and do not access the network.
- Mock CLI regression still passes.
- Live installation and YouTube smoke test remain separate confirmation steps.

## 2026-07-06

Status: `v0.4.x Official Transcript` implementation in progress.

Changes:

- Add YouTube official subtitle provider for VTT/WebVTT tracks only.
- Read official subtitle tracks from `yt-dlp` metadata `raw_metadata["subtitles"]`.
- Keep automatic captions, transcript API fallback, Whisper, and LLMs out of this stage.
- Keep transcript provider attempts stable with `yt_dlp_official_subtitles`.

Validation target:

- Unit tests mock subtitle fetching and do not access YouTube.
- Mock CLI regression still passes.
- Live official subtitle smoke test remains a separate confirmation step.

## 2026-07-06

Status: `v0.4.x Official Transcript` error boundary fix in progress.

Findings:

- TED video metadata-only screening found official subtitles with a `zh-CN` VTT/WebVTT track.
- Full official subtitle smoke test reached the VTT text request step but received YouTube HTTP 429.
- Browser access to YouTube also showed HTTP 429, so this is treated as current access environment or platform rate limiting.
- This does not mean the selected video lacks official subtitles.

Changes:

- Wrap official subtitle VTT text fetch failures in `TranscriptProviderError`.
- Keep errors sanitized so subtitle URLs, signatures, tokens, cookies, and temporary credentials are not exposed.

Validation target:

- CLI must print a concise `Error: official subtitle VTT fetch failed: ...` message without traceback.
- Real VTT parsing smoke test remains pending until the network environment is no longer rate limited.

## 2026-07-08

Status: `v0.4.x Official Transcript` live smoke test passed.

Validation:

- URL: `https://www.youtube.com/watch?v=iG9CE55wbtY`
- Selected subtitle: official `zh-CN` `vtt`
- Provider: `yt_dlp_official_subtitles`
- Attempted providers: `["yt_dlp_official_subtitles"]`
- Output: Markdown only
- Generated Markdown: `output\markdown\do-schools-kill-creativity-sir-ken-robinson-ted.md`
- No video, audio, subtitle, thumbnail, or other media artifacts were found in the project directory.
- Unit tests passed: `Ran 30 tests ... OK`

Next target:

- Prepare `v0.4.0` tag.
- Plan `v0.5.x Whisper Fallback`, starting with fallback policy and error taxonomy.

## 2026-07-08

Status: `v0.5.0a Fallback Policy and Error Taxonomy` implementation in progress.

Changes:

- Add transcript error classes for fallback-eligible and access-failure cases.
- Define Whisper fallback eligibility policy.
- Keep `real-fallback` as a policy validator only; it does not download audio or run Whisper in this stage.
- Preserve official subtitle behavior and automatic captions boundary.

Policy:

- Missing official subtitles can enter future Whisper fallback.
- Official subtitles without VTT/WebVTT can enter future Whisper fallback.
- Platform access failures such as HTTP 429 and HTTP 403 must stop.
- Network access failures such as timeout and network request failure must stop.
- Metadata contract errors must stop.

Validation target:

- Unit tests cover eligibility and non-eligibility cases without network access.
- Mock CLI regression still passes.
