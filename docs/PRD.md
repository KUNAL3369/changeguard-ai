# PRD — ChangeGuard AI (refined MVP)
> Subordinate to docs/PROJECT_UPDATE.md where they conflict.

## Problem
AI developers change prompts, models, schemas and retrieval. A change that fixes one document can
break another (e.g. better vendor names but wrong totals). Without a repeatable dataset and
comparison, regressions are found after deployment. Existing tools offer broad tracing/evals;
this project does one narrow thing: **Replay → Evaluate → Compare → Explain → Decide.**

## Users
Primary: Applied AI engineer / developer maintaining an invoice or document-extraction workflow.
Secondary: small AI teams, AI implementation consultants, technical founders.
Persona: maintains an invoice extractor, changes a prompt, needs to know what else broke without
manually reviewing every PDF.

## MVP scope
IN: text-layer synthetic PDF invoices; fields invoice_number, vendor_name, invoice_date, currency, subtotal,
tax_amount, total_amount (see PROJECT_UPDATE.md; RAG and other document types are post-MVP); one LLM provider behind an adapter + a mock
provider; deterministic evaluators; baseline/candidate comparison; severity; release policy;
Markdown/JSON report; CLI; GitHub Action; minimal UI; one deployment.
OUT: see CLAUDE.md "Out of scope".

## User journey
1. Create project. 2. Upload invoice PDFs. 3. Enter expected values per test case (or import
generated ground truth). 4. Create an immutable dataset version (with field_specs).
5. Register workflow versions (provider, model, prompt, schema, config; no secrets).
6. Start an evaluation run (dataset version + workflow version) → background worker executes.
7. Compare two completed runs on the same dataset version.
8. Inspect failures: document, expected vs baseline vs candidate, evidence, evaluator reason.
9. Apply release policy → PASS / FAIL / REVIEW_REQUIRED with per-rule explanation.
10. CLI/GitHub Actions runs steps 6–9 and returns an exit code.

## Functional requirements (condensed; refinements from review applied)
FR-01 Project CRUD (archive instead of hard delete).
FR-02 PDF upload; original preserved; sha256 dedupe per project.
FR-03 Dataset versioning: immutable; pins exact expected_output versions; runs reference the exact version used.
FR-04 Workflow versions: immutable configuration snapshot; prompt hash; no credentials.
FR-05 Evaluation execution: per-case raw + normalized output, errors, latency, tokens/cost when available;
      explicit run states; bounded concurrency; transient-error retries (max 2) recorded.
FR-06 Evaluators: exact, normalized string, numeric tolerance, date, required, JSON schema, custom rule.
FR-07 Comparison: per (case, field) classification with precedence rules (EVALUATION_ENGINE.md).
FR-08 Severity configurable per field via dataset-version field_specs.
FR-09 Evidence: LLM returns quote+page; we verify the quote exists in extracted page text.
      Verified → show; unverified → labeled "unverified". Never fabricate. No bounding boxes in MVP.
FR-10 Release policy: declarative rules, each with on_fail = fail | review. Backend is authoritative.
FR-11 Report (Markdown + JSON): project, dataset/workflow versions, counts, pass rate, regressions,
      critical regressions, execution errors, latency, cost if known, decision, per-rule reasons, failure details.
FR-12 CLI + GitHub Actions sample; stable exit codes (0 pass, 1 fail, 2 error/config, 3 review required).

## Non-functional requirements
Reliability: explicit run states; failures never silent; reruns create new runs.
Reproducibility: store dataset version, workflow version, provider+model actually used, evaluator
version, app version. Exact LLM output reproducibility is NOT guaranteed by providers; document this.
Security: see ARCHITECTURE.md. Performance: 10–100 cases per run, bounded concurrency (engineering
targets, not measured claims). Maintainability: modular monolith, typed schemas, migrations, tests.

## MVP acceptance criteria
1 create project; 2 upload invoice PDFs; 3 enter expected values; 4 create dataset version;
5 register workflow version; 6 run evaluation; 7 field-level evaluation; 8 compare baseline/candidate;
9 a deliberately introduced regression is detected; 10 failed field inspectable with evidence;
11 critical regression causes FAIL; 12 report generated; 13 CLI runs an evaluation;
14 GitHub Actions executes the release check; 15 automated tests cover core logic;
16 deployed and verified live.
Most important demo: a controlled regression the platform detects (docs/SAMPLE_DATA.md).

## Definition of done (portfolio-ready)
All acceptance criteria verified with evidence, migrations work, tests pass, deployment works,
README documents architecture AND limitations, no invented claims.

## What not to claim
Production adoption, customers, revenue, guaranteed correctness, detection of every regression,
universal model evaluation, unmeasured accuracy gains or savings. This is a simulated developer tool
unless real users exist. Report only: number of test cases, field pass rate, critical regression
count, execution failures, latency, cost where calculable, comparison results, and the dataset/method.
Portfolio headline may be used only after the features work: "Built an AI workflow change-impact
testing system that compares prompt/model versions, identifies field-level regressions in document
extraction, and blocks releases when configured quality requirements fail."

## Future (not MVP)
RAG retrieval evaluation, citation checks, multiple providers, more document types, evaluator
plugins, dataset import/export, scheduling, trace ingestion (prefer integrating Langfuse over rebuilding),
teams, richer policies. Also: later reuse for Forward Deployed Engineer work: per-customer datasets and policies.
