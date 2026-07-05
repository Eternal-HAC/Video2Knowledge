# AGENTS.md

## Project Rules

- Project title and documentation name: `Video2Knowledge`.
- Source package directory: `app/`.
- Runtime target: Windows + PowerShell + Python 3.11+.
- First stage must stay Mock-only.
- Do not perform network installs unless the user explicitly approves.
- Do not connect real APIs during the Mock MVP stage.
- Do not delete, move, or rename existing files unless the user explicitly asks.

## Development Loop

Before changing scope or architecture:

1. Read `README.md`, `PRD.md`, and this file.
2. Check `PROJECT_STATUS.md` and `TODO.md`.
3. Record design decisions in `DECISIONS.md`.
4. Update `PROJECT_SNAPSHOT.md` at stage boundaries.

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

