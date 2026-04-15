---
title: "The AWS Playbook: From AgentCore to Agent Registry"
date: 2026-04-15
tags: ["agentic-AI", "platform-engineering", "AWS", "AgentCore", "agent-registry", "enterprise-AI"]
series: "Platform Engineering for AI Agents"
summary: "AWS has been building the managed infrastructure for agentic AI at enterprise scale — from AgentCore's runtime and governance services to the newly announced Agent Registry. Here's how the pieces fit together, what a real production deployment looks like, and where the gaps remain."
---

*The AWS-opinionated view: how Amazon Bedrock AgentCore and the new Agent Registry map to the platform engineering challenges from [Part 1](../part1-the-production-gap/) and [Part 2](../part2-the-platform-engineering-playbook/), grounded in a real enterprise case study.*

> **TL;DR:** AWS's AgentCore platform maps directly to the "agents on / agents in" architecture from Part 2. Thomson Reuters achieved 15x productivity gains and 70% automation by building on it — but had to custom-build the governance layer themselves. The new Agent Registry (preview, April 2026) closes that gap. Start by writing a one-page "agent contract" for your first workflow before evaluating any tooling. If you can't fill it in, you're not ready to build — and that's the most valuable information you can have.

![Illuminated control room with multiple monitoring screens](https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1200&auto=format&fit=crop&q=80)
*Photo by [Jordan Harrison](https://unsplash.com/@jordanharrison) on [Unsplash](https://unsplash.com)*

In [Part 1](../part1-the-production-gap/), we examined why the production gap exists — the 12:1 ratio between AI experimentation and operational deployment, and why it's an infrastructure problem, not a model problem. In [Part 2](../part2-the-platform-engineering-playbook/), we laid out the technical architecture: the "agents on / agents in" framework, the vendor landscape, the protocols, and the governance requirements that platform teams need to address.

This post takes an opinionated turn. AWS has been building a managed platform that directly addresses the infrastructure gaps we described — and a recent enterprise case study at Thomson Reuters shows what production deployment actually looks like when you build on it. The views here are my own, informed by work in this space, and not a statement on behalf of AWS.

## Before You Build: What Makes Work "Agent-Shaped"

Before mapping the platform stack, it's worth grounding in the operational framework that determines whether any platform investment pays off. AWS's Generative AI Innovation Center developed this after working with over a thousand enterprise customers. The GenAI Innovation Center published a [two-part series on operationalizing agentic AI](https://aws.amazon.com/blogs/machine-learning/operationalizing-agentic-ai-part-1-a-stakeholders-guide/) that identifies a consistent failure pattern: organizations with impressive pilots that never leave the lab tend to share the same structural problems — vague use case definitions, autonomy that outpaces controls, and no shared definition of what success looks like.

Their core insight: don't start with "where can we use an agent?" Start with "where is the work already structured like a job an agent could do?" That requires four conditions to be true simultaneously:

**Clear start, end, and purpose.** The agent must recognize when it has enough information to begin, what goal it's working toward, and when the task is complete or needs handoff. If the team can't articulate what "done well" looks like — including edge cases — the work isn't ready.

**Judgment across tools.** The agent reasons about what information it needs, decides which systems to query, and determines the right action based on context. Critically, the tools must exist: well-defined, secure, and reliable interfaces the agent can call. If the current process runs in email and spreadsheets, there's both process design and tooling work to complete before an agent is viable.

**Observable, measurable success.** Someone outside the team can verify the output. Beyond output quality, the reasoning trace must be inspectable: what data the agent used, what tools it called, what options it considered, and why it chose one over another.

**A safe failure mode.** Early agent candidates should have mistakes that are caught quickly, corrected cheaply, and don't create irreversible harm. As trust, controls, and evaluation mature, you earn the right to move into higher-stakes work where the agent closes the loop autonomously.


This diagnostic is worth internalizing before evaluating any platform investment. The most common failure mode the Innovation Center observes isn't technology selection — it's starting from "we want to deploy an agent" and working backwards, leaving the success definition abstract ("it should handle customer queries better") rather than operational ("resolution rate above 82%, escalation within 4 hours, no legal exposure on these 12 topic categories"). That abstraction is tolerable in a demo. In production, it means you can't evaluate, improve, or defend the agent when something goes wrong.

## Who Makes This Work: Cross-Functional Accountability

The GenAI Innovation Center's [second post in the series](https://aws.amazon.com/jp/blogs/machine-learning/agentic-ai-in-the-enterprise-part-2-guidance-by-persona/) assigns distinct responsibilities to each leadership role. The underlying logic: agentic AI fails not because any one person made the wrong call, but because the roles never aligned on a shared operating model. A few framings are worth internalizing for what follows.

**For the CTO or Chief Architect** — The core question is whether you want ten impressive one-off agents or a platform that can support a hundred agents safely. The system path requires early investment: standardizing how tools are exposed, separating planning from execution in agent design, capturing decision traces consistently, and treating agents as long-lived services with identities, permissions, lifecycle management, and upgrade paths. That's more work upfront — but it's what allows you to say yes to the tenth team requesting an agent without starting from scratch.

**For the CISO** — Agents aren't applications. They're closer to colleagues: they have accounts, roles, and tools they can use, and they can make mistakes at machine speed. The practical response is to assign non-human identities to agents with the same rigor applied to human identities — individual credentials, scoped permissions, and a dedicated audit trail. Kill switches must actually work. Policies that require human approval for certain action classes should be enforced at the tool level, not in the agent's prompt.

**For the Chief Data Officer** — Agents amplify whatever data foundation exists. If that foundation is fragmented and undocumented, agents make those problems visible to everyone, quickly. The CDO's job in the agentic era is to make the data "boring in the best possible way" — consistent definitions, documented lineage, clear domain readiness.

**For the Chief AI / Data Science Officer** — In production, the real product isn't the model — it's the evaluation system wrapped around the model. Agents fail in ways benchmarks don't measure: loops, incorrect tool calls, half-completed tasks that look plausible. A mature evaluation system turns real production failures into test cases, runs automatically on every change, and measures what the business cares about.

Each of these personas maps directly to specific AgentCore services — which is what makes the platform story coherent rather than just a feature list. The CTO's "sturdy floor" maps to Runtime and Gateway. The CISO's non-human identity requirement maps to AgentCore Identity and Policy. The CDO's data readiness maps to Memory and Gateway's tool connectivity. The AI Officer's evaluation system maps to AgentCore Evaluations and Observability.

The most recurring friction pattern across enterprise teams is the CDO–CTO misalignment: the CTO wants to ship the first agent in four weeks; the CDO knows that the data domain the agent needs is inconsistently defined across three source systems. Neither is wrong. The practical resolution is to sequence around data readiness — start with the workflow where the data is already clean, consistent, and well-understood, even if it's not the most strategically exciting. A working agent on a "boring" workflow builds more organizational trust than a stalled agent on the right one.

Let's see how this plays out in practice.

## What Production Looks Like: Thomson Reuters and Aether

Thomson Reuters' Platform Engineering team is one of the most instructive enterprise examples to date — not because the technology is exotic, but because it demonstrates both the value ceiling and the implementation cost of building agentic infrastructure on a managed platform.

Their challenge was classic enterprise platform engineering: supporting multiple product teams with cloud infrastructure and enablement services — account provisioning, database patching, network configuration, compliance review — through processes that were labor-intensive, repetitive, and required repeated cross-team coordination.

> "Our engineers were spending considerable time answering the same questions and executing identical processes across different teams. We needed a way to automate these interactions while maintaining our security and compliance standards."
>
> — Naveen Pollamreddi, Distinguished Engineer, Thomson Reuters

Their solution, [built on Amazon Bedrock AgentCore](https://aws.amazon.com/blogs/machine-learning/how-thomson-reuters-built-an-agentic-platform-engineering-hub-with-amazon-bedrock-agentcore), deployed multiple specialized agents — for cloud account provisioning, database patching, network services, and architecture review — coordinated by a central orchestrator named Aether. The architecture followed what is now a recognizable enterprise agentic pattern:

- A **custom web portal** for natural language interaction, authenticated against TR's enterprise SSO
- A **central orchestrator agent** (Aether) built on LangGraph, routing requests and managing interactions
- **Specialized domain agents** handling cloud account provisioning, database patching, network configuration, and architecture review
- A **human-in-the-loop validation service** (Aether Greenlight) for sensitive operations, with audit trails supporting ITIL compliance

The outcomes were material: a **15x productivity gain** through intelligent automation of routine tasks, and a **70% automation rate** at first launch. But what's instructive for platform leaders is what TR had to *build themselves* to get there — and what they didn't have to.

### What AgentCore Provided

AgentCore served as the foundational orchestration layer, providing the core agentic capabilities: Runtime for managed execution, Memory for maintaining conversation context (short-term within sessions, long-term for user preferences and interaction patterns), and Gateway for secure tool connectivity. TR's developers could focus on business logic rather than infrastructure plumbing — the framework handled connection management, tool orchestration, and baseline agent setup.

### What TR Built on Top

The custom engineering investment is where the story gets interesting for platform teams:

- **A custom A2A agent registry** on Amazon DynamoDB and Amazon API Gateway to enable agent discovery and cross-account routing — because at the time, no managed registry service existed
- **TR-AgentCore-Kit (TRACK)** — their own deployment framework that abstracts AgentCore infrastructure complexity, standardizes agent onboarding, handles compliance alignment (asset identification, resource tagging), and manages registration of service agents into the Aether environment
- **A governed approval workflow** requiring human validation before any new agent enters the production environment, with version history for auditing

These weren't product features — they were custom engineering investments by a team with a Distinguished Engineer driving the architecture. What TR's team constructed maps closely to capabilities that are now available or emerging in the AgentCore platform: the custom agent registry maps to the newly announced AWS Agent Registry, the deployment abstraction maps to patterns in the AgentCore SDK and starter toolkit, and the approval workflow maps to the governance lifecycle now built into the Registry.

The lesson: TR got to production because they were willing to build the governance and discovery layer themselves. Most organizations won't have that engineering capacity — which is exactly why the managed platform matters.

> **Key takeaway:** Thomson Reuters achieved 15x productivity and 70% automation — but had to custom-build an agent registry, a deployment framework, and an approval workflow. What they built maps closely to what AgentCore and Agent Registry now provide as managed services.

## The AgentCore Platform Stack

Amazon Bedrock AgentCore is a managed platform for building, deploying, and operating production-grade AI agents. It's model-agnostic and framework-agnostic by design — built to work with LangGraph, CrewAI, LlamaIndex, Strands Agents, and others. [AgentCore reached general availability in October 2025](https://aws.amazon.com/blogs/aws/introducing-amazon-bedrock-agentcore-securely-deploy-and-operate-ai-agents-at-any-scale/), with all services gaining VPC, PrivateLink, CloudFormation, and resource tagging support at GA.


Read as a progression, each component addresses a specific infrastructure concern that enterprises building early agentic systems have had to solve themselves. Here's how the stack maps to the "agents on / agents in" framework from [Part 2](../part2-the-platform-engineering-playbook/):

![Amazon Bedrock AgentCore — Platform Stack](images/agentcore-platform-stack.png)

### Agents *in* the Platform — The Workload Layer

These services address the challenge of running agents as production workloads:

**AgentCore Runtime** — Managed serverless execution with session isolation, supporting workloads up to 8 hours. Each user session runs in its own protected environment to prevent data leakage. This is the deployment golden path that Part 2 identified as the first platform requirement for agent workloads. Now supports bidirectional streaming for voice agents where both users and agents can speak simultaneously.

**AgentCore Memory** — Short-term conversation context and long-term user/preference persistence. TR's Aether uses both: short-term memory maintains context within individual conversations, while long-term memory tracks user preferences and interaction patterns. The recently added episodic memory capability lets agents learn from past experiences — capturing structured episodes that record context, reasoning, actions, and outcomes, then extracting broader patterns to improve future decision-making.

**AgentCore Observability** — Production telemetry integrated with Amazon CloudWatch: step-by-step visualization of agent execution, metadata tagging, custom scoring, trajectory inspection, and troubleshooting filters. This is the AI-specific observability layer that Part 2 identified as going beyond traditional APM — tracking token usage, tool call success rates, inference latency, and reasoning traces. Grupo Elfa, a Brazilian distributor, uses AgentCore Observability for complete audit traceability, achieving 100% traceability of agent decisions and reducing problem resolution time by 50%.

**AgentCore Evaluations** — [Reached general availability in March 2026](https://aws.amazon.com/blogs/aws/amazon-bedrock-agentcore-adds-quality-evaluations-and-policy-controls-for-deploying-trusted-ai-agents/). Continuously monitors agent performance using built-in evaluators for correctness, helpfulness, tool selection accuracy, safety, goal success rate, and context relevance — plus custom model-based scoring for business-specific requirements. Results feed into CloudWatch alongside Observability insights, with alerts when quality metrics drop below thresholds. This directly addresses the Chief AI Officer's mandate: evaluation as the real product.

### Agents *on* the Platform — The Connectivity and Control Layer

These services address the challenge of agents consuming platform capabilities safely:

**AgentCore Gateway** — MCP-compatible tool connectivity that transforms existing APIs and Lambda functions into agent-ready tools with zero code. Provides unified access across protocols, runtime discovery, and built-in authorization. This is the "machine-readable API" layer that Part 2 identified as the prerequisite for agents consuming the platform.

**AgentCore Identity** — Enables agents to securely access AWS services and third-party tools (GitHub, Salesforce, Slack) either on behalf of users or with pre-authorized consent. This is the CISO's non-human identity requirement made concrete — each agent gets its own credentials, permissions, and audit trail rather than inheriting a service account's rights.

**AgentCore Policy** — [Reached general availability in March 2026](https://aws.amazon.com/blogs/aws/amazon-bedrock-agentcore-adds-quality-evaluations-and-policy-controls-for-deploying-trusted-ai-agents/). Defines boundaries for agent actions by intercepting Gateway tool calls before they execute, using Cedar (an open-source policy language) for fine-grained permissions. Policies operate independently of how the agent was built or which model it uses. Natural language policy authoring makes this accessible to security and compliance teams, not just developers. This is architectural governance — enforced at the tool level, not in the agent's prompt.

**AgentCore Browser** — Managed web browser instances for agents' web automation workflows.

**AgentCore Code Interpreter** — Isolated sandbox environments for executing agent-generated code.

### The Foundation Layer

**Any model · Any framework · Any architecture.** AgentCore works with Amazon Bedrock models, third-party models, custom frameworks, and on-premises agents. The AgentCore SDK has been downloaded over 2 million times in its first 5 months.

The key architectural insight: these services can be used independently or together. A team can start with just Runtime and Gateway, add Observability when they need production telemetry, layer in Policy when governance requirements mature, and adopt the Registry when multi-team coordination becomes necessary. That modularity maps to the maturity progression that most organizations actually follow.

> **Key takeaway:** AgentCore is modular by design. Start with Runtime + Gateway for your first agent. Add Observability and Evaluations before the third. Layer in Identity, Policy, and Registry as governance needs mature. Don't buy the whole stack on day one.

## The Agent Registry: From Bespoke to Platform

[Announced on April 9, 2026](https://aws.amazon.com/blogs/machine-learning/the-future-of-managing-agents-at-scale-aws-agent-registry-now-in-preview/), the AWS Agent Registry is the newest addition to the AgentCore suite. It entered preview in five regions (US East N. Virginia, US West Oregon, Asia Pacific Tokyo, Asia Pacific Sydney, and Europe Ireland) and directly addresses the governance and discovery gap that enterprises like Thomson Reuters were forced to close with custom infrastructure.

### What It Does

The registry stores structured metadata for every agent, tool, MCP server, agent skill, and custom resource in the enterprise — capturing ownership, protocols implemented, capabilities exposed, compliance status, and invocation instructions. It supports MCP and Agent-to-Agent (A2A) protocol natively, alongside custom schemas for organizational-specific needs.

Discovery is built on hybrid search combining keyword and semantic matching: a query for "payment processing" surfaces tools tagged as "billing" or "invoicing" even if named differently. Every record follows a governed approval lifecycle — draft, pending approval, discoverable — with IAM-enforced publish and consume permissions and full audit trails via AWS CloudTrail.

Registration supports two paths: manual metadata entry via the AgentCore Console, AWS SDK, or API; or URL-based auto-discovery that pulls tool schemas and capability descriptions directly from a live MCP or A2A endpoint. Critically, the registry indexes agents regardless of where they run — AWS, other cloud providers, or on-premises. Access is available through the AgentCore Console, APIs, and as an MCP server queryable directly from IDEs including Kiro and Claude Code.

### How It Closes the Loop on the Operating Model

Return to the CTO framing from the GenAI Innovation Center series: the job is to build a sturdy floor that lets many teams ship agents safely, quickly, and consistently. Agent Registry is the missing piece of that floor that no managed service previously covered:

| Challenge | Previous State | With Agent Registry |
|---|---|---|
| **Visibility** | No central view of what agents existed; discovery via Slack or tribal knowledge | Structured catalog with hybrid semantic search; every agent, tool, and skill discoverable from console or IDE |
| **Governance** | Anyone could deploy anything; no enforced standards or lifecycle tracking | IAM-enforced publish/discover permissions; draft → approval → production lifecycle; CloudTrail audit trail |
| **Reuse** | Teams duplicated capabilities because discovery was too hard | Registry-first discovery before building; semantic search surfaces related capabilities even with different naming |
| **Multi-cloud reality** | Any registry covering only AWS left agents on other platforms invisible | Indexes agents from any provider or on-premises via URL-based discovery or manual registration |


### Early Adopters

The early adopter profiles point to two natural archetypes. [Southwest Airlines](https://aws.amazon.com/blogs/machine-learning/the-future-of-managing-agents-at-scale-aws-agent-registry-now-in-preview/) is enabling an enterprise-wide agent catalog and governance, using the Registry to solve the discoverability challenge — enabling teams to find and reuse existing agents instead of rebuilding from scratch, with standardized ownership metadata and policy enforcement. [Zuora](https://aws.amazon.com/blogs/machine-learning/the-future-of-managing-agents-at-scale-aws-agent-registry-now-in-preview/), deploying 50 agents across Sales, Finance, Product, and Developer teams, uses the Registry to give Principal Architects a unified view to discover, manage, and catalog every agent, tool, and skill in use.

Both fit the pattern: large enterprises with many distributed teams each independently building agents, facing the sprawl problem earliest and feeling the governance gap most acutely.

## What Agent Registry Does Not Yet Solve

It's worth being clear-eyed about what's still ahead, both for the Registry and for the broader platform.

**Observability integration is on the roadmap.** The most critical governance question — "is this agent actually performing correctly in production?" — isn't yet answered by the registry. AWS has indicated that operational intelligence (invocation counts, latency, uptime, usage patterns) will eventually surface alongside registry records from AgentCore Observability, but this integration isn't available today. For now, observability and discovery remain separate workflows.

**Cross-registry federation isn't yet available.** Organizations with agents spread across subsidiaries, regional business units, or multiple cloud environments can't yet connect multiple registries and query them as one. This is a disclosed roadmap item, and it will matter significantly for large, decentralized enterprises.

**Automatic indexing requires further platform integration.** The vision of agents being indexed automatically at deployment time — from AgentCore, Amazon Q, and Kiro — is forward-looking. Today, registration still requires either manual metadata entry or pointing to an endpoint. That's a reasonable starting point, but it adds operational overhead as fleet size grows.

**IaC support is a gap for production adoption.** As of April 2026, AWS Agent Registry has no CloudFormation or Terraform support. Teams that manage infrastructure-as-code from day one will need to work around this limitation during the preview period. Note that the core AgentCore services (Runtime, Gateway, Memory, etc.) *do* have CloudFormation support since GA — this gap is specific to the Registry in its preview state.

**Regional availability is limited.** The Registry is available in five regions during preview. The core AgentCore services are available more broadly (US East N. Virginia, US West Oregon, Asia Pacific Mumbai, Singapore, Sydney, Tokyo, and Europe Frankfurt, Ireland). Teams planning multi-region deployments should check the [regional availability page](https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/).

## Sequencing the Platform: A Practical Adoption Path

The right next move depends on where your organization sits. Rather than a generic maturity model, here's how to sequence AgentCore adoption against the challenges from Parts 1 and 2:

### If you're exploring (no agents in production)

Don't invest in platform infrastructure yet. The highest-leverage action is to pick one workflow, apply the GenAI Innovation Center's "agent-shaped work" diagnostic, and write the agent's job description in operational terms — what it does, what tools it needs, what success looks like, what happens when it fails. If you can't fill in that page, you're not ready to build, and that's valuable information.

When you are ready, start with **AgentCore Runtime + Gateway**. Runtime gives you a managed execution environment without building deployment infrastructure. Gateway gives your agent secure access to tools. That's enough to get a first agent into production.

### If you have one or two agents running

You're feeling the friction of ad hoc tooling: inconsistent logging, manual deployment, no shared evaluation approach. The right move is to standardize before deploying a third agent:

- Add **AgentCore Observability** from the first production deployment, not the fifth. The cost of adding tracing retroactively across a distributed agent fleet is high. The cost of including it from the start is low.
- Layer in **AgentCore Identity** to establish non-human identity patterns before they become a security debt.
- Connect **AgentCore Evaluations** to establish the evaluation habit — turning real production failures into test cases that run automatically on every change.

### If multiple teams are building independently

This is exactly the problem Agent Registry is designed for. Establish the registry as the authoritative catalog now — while the fleet is still small enough that registration is fast — and use the approval workflow to create a governance habit before it becomes necessary to enforce one.

Add **AgentCore Policy** to enforce boundaries at the tool level. The combination of Registry (what exists and who owns it) + Policy (what each agent is allowed to do) + Identity (how each agent authenticates) creates the governance triad that the CISO needs.

### If you're operating at fleet scale

The work at this stage is connecting the pieces: observability data informing registry records, evaluation metrics driving governance decisions, and cost attribution visibility across agent decision chains — the kind of visibility that finance needs to govern AI spend at scale. This is where the roadmap items — observability-registry integration, cross-registry federation, automatic indexing — will matter most. Plan for them, but don't wait for them to start building the governance foundation.

## Write the Job Description Before You Write the Code

The single highest-leverage action any platform team can take before their next agent sprint is to require a one-page "agent contract" for every new agent request: what it does, what tools it needs, what success looks like, and what happens when it fails. Not as a bureaucratic gate, but as a forcing function for the clarity that every production agent needs anyway.

This isn't process overhead — it's the diagnostic that separates agents that ship from agents that stall. Teams that do this work before building will ship faster, not slower, because they surface the hard questions (data readiness, tool availability, success criteria, failure modes) before they're embedded in code. The GenAI Innovation Center's "agent-shaped work" framework is the template. If you can't fill in that one page, you're not ready to build — and that's the most valuable information you can have before committing engineering time.

## The Key Question

Here's how the entire series connects — the two relationships from Part 1, the platform requirements from Part 2, and the AWS services that address them:

| Relationship | Failure Mode | Platform Requirement | AgentCore Service |
|---|---|---|---|
| **AI as a tool** / Agents *on* the platform | Agents generate plausible but wrong code — can't see org context | Machine-readable APIs, MCP integration, agent golden paths | Gateway, Identity, Policy |
| **AI as a product** / Agents *in* the platform | Customer-facing agents crash — no one owns reliability | Deployment runtimes, AI observability, evaluation, governance | Runtime, Memory, Observability, Evaluations |
| **Both** | Duplicate agents, no visibility, ungoverned sprawl | Discovery, lifecycle management, reuse, audit trails | Agent Registry |

Regardless of where your organization sits on this curve, the question that cuts through most of the noise is this: can you name one workflow today where you could write a complete agent job description — clear start, measurable end, required tools, success criteria, failure mode — and have every stakeholder in the room agree on it?

If yes, that's your first agent. If no, that's your first project.

The platform infrastructure — AgentCore, the Registry, the governance services — exists to make the execution tractable once you've answered that question. But no amount of platform sophistication compensates for starting without it.

---

*This is Part 3 of the Platform Engineering for AI Agents series. [Part 1: Why Your AI Program Stalls Between Pilot and Production](../part1-the-production-gap/) covers the business case. [Part 2: The Platform Engineering Playbook](../part2-the-platform-engineering-playbook/) covers the technical architecture.*

---

## Sources

1. AWS Generative AI Innovation Center: "Operationalizing Agentic AI Part 1: A Stakeholder's Guide" (March 2026) — [aws.amazon.com/blogs/machine-learning/operationalizing-agentic-ai-part-1-a-stakeholders-guide](https://aws.amazon.com/blogs/machine-learning/operationalizing-agentic-ai-part-1-a-stakeholders-guide/)
2. AWS Generative AI Innovation Center: "Agentic AI in the Enterprise Part 2: Guidance by Persona" (March 2026) — [aws.amazon.com/blogs/machine-learning/agentic-ai-in-the-enterprise-part-2-guidance-by-persona](https://aws.amazon.com/jp/blogs/machine-learning/agentic-ai-in-the-enterprise-part-2-guidance-by-persona/)
3. Thomson Reuters: "How Thomson Reuters built an Agentic Platform Engineering Hub with Amazon Bedrock AgentCore" (January 2026) — [aws.amazon.com/blogs/machine-learning/how-thomson-reuters-built-an-agentic-platform-engineering-hub-with-amazon-bedrock-agentcore](https://aws.amazon.com/blogs/machine-learning/how-thomson-reuters-built-an-agentic-platform-engineering-hub-with-amazon-bedrock-agentcore)
4. AWS: "Introducing Amazon Bedrock AgentCore" (July 2025 preview, October 2025 GA) — [aws.amazon.com/blogs/aws/introducing-amazon-bedrock-agentcore-securely-deploy-and-operate-ai-agents-at-any-scale](https://aws.amazon.com/blogs/aws/introducing-amazon-bedrock-agentcore-securely-deploy-and-operate-ai-agents-at-any-scale/)
5. AWS: "Amazon Bedrock AgentCore adds quality evaluations and policy controls" (Policy GA March 2026, Evaluations GA March 2026) — [aws.amazon.com/blogs/aws/amazon-bedrock-agentcore-adds-quality-evaluations-and-policy-controls-for-deploying-trusted-ai-agents](https://aws.amazon.com/blogs/aws/amazon-bedrock-agentcore-adds-quality-evaluations-and-policy-controls-for-deploying-trusted-ai-agents/)
6. AWS: "The future of managing agents at scale: AWS Agent Registry now in preview" (April 2026) — [aws.amazon.com/blogs/machine-learning/the-future-of-managing-agents-at-scale-aws-agent-registry-now-in-preview](https://aws.amazon.com/blogs/machine-learning/the-future-of-managing-agents-at-scale-aws-agent-registry-now-in-preview/)
7. AWS: Amazon Bedrock AgentCore — [aws.amazon.com/bedrock/agentcore](https://aws.amazon.com/bedrock/agentcore/)
8. AWS: AgentCore Identity — [aws.amazon.com/blogs/machine-learning/introducing-amazon-bedrock-agentcore-identity-securing-agentic-ai-at-scale](https://aws.amazon.com/blogs/machine-learning/introducing-amazon-bedrock-agentcore-identity-securing-agentic-ai-at-scale/)
9. AWS: AgentCore Gateway — [aws.amazon.com/blogs/machine-learning/introducing-amazon-bedrock-agentcore-gateway-transforming-enterprise-ai-agent-tool-development](https://aws.amazon.com/blogs/machine-learning/introducing-amazon-bedrock-agentcore-gateway-transforming-enterprise-ai-agent-tool-development/)
10. AWS: AgentCore Evaluations — [aws.amazon.com/blogs/machine-learning/build-reliable-ai-agents-with-amazon-bedrock-agentcore-evaluations](https://aws.amazon.com/blogs/machine-learning/build-reliable-ai-agents-with-amazon-bedrock-agentcore-evaluations/)
11. AWS: AgentCore Policy — [aws.amazon.com/blogs/machine-learning/secure-ai-agents-with-policy-in-amazon-bedrock-agentcore](https://aws.amazon.com/blogs/machine-learning/secure-ai-agents-with-policy-in-amazon-bedrock-agentcore/)
12. Forbes: "Agent Registries Become The New Battleground For Cloud Giants" (April 2026) — [forbes.com/sites/janakirammsv/2026/04/10/agent-registries-become-the-new-battleground-for-cloud-giants](https://www.forbes.com/sites/janakirammsv/2026/04/10/agent-registries-become-the-new-battleground-for-cloud-giants/)
13. SiliconAngle: "AWS previews a cloud-agnostic registry for managing agentic fleets at scale" (April 2026) — [siliconangle.com/2026/04/09/aws-previews-cloud-agnostic-registry-managing-agentic-fleets-scale](https://siliconangle.com/2026/04/09/aws-previews-cloud-agnostic-registry-managing-agentic-fleets-scale/)
14. AWS: "Enabling customers to deliver production-ready AI agents at scale" (July 2025) — [aws.amazon.com/blogs/machine-learning/enabling-customers-to-deliver-production-ready-ai-agents-at-scale](https://aws.amazon.com/blogs/machine-learning/enabling-customers-to-deliver-production-ready-ai-agents-at-scale/)
15. AWS: "Can your governance keep pace with your AI ambitions? AI risk intelligence in the agentic era" — [aws.amazon.com/blogs/machine-learning/can-your-governance-keep-pace-with-your-ai-ambitions-ai-risk-intelligence-in-the-agentic-era](https://aws.amazon.com/blogs/machine-learning/can-your-governance-keep-pace-with-your-ai-ambitions-ai-risk-intelligence-in-the-agentic-era/)
