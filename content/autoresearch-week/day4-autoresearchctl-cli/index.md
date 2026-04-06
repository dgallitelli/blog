---
title: "autoresearchctl — Ship the Loop as a CLI"
date: 2026-04-02
tags: ["autoresearch", "CLI", "tools"]
series: "Autoresearch Week"
summary: "A pip-installable CLI that bakes the seven principles, dual eval harness, and six mutation operators into six verbs: init, eval, run, log, diff, rollback."
---

> *This is Part 4 of 5 in the Autoresearch Week series.*

This week I broke down the autoresearch pattern (Monday), ported it to SageMaker (Tuesday), and generalized it beyond ML training with binary criteria and seven principles (Wednesday). Each step moved the pattern forward — but each required a different setup: GPU fleet, Kiro Power, specific IDE.

Today I'm shipping the tool that makes the pattern accessible to anyone with a terminal: **autoresearchctl**.

It's a pip-installable CLI that bakes the seven principles from Day 3, the dual eval harness (command + LLM judge), and the six mutation operators into a single tool. Six verbs: `init`, `eval`, `run`, `log`, `diff`, `rollback`. Works standalone or as the backend for any AI agent.

**Repo**: [github.com/dgallitelli/autoresearchctl](https://github.com/dgallitelli/autoresearchctl)

## Why a CLI?

Every implementation this week required a different setup. The SageMaker version needs AWS credentials and a GPU fleet. The Kiro Power needs Kiro. If you just want to try the pattern on a docs folder or a system prompt, you need something simpler.

```bash
pip install autoresearchctl
autoresearchctl init
# edit .autoresearch/config.yaml
autoresearchctl run --cycles 10
```

That's it. No cloud resources, no IDE plugin, no agent session. Define your target, define your criteria, run the loop.

## The Six Verbs

I spent time stress-testing each command to make sure it earns its place. No forced kubectl metaphors — every verb does something the others can't.

```bash
autoresearchctl init           # Scaffold config template
autoresearchctl eval           # Measure current state
autoresearchctl run            # Execute the optimization loop
autoresearchctl log            # Score trends + operator analysis
autoresearchctl diff 0 5       # Compare artifacts between runs
autoresearchctl rollback 3     # Restore to a previous state
```

**`eval`** is the one worth explaining. It runs all criteria against the current state without mutating anything — a dry measurement. Use it to validate that your criteria work before committing to a full run, or to measure your manual edits against the same bar the loop uses.

**`rollback`** exists because criteria are imperfect. The ratchet only moves forward during a run, but your human judgment might say run 12 was better than run 18 even if the score disagrees. Rollback lets your taste override the metrics.

## Config as Code

Everything lives in `.autoresearch/config.yaml`:

```yaml
target: "docs/*.md"
criteria:
  - name: title_length
    type: command
    check: '[ $(wc -c < {file}) -lt 60 ]'
  - name: has_clear_purpose
    type: llm_judge
    check: "Does the doc clearly state its purpose?"
mutator: rule-based     # or "llm"
evaluator: local         # or "bedrock" or "anthropic"
model_id: us.anthropic.claude-sonnet-4-6
max_cycles: 20
plateau_threshold: 3
```

Two eval types in one config. **Command evals** are shell commands — deterministic, free, fast. **LLM judge evals** call Bedrock (or Anthropic, when implemented) — for criteria that require understanding. The `evaluator` field controls the backend; `model_id` is shared across the LLM judge and the LLM mutator.

The `--model`, `--mutator`, and `--evaluator` CLI flags override config values, so you can experiment without editing YAML:

```bash
# Full LLM mode: Bedrock judges + LLM-powered mutations
autoresearchctl run \
  --mutator llm \
  --evaluator bedrock \
  --model us.anthropic.claude-sonnet-4-6
```

## A Real Run

Here's `autoresearchctl` optimizing 5 documentation pages for SEO compliance — the same test case from Day 3, now running through the CLI:

```
$ autoresearchctl eval
File                  title_length  meta_desc  single_h1  links
---------------------------------------------------------------
advanced-usage.md             PASS       FAIL       PASS   FAIL
api-reference.md              FAIL       FAIL       FAIL   FAIL
configuration.md              FAIL       FAIL       FAIL   FAIL
getting-started.md            PASS       PASS       PASS   PASS
troubleshooting.md            PASS       PASS       FAIL   PASS
---------------------------------------------------------------
Score: 9/20 (45%)
```

Nine of twenty checks pass. Now the loop (non-improving cycles omitted):

```
$ autoresearchctl run --cycles 6
BASELINE: 9/20 (45%)
Cycle 1 [add_constraint]:       12/20 IMPROVED
  + added meta descriptions to 3 docs
Cycle 3 [add_negative_example]: 15/20 IMPROVED
  + demoted extra H1s to H2 in 3 docs
Cycle 6 [add_counterexample]:   18/20 IMPROVED
  + added internal links to 3 docs

Final score: 18/20 (90%)
```

45% to 90% in 6 cycles. Zero LLM calls — all four criteria are shell commands. Then I checked what actually changed:

```
$ autoresearchctl diff 0 best
--- run-0000/docs/api-reference.md
+++ run-0006/docs/api-reference.md
+---
+description: "Runs all criteria against..."
+---
-# API Reference
+## API Reference
-# Core Module
+## Core Module
```

The diff makes the changes concrete. Every score improvement maps to a specific edit.

## Governance Is Built In

The loop wants to run forever. Left unconstrained, that's great for metrics and dangerous for everything else. `autoresearchctl` has three structural safeguards:

- **`max_cycles`** — hard stop after N iterations
- **`plateau_threshold`** — stop after N cycles with no improvement (default: 3)
- **`rollback`** — revert to any previous state when criteria don't capture what you actually care about

These are enforced in the loop logic, not written in a prompt the agent might ignore. The loop stops structurally, not advisorily.

One thing the CLI doesn't do: parallel hypothesis testing. Day 2's SageMaker orchestrator launches N experiments simultaneously; `autoresearchctl` runs sequential cycles. For local optimization (docs, prompts, configs), sequential is fine — each cycle takes seconds. For GPU-bound ML training, use the SageMaker version.

## What's Next

`autoresearchctl` gives you the pattern locally. But what about running it across 10 projects simultaneously? What about team visibility, cost governance, and audit trails? What about non-technical users who want a dashboard instead of a terminal?

**Tomorrow**: I'll share the architecture for autoresearch-as-a-service — a serverless platform on AWS that takes this CLI to enterprise scale with Step Functions orchestration, budget controls, and a React dashboard. We'll also step back and ask the bigger question: what happens when optimization loops become the default way teams improve their artifacts?

---

*This is Part 4 of 5 in the Autoresearch Week series. [Part 1](../day1-the-autoresearch-pattern/) | [Part 2](../day2-autoresearch-on-sagemaker/) | [Part 3](../day3-beyond-ml-training/)*

*Code: [autoresearchctl](https://github.com/dgallitelli/autoresearchctl)*
