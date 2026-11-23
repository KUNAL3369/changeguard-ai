# PROJECT UPDATE 001 — latest source of truth

Where this file conflicts with other docs, THIS FILE WINS for positioning, differentiation, initial use case,
MVP boundaries and portfolio priority. (Other docs have been reconciled; see table at the bottom.)

## Positioning
ChangeGuard AI is the FIRST major portfolio project. It is an AI workflow regression-testing and release-gating
tool for document extraction (RAG is a later extension, not MVP). Its value is not "evaluating an LLM response";
it is deciding whether a workflow change is SAFE TO RELEASE.

Do NOT recreate: Langfuse, LangSmith, Braintrust, Arize Phoenix, Promptfoo, DeepEval, Ragas.
Focus: document-workflow change-impact testing.

## Central demonstration
A developer changes an invoice-extraction prompt. Vendor name improves but totals break. ChangeGuard:
runs the baseline and candidate on the same versioned dataset, compares expected vs actual, classifies fields
(regressed / improved / unchanged), shows evidence when available, applies a release policy, returns
PASS / FAIL / REVIEW_REQUIRED. Also demonstrate an IMPROVEMENT scenario.
**The regression must be reproducible. Never depend on an LLM randomly failing during the demo.**

## Initial workflow
Invoice extraction only. Synthetic invoice PDFs, clearly labelled synthetic (never imply real customers).
MVP fields: invoice number, vendor name, invoice date, currency, subtotal, tax, total.
(PO number is NOT an MVP field; it may appear on sample invoices only as a distractor.)
No other document categories until invoice works end to end.

## Explicitly out of scope
General LLM observability, replacing Langfuse/LangSmith, prompt playground, model marketplace, multi-agent
orchestration, general tracing SDK, multi-tenant SaaS (orgs/teams), many document types, complex distributed infra,
Redis/Celery/Kubernetes/microservices (unless a demonstrated requirement appears).
Note: per-user ownership checks (`owner_id`) are access control, not multi-tenancy, and stay.

## Execution rules
- Foundation milestone first; review and verify it BEFORE authentication, frontend, evaluation logic or release gating.
- Build incrementally; verify each milestone; add tests with features; keep evaluation deterministic.
- Use synthetic data and disclose it. Do not invent adoption, accuracy figures, performance gains or business impact.
- Do not add features to lengthen the technology list. A working end-to-end product beats many unfinished features.
- Do not redesign or broaden scope without a clear reason; ask first.
- Provider API keys never go in workflow records; environment variables or a secret store only.

## Portfolio roadmap (context only; do not build Project 2 now)
1. ChangeGuard AI (now). 2. Business Support Resolution Agent (after ChangeGuard): support-ticket resolution, order
lookup, refund eligibility, human approval, audit history; shows tool calling, controlled actions, FDE skills.
Improve/document existing projects instead of adding unrelated ones. No standalone doc Q&A app, no standalone
multi-agent research desk, no standalone SSO app (add auth/audit to an existing project if relevant).

## Reconciliation with earlier docs
| Topic | Earlier docs | Resolution |
|---|---|---|
| RAG | In positioning line of update; "future" in PRD | RAG is post-MVP |
| Fields | PRD listed po_number | Removed from MVP fields |
| Severity | critical/high/medium/low | Keep four levels (update says "such as"); medium optional |
| Demo reproducibility | "tune live prompt and measure" | Demo uses a deterministic `replay` provider (ADR-014) |
| Auth timing | T06 inside M1 | Moved to start of M3, after the M1/M2 review (ADR-015) |
| Supabase | Auth + storage | Still "may be used"; storage adapter also gets a local-disk implementation for dev/tests |
