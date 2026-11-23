# How to start the project with Claude Code

Claude Code specifics below are from my general knowledge and may have changed. Verify against the official
Claude Code documentation if a command behaves differently.

## One-time setup (≈30 min)
1. Create an empty GitHub repo `changeguard-ai` and clone it.
2. Copy this bundle into the repo root so you have `CLAUDE.md` at the root and `docs/` beside it.
3. `git add . && git commit -m "docs: project context"` (commit the docs before any code exists).
4. Make sure Docker, `uv` and Git are installed. Create a free Supabase project later (needed at T06, not before).
5. Start Claude Code in the repo root: run `claude` from that folder. CLAUDE.md is picked up automatically from the project root.

## First message to send
Use the prompt in `docs/prompts/KICKOFF.md` (it includes PROJECT_UPDATE.md, forces inspect-plan-wait, and has the follow-up messages for approval and verification).
Review its plan. If it matches the docs, send the approval message from the same file.

## Daily 2-hour routine
- 10 min: read docs/PROGRESS.md, pick the next ticket from docs/BACKLOG.md.
- 80 min: Claude Code plan → approve → implement → tests.
- 20 min: run the verification commands YOURSELF, read the diff, commit, update docs/PROGRESS.md.
- Start a fresh Claude Code session per ticket (clear context) so it re-reads CLAUDE.md and PROGRESS.md.
- Never accept "tests should pass". Ask for the real output, then run it yourself.

## Review checklist for every ticket
- Does the diff touch only the ticket's scope?
- Did it run the commands, and did I reproduce the result?
- Any secret, URL or document text in logs/code?
- Does app/core still import nothing forbidden?
- Are new decisions recorded in docs/DECISIONS.md?

## When to bring work back to this chat
After each milestone (M1, M2, ...): paste the final report, real test output and key diffs for architectural review,
and I will write the next ticket prompts (including the exact payload contracts for the upcoming phase).

## Before specific milestones
- Before T06: create a Supabase project; check its JWT verification settings (decision O3).
- Before T25: choose the LLM provider (O1) and set its API key in server env only.
- Before M8: choose hosting (O2).
