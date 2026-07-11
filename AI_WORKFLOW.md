# AI Collaboration Workflow

## Purpose

This document defines how ChatGPT Web, Codex Desktop, and GitHub collaborate on Video2Knowledge. It coordinates work across tools without replacing the project's product, architecture, status, planning, or decision documents.

The repository remains the source of truth. Chat history is supporting context, not durable project memory.

## Document Boundaries

Use the existing documents for their established responsibilities:

- `PRD.md`: product positioning, scope, and success criteria.
- `ARCHITECTURE.md`: system structure, boundaries, and technical design.
- `ROADMAP.md`: version milestones and sequencing.
- `PROJECT_STATUS.md`: chronological implementation status.
- `PROJECT_SNAPSHOT.md`: current stage-boundary summary.
- `TODO.md`: actionable work queue.
- `DECISIONS.md`: durable design decisions and their rationale.
- `PROGRAM_MAP.md`: current code and module map.
- `AGENTS.md`: repository rules and development workflow.
- `CHAT_INDEX.md`: pointers to important AI conversations and their durable outcomes.

Do not copy the contents of those documents into this file. If a conversation changes product scope, architecture, priorities, status, or code ownership, update the document that already owns that information.

## Tool Responsibilities

### ChatGPT Web

Use ChatGPT Web for exploratory work that benefits from broad discussion:

- Clarifying product intent, user experience, and trade-offs.
- Comparing approaches before a development stage is approved.
- Drafting a bounded proposal or review checklist.
- Reviewing explanations, documentation wording, and release narratives.

ChatGPT Web should not be treated as having authoritative knowledge of the current worktree. Before proposing repository changes, provide it with the relevant current documents or ask it to identify assumptions explicitly.

Its useful output is a proposal, review, or decision candidate. Durable conclusions must be transferred to the appropriate repository document; a chat transcript alone does not change project scope or architecture.

### Codex Desktop

Use Codex Desktop for repository-grounded execution:

- Read the current worktree and required project documents.
- Inspect Git state before editing.
- Plan, implement, and validate one bounded stage.
- Preserve unrelated user changes.
- Update the project memory document that owns each durable result.
- Create the local commit required by `AGENTS.md` after validation.
- Stop before push and wait for user confirmation.

Codex Desktop must follow `AGENTS.md`, including the explicit approval boundaries for dependency installation, authenticated access, live provider validation, media acquisition, and retained audio cache.

### GitHub

Use GitHub for shared review and repository history:

- Publish user-approved branches and commits.
- Review a focused pull request against its stated stage.
- Track review comments and CI results.
- Preserve the final discussion attached to the change.
- Merge only after the required review and validation are complete.

GitHub issues and pull requests may coordinate work, but they do not replace `PRD.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `TODO.md`, or the other repository memory documents. Any durable conclusion reached in GitHub must be reflected in the appropriate document before or with the implementation.

## Standard Collaboration Flow

Follow the project workflow in `AGENTS.md`:

```text
Plan -> Review -> Implement -> Validate -> Update Documentation -> Local Commit -> Review -> Push
```

The tools normally participate as follows:

1. Explore and frame the problem in ChatGPT Web when broad discussion is useful.
2. Record an important conversation in `CHAT_INDEX.md` if it will be needed for later work.
3. Transfer the approved objective, constraints, and unresolved questions to Codex Desktop.
4. Have Codex Desktop re-read the repository source of truth and reconcile the handoff with the current worktree.
5. Implement and validate one focused stage locally.
6. Update only the existing project documents whose owned facts changed.
7. Create a local commit and review its diff.
8. Push only after explicit user confirmation.
9. Use GitHub for pull-request review, CI, and merge history.
10. Reflect any durable review outcome back into the repository before merge or in a focused follow-up stage.

For small repository-grounded work, ChatGPT Web may be skipped. GitHub is skipped until the user approves publication.

## Handoff Contract

A handoff between tools should contain:

- Objective: one concrete outcome.
- Scope: files or subsystem included.
- Exclusions: work that must not be combined into the stage.
- Source of truth: repository branch or commit and required documents.
- Constraints: approvals, security boundaries, and compatibility requirements.
- Acceptance criteria: observable completion conditions.
- Validation: commands or review checks that should run.
- Open questions: unresolved choices that require user input.
- Conversation reference: a `CHAT_INDEX.md` entry when the source discussion is important.

The receiving tool must verify the handoff against the current repository. If chat guidance conflicts with committed documentation, stop and resolve the conflict rather than silently changing scope.

## Approval and Safety Boundaries

AI collaboration does not broaden authorization. In particular:

- Do not install dependencies without explicit user approval.
- Do not run a real provider live validation without separate explicit approval for that validation.
- Do not use cookies, login sessions, or authenticated access without explicit approval.
- Do not acquire or download media artifacts without explicit confirmation for the current stage.
- Do not retain audio cache without separate explicit confirmation.
- Do not push commits, open a pull request, or merge merely because local work is complete.
- Never place secrets, credentials, signed URLs, private chat content, or generated runtime output in commits or `CHAT_INDEX.md`.

When approval is required, record the approved scope in the working conversation or GitHub review. Record a durable policy in `DECISIONS.md` only when it changes or clarifies the project's design rules.

## Conflict Resolution

Resolve conflicting information in this order:

1. Explicit current user instruction.
2. `AGENTS.md` repository rules and safety boundaries.
3. Current committed product, architecture, decision, status, and planning documents according to their responsibilities.
4. The current worktree and Git history.
5. GitHub issue or pull-request discussion.
6. ChatGPT Web or Codex conversation history.

An earlier chat is never sufficient authority to override newer repository state. When a conflict changes product scope or architecture, obtain user direction and update the owning repository document.

## Completion Checklist

Before handing off or publishing a stage, confirm:

- The stage solves one problem and respects its exclusions.
- The current diff contains no unrelated or generated files.
- Validation results are real and reported accurately.
- Required approvals were obtained for sensitive actions.
- Durable facts were written to the document that owns them.
- `CHAT_INDEX.md` contains only useful pointers, not duplicated project memory.
- A local commit exists after validation.
- Push remains pending until user confirmation.
