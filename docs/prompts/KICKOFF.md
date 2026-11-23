# Kickoff prompt (send this first in Claude Code)

```
You are my coding agent for ChangeGuard AI, a portfolio project: an AI workflow regression-testing and release-gating
tool for invoice extraction (FastAPI + PostgreSQL + React later). I work ~2 hours/day, so every task must fit one session.

READ, in this order: CLAUDE.md, docs/PROJECT_UPDATE.md (wins on scope conflicts), docs/PRD.md, docs/ARCHITECTURE.md,
docs/DECISIONS.md, docs/BACKLOG.md, docs/prompts/M1.1-M1.2.md.

DO NOT write or change any code yet.

Reply with:
1. A 10-line summary of the project and its MVP boundaries in your own words.
2. Conflicts, ambiguities or risks you found in the docs (be specific; cite file and section).
3. The open decisions you must NOT decide without me.
4. Your inspection of the current repo (files, git state, new vs existing).
5. Your plan for tickets T01–T02 ONLY, following docs/prompts/M1.1-M1.2.md: files to create, order of work, tests, and the
   exact verification commands.

Then STOP and wait for my approval. Do not start T03 or later, and do not add authentication, frontend, evaluation logic
or release gating. Never claim anything works unless you ran it and show the real output.
```

## After you review the plan, send:
```
Approved. Implement T01–T02 on branch m1-foundation. Follow CLAUDE.md rules and the final report format. Do not commit
until I review the diff. Update docs/PROGRESS.md and the Commands section of CLAUDE.md with only verified commands.
```

## After the implementation, send:
```
Now run every acceptance criterion from docs/prompts/M1.1-M1.2.md yourself, including stopping and restarting the database
to check /ready, and paste the real output. List anything you could not verify.
```
Then run the commands yourself and bring the final report + real output to the ChatGPT/Claude planning chat for review.
