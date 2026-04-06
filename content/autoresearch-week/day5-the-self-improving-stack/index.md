---
title: "The Self-Improving Stack — From CLI to Platform to Paradigm"
date: 2026-04-03
tags: ["autoresearch", "platform", "architecture"]
series: "Autoresearch Week"
summary: "The teams that win in the agentic era won't have the best agents — they'll have the best optimization loops and the governance to trust them. Here's the full platform design and the argument for why the eval is the product."
---

> *This is Part 5 of 5 in the Autoresearch Week series.*

This week started with a question: what's missing from Karpathy's autoresearch (Day 1)? From there I built a SageMaker port for GPU fleets (Day 2), a Kiro Power that generalizes the pattern beyond ML (Day 3), and a pip-installable CLI called `autoresearchctl` (Day 4). Each step moved up the abstraction ladder: local GPU → managed fleet → generalized pattern → CLI tool.

But this final post isn't just about architecture. It's about what happens when optimization loops become the default way teams improve their artifacts. The platform design is the vehicle for a bigger argument.

## The Platform: Autoresearch-as-a-Service

Yesterday's `autoresearchctl` works great for a developer at a terminal. It doesn't work for:

- **Multiple concurrent projects** — you need one terminal per loop
- **Team visibility** — nobody else can see what the loop is doing
- **Non-technical users** — prompt engineers shouldn't need to learn CLI tools

The platform is a serverless architecture on AWS that wraps the same loop in a dashboard:

```
+-----------------------------------------+
|  React SPA (S3 + CloudFront)            |
|  Dashboard | Project Wizard | Detail    |
+--------------------+--------------------+
                     |
                     v
+--------------------+--------------------+
|  API Gateway (REST) + JWT auth          |
+--------------------+--------------------+
                     |
                     v
+--------------------+--------------------+
|  Step Functions State Machine           |
|  Init -> Reason -> Execute -> Evaluate  |
|  Budget check per iteration             |
+--------------------+--------------------+
                     |
                     v
+--------------------+--------------------+
|  DynamoDB (metadata, cost ledger)       |
|  S3 (variants) | Git (commits, PRs)    |
+--------------------+--------------------+
```

Everything serverless. You pay only when experiments are running.

## Why Step Functions Over a Persistent Agent?

The core of the platform is a Step Functions state machine — not a long-running Claude Code session in a container. Three reasons:

**Cost.** A persistent agent consumes LLM tokens continuously — reading files, reasoning about context, deciding what to do next. Step Functions calls Bedrock only when needed: once per cycle for reasoning, plus N calls for LLM judge criteria. Between cycles, nothing is running.

**Observability.** Step Functions gives you a visual execution graph in the console — which state the loop is in, how long each step took, inputs and outputs at each boundary. With a persistent agent, you'd build this yourself with OpenTelemetry and a custom dashboard.

**Reliability.** A persistent agent can crash, lose context, or hallucinate after 30+ cycles (principle #4 from Day 3: "files are truth, not memory"). Step Functions state machines are durable by design. If a Lambda times out, the Map state catches it. The DynamoDB experiment history and git commits provide checkpoints for re-execution.

A skeptical architect might push back: "I can add a token counter, OpenTelemetry, and a supervisor process to a container-based agent." Fair point. The real argument is that the autoresearch loop is *structurally simple* — a fixed sequence of steps with clear inputs and outputs. You're not giving up expressiveness because the loop doesn't need it. For exploratory research requiring multi-file reasoning, you'd still want a full agent. For the constrained optimization loop, the state machine is the right abstraction.

## Governance Through Data

`autoresearchctl` has structural safeguards — `max_cycles`, `plateau_threshold`, `rollback`. The platform version goes further with a **Cost Ledger**: a DynamoDB table recording every Bedrock call and Lambda execution with its estimated cost. The BudgetCheck step queries it before each cycle. If cumulative cost exceeds `max_cost_usd`, the loop stops. The dashboard shows real-time spend per project.

When the loop terminates, it creates a pull request with a summary: total experiments, best metric, cost breakdown, winning hypothesis. The PR is the audit trail.

This platform is a design document, not a shipped product — I'm publishing the full spec (1,166 lines) for anyone who wants to build on it. But the architecture matters less than what it represents.

## The Week's Arc

Day 1 identified five gaps in Karpathy's autoresearch. Here's where they stand:

```
Gap                Day   Status
---------------------------------------------------
1. Fleet compute   2     Shipped (SageMaker)
2. Cost visibility 2     Shipped (per-job estimates)
3. Parallelism     2     Shipped (N-job parallel)
4. Governance      4+5   Partial (CLI safeguards
                         shipped, Cost Ledger designed)
5. Generalization  3     Shipped (binary criteria)
```

Four shipped, one designed. Honest accounting. But closing gaps isn't the point. The point is what the pattern enables at scale.

## The Self-Improving Stack

Here's my thesis: **the teams that win in the agentic era won't be the ones with the best agents. They'll be the ones with the best optimization loops and the governance to trust them.**

When you zoom out from individual tools, a layered architecture emerges:

```
Layer          What it does
---------------------------------------------------
Runtime        Where it runs (autoresearchctl,
               Kiro Power, Step Functions, SageMaker)

Governance     What constrains the loop (budgets,
               plateau detection, rollback, audits)

Optimization   How artifacts improve (autoresearch
               loop: mutate -> evaluate -> keep)

Evals          How we measure quality (binary
               criteria, command + LLM judge)

Artifacts      What you optimize (docs, prompts,
               configs, skills, code)
```

Runtime at the foundation. Governance wraps optimization. Optimization is driven by evals. Evals judge artifacts. Each layer constrains the one above it: governance stops the loop when budget is exhausted, evals revert changes that fail criteria.

In traditional software engineering, you have code → tests → CI/CD → policy → infrastructure. Same pattern. The difference: the optimization layer is autonomous. It runs without human intervention. The system can improve itself faster than humans can review the improvements. This is why governance isn't a nice-to-have — it's the layer that determines whether the stack is trustworthy or dangerous.

## Three Risks I've Hit

**Score gaming.** An LLM judge evaluated code review quality on a 1-5 scale. Over 30 cycles, the agent learned to produce verbose outputs that scored 4.5+ by covering every possible issue — including hallucinated ones. Binary criteria (Day 3, principle #5) fixed this. `autoresearchctl` enforces binary by design.

**Drift.** A file that's been through 50 cycles may look nothing like the original. If cycle 23 introduced a subtle behavior change that no criterion catches, it propagates through every subsequent cycle. `autoresearchctl diff 0 50` and `rollback` exist specifically for this. Snapshots at every cycle make drift visible and reversible.

**Cost runaway.** An overnight loop with LLM judges on every criterion can burn hundreds of dollars. The loop doesn't know money exists unless you tell it. Budget enforcement must be structural — checked before each cycle in code — not advisory, written in a prompt the agent might ignore.

## The Eval Is the Product

Karpathy called this the "loopy era." I think the more precise framing is: we've entered the era where **the eval is the product.**

The agent that mutates code is commodity — Claude, Codex, Kiro, they all do it. The runtime is commodity — CLI, Step Functions, SageMaker, pick your substrate. The mutation operators are mechanical. None of these are your competitive advantage.

The eval criteria — the binary gates that determine what "better" means — are where human judgment lives. Taste, direction, domain expertise. The things an agent can't generate for itself. Write better evals and you get better agents. Write lazy evals and the loop optimizes for the wrong thing (see: score gaming above).

This is true at every layer of the stack. Better criteria produce better artifacts. Better governance produces trustworthy optimization. Better runtime produces faster iteration. But it all starts with the eval.

If you want to try the pattern this weekend: `pip install autoresearchctl`, define 3-5 binary criteria for any file in your project, and run 10 cycles (see [Day 4](../day4-autoresearchctl-cli/) for the full walkthrough). Look at what the loop changes — the mutations reveal quality dimensions you didn't know you cared about.

It's turtles all the way down — except at the bottom, there's a human deciding what matters.

---

*This is Part 5 of 5 in the Autoresearch Week series. [Part 1](../day1-the-autoresearch-pattern/) | [Part 2](../day2-autoresearch-on-sagemaker/) | [Part 3](../day3-beyond-ml-training/) | [Part 4](../day4-autoresearchctl-cli/)*

*All code is open source: [autoresearchctl](https://github.com/dgallitelli/autoresearchctl) | [sagemaker-autoresearch](https://github.com/dgallitelli/sagemaker-autoresearch) | [kiro-power-autoresearch](https://github.com/dgallitelli/kiro-power-autoresearch)*
