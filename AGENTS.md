# AGENTS.md

## Project Rules

- Project title and documentation name: `Video2Knowledge`.
- Source package directory: `app/`.
- Runtime target: Windows + PowerShell + Python 3.11+.
- Do not perform network installs unless the user explicitly approves.
- Do not run real provider live smoke tests unless the user explicitly approves.
- Do not use cookies, login sessions, or authenticated access unless the user explicitly approves.
- Do not download video, audio, subtitles, thumbnails, or other media artifacts unless the current stage explicitly allows it and the user confirms.
- Each real provider live validation must be confirmed as a separate step.
- Do not delete, move, or rename existing files unless the user explicitly asks.

## Development Loop

Before changing scope or architecture:

1. Read `README.md`, `PRD.md`, and this file.
2. Check `PROJECT_STATUS.md`, `TODO.md`, `DECISIONS.md`, and `PROGRAM_MAP.md`.
3. Record design decisions in `DECISIONS.md`.
4. Update `PROJECT_SNAPSHOT.md` at stage boundaries.

## Development Workflow

Every development stage follows:

```text
Plan -> Review -> Implement -> Validate -> Update Documentation -> Local Commit -> Review -> Push
```

- Plan first for medium or large changes.
- Keep each stage small and focused.
- Run tests or explain why validation cannot run.
- Update related project memory documents with the implementation.
- Commit locally after validation.
- Wait for user confirmation before pushing.
- Tag important architecture or release milestones.

## Stage Definition

A stage should:

- Solve one problem only.
- Be independently testable.
- Produce one logical commit.
- Update related documentation.
- Be reviewable before push.

Do not combine metadata, transcript, Whisper, LLM, export, and integration work into one stage.

## Validation

For software changes, prefer:

```powershell
python -m unittest discover -s tests
python -m app.cli import-url "https://example.com/watch?v=mock" --output-dir output/markdown
```

If validation cannot run, state why and do not invent results.

## Security

Never commit:

- `.env`
- `.venv`
- API keys
- tokens
- cookies
- local settings
- generated output files
