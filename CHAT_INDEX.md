# AI Conversation Index

## Purpose

This file is a lightweight index of AI conversations that materially help continue, review, or audit Video2Knowledge work across ChatGPT Web, Codex Desktop, and GitHub.

It records pointers and outcomes, not full transcripts. The repository documents and Git history remain authoritative.

## What Belongs Here

Add an entry when a conversation:

- Produces a proposal that will be handed to another tool.
- Explains a non-obvious trade-off needed for later review.
- Leads to a durable repository update or focused implementation stage.
- Contains unresolved questions that must survive a tool handoff.
- Is likely to be referenced from a future GitHub issue or pull request.

Do not add routine command exchanges, transient debugging, or conversations whose complete outcome is already obvious from the commit and owning project document.

## Source-of-Truth Rules

- Product scope belongs in `PRD.md`.
- Technical structure belongs in `ARCHITECTURE.md`.
- Version sequencing belongs in `ROADMAP.md`.
- Durable design rationale belongs in `DECISIONS.md`.
- Current and chronological progress belongs in `PROJECT_SNAPSHOT.md` and `PROJECT_STATUS.md`.
- Action items belong in `TODO.md`.
- Code ownership and locations belong in `PROGRAM_MAP.md`.
- Repository operating rules belong in `AGENTS.md` and cross-tool coordination rules belong in `AI_WORKFLOW.md`.
- Commits and pull requests contain the authoritative implementation history.

If a conversation changes one of those facts, update the owning document. The index entry should link to or name that durable result instead of restating it.

## Privacy and Security

Never record:

- API keys, tokens, cookies, credentials, or authentication details.
- Signed URLs or sensitive query parameters.
- Private media locations or generated runtime artifacts.
- Full prompts or transcripts containing confidential information.
- Local machine details that are unnecessary for project continuity.

Use a stable public or user-accessible conversation link when available. If no durable link exists, use `Not available` and point to the resulting commit or repository document.

## Entry Format

Add new entries in reverse chronological order under `Conversation Log`.

```markdown
### YYYY-MM-DD - Short topic

- Surface: ChatGPT Web | Codex Desktop | GitHub
- Reference: URL, task identifier, issue/PR number, or `Not available`
- Repository state: branch and/or commit, if known
- Purpose: why the conversation mattered
- Outcome: concise result or `No durable change`
- Durable record: owning document, commit, issue, or pull request
- Open questions: unresolved items or `None`
```

Keep each entry concise. Link to repository files, commits, issues, or pull requests when those references are available and stable.

## Conversation Log

<!-- Add new entries immediately below this comment. -->
