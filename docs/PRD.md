# PRD: AI Financial Coach Agent
**Version:** 1.5
**Status:** In Progress (v1.0 + v1.5 shipped, v2.0 planned)
**Author:** Leo Cherupushpam (AI Product Manager)
**Date:** 2026-04-02
**Last Updated:** 2026-04-02 — shipped v1.5 (session history, progress tracking, action completion tracking)

---

## 1. Problem Statement

> "67% of Americans couldn't pass a basic financial literacy test. Personal finance advice is expensive ($150–$500/hr for a CFP), inaccessible, and generic."

### Root Problems
| Problem | Evidence | Severity |
|---|---|---|
| Financial advice is expensive and inaccessible | CFP costs $150–$500/hr; only 1 in 3 Americans has a financial advisor | Critical |
| Generic budgeting apps lack personalized guidance | Mint, YNAB — rules-based, no natural language coaching | High |
| Users don't act on financial data | 72% of users who track expenses still don't change behavior | High |
| Debt repayment is confusing | 43% of Americans don't know the difference between avalanche/snowball methods | Medium |

---

## 2. User Personas

### Primary Persona: "Struggling Steph"
- **Demographics:** 28–38 years old, household income $55–90K, 1–2 dependents
- **Jobs-to-be-Done:** "Help me figure out if I'm doing okay with money — and what to fix first"
- **Pain Points:**
  - Feels overwhelmed by debt + savings simultaneously
  - Has tried budgeting apps but doesn't know what to *do* with the data
  - Can't afford a financial advisor
- **Motivation:** Wants clarity and confidence, not complexity
- **Tech comfort:** Moderate — uses mobile apps daily, comfortable with chat UIs

### Secondary Persona: "Deliberate Dan"
- **Demographics:** 35–50 years old, income $100K+, planning for major life events
- **Jobs-to-be-Done:** "Give me a personalized roadmap to retire by 55"
- **Pain Points:**
  - Has data but lacks a trusted sounding board for major decisions
  - Doesn't want cookie-cutter advice
- **Motivation:** Optimization and confidence in specific decisions
- **Tech comfort:** High

---

## 3. Solution Overview

A multi-agent AI system that functions as a personal financial coach:
- Ingests financial data (CSV upload or manual entry)
- Routes analysis to three specialized agents in parallel:
  - **Budget Agent** — spending pattern analysis, category optimization
  - **Savings Agent** — emergency fund sizing, savings rate benchmarking, automation strategy
  - **Debt Agent** — payoff method comparison (avalanche vs. snowball), timeline visualization
- Synthesizes into a prioritized action plan with visual dashboards
- Maintains context across sessions (memory layer)

### What it is NOT
- Not a trading platform or investment advisor
- Not a bank or financial institution
- Not a replacement for a CFP for complex tax/estate situations

---

## 4. Project Outcomes

### 4A. Product Outcome (User Behavior Change)

> **"A user who felt overwhelmed by their finances leaves with a clear, prioritized list of 3–5 actions they can take this week — and actually takes at least one."**

This product succeeds not when it generates analysis, but when it **changes behavior**. The output is not a dashboard — it is a decision. Every design choice should reduce the distance between "I see the data" and "I know what to do next."

#### Outcome vs. Output Distinction

| Output (what we build) | Outcome (what we measure) |
|---|---|
| Budget breakdown chart | User identifies one category to cut |
| Savings allocation plan | User sets up an auto-transfer |
| Debt payoff comparison | User switches repayment strategy |
| Synthesized action plan | User completes 1+ action within 7 days |

#### 6-Month Vision
A user who runs this analysis monthly sees their budget health score improve by 15+ points, their savings rate increase by 5%+, and their debt balance decrease faster than their pre-AI trajectory. They trust the tool enough to return without being prompted.

---

### 4B. Portfolio Outcome (What This Project Demonstrates)

This project was built to showcase AI Product Management skills. Success means:

| Dimension | Demonstrates |
|---|---|
| **Problem Discovery** | Can identify real, sizable problems from research (67% financial literacy gap, $150–500/hr CFP cost) |
| **User-Centric Design** | Built 2 personas with JTBD, not just feature lists |
| **Metrics-First Thinking** | North Star metric is behavior change, not engagement or vanity metrics |
| **AI-Specific Judgment** | Explained model choice (GPT-4o), multi-agent tradeoffs, hallucination mitigation, cost per session |
| **Shipping & Iteration** | v1.0 → v1.5 progression; each version tests a hypothesis |
| **Retention Strategy** | Session history + progress tracking + action completion = measurable retention driver |
| **Technical + Product** | Code is readable, decisions are documented, PRD is the artifact (not just the app) |

#### What We're NOT Doing
- Building without a problem statement
- Vanity metrics (DAU, MAU, session count)
- Promising "AI will fix everything"
- Vague feature lists ("add memory", "improve UX")
- One-shot building without iteration

#### Success = Portfolio Reviewer Says
> *"This person understands: real problems, user behavior, how to measure product impact, AI tradeoffs, AND how to ship. They think like a PM, not an engineer."*

---

## 4. Success Metrics

### North Star Metric
**"% of users who complete at least 1 recommended action within 7 days of first session"**

Rationale: Behavior change is the product outcome — not just analysis generation.

### Supporting KPIs

| Metric | Baseline (Day 0) | Target (Day 90) | How Measured |
|---|---|---|---|
| Activation rate (upload CSV or enter data) | — | >60% of signups | App analytics |
| Advice action rate (1+ action in 7 days) | — | >35% | Self-report / follow-up session |
| Session completion rate | — | >70% | App analytics |
| Return visit rate (D7, D30) | — | D7: 40%, D30: 25% | App analytics |
| Net Promoter Score | — | >45 | In-app survey |
| Hallucination / bad advice rate | — | <2% | QA sampling (25 sessions/week) |
| Cost per session (API cost) | — | <$0.15 | OpenAI usage dashboard |

---

## 5. AI-Specific Design Decisions

### 5.1 Model Choice: OpenAI GPT-4o
- **Why GPT-4o:** Best structured output reliability on complex nested Pydantic schemas; `beta.chat.completions.parse()` gives native schema enforcement with zero framework overhead
- **Why not Gemini/ADK:** Original repo used Google ADK v0.1.0 (unstable). Switched to raw OpenAI API — every design decision is visible in code, which is better for both explainability and portfolio interviews
- **Tradeoff accepted:** Slightly higher cost per session vs. Gemini Flash; OpenAI vendor dependency
- **Revisit trigger:** If GPT-4o cost exceeds $0.15/session at scale, evaluate Gemini 2.0 Flash or Claude Haiku

### 5.2 Multi-Agent vs. Single Agent
- **Decision:** Multi-agent (3 specialized agents)
- **Why:** Budget, savings, and debt are distinct problem domains with different reasoning patterns. Specialization improves output quality.
- **Tradeoff:** Higher latency (+1.5–2s per session) and complexity vs. deeper, more accurate analysis per domain
- **Revisit trigger:** If latency complaints exceed 15% of NPS verbatims

### 5.3 Memory Strategy
- **Decision:** Session-level context only for v1; persistent memory in v2
- **Why:** Reduces privacy/compliance risk in v1 while validating core value prop
- **Tradeoff:** Each session starts fresh — users must re-upload data
- **Revisit trigger:** >40% of users re-upload identical CSV in sessions 2+

### 5.4 Hallucination Risk Mitigation
- **Risk:** Financial advice hallucinations can cause real harm
- **Mitigations:**
  1. Ground all advice on user-provided data only (no market predictions)
  2. Add explicit disclaimers on advice output ("This is not financial advice from a licensed CFP")
  3. Implement QA sampling: review 25 random sessions/week for accuracy
  4. Add confidence flags: agent outputs flagged as "high certainty" vs. "exploratory"
- **Severity:** Critical — any hallucination in this domain is a trust-destroying event

---

## 6. Feature Roadmap

### v1.0 — MVP ✅ Shipped
- [x] CSV upload + manual expense entry
- [x] 3-agent sequential analysis (Budget → Savings → Debt)
- [x] Visual dashboard (expense pie, savings bar, debt comparison chart)
- [x] Spending vs. benchmark chart (actual % vs. industry standard per category)
- [x] 4th synthesis agent — prioritized action plan (Top 5 actions this week)
- [x] Financial health banner (overall score + one-line summary)
- [x] Sample data button (instant demo, no data entry required)
- [x] Download report (full analysis as markdown)
- [x] Disclaimer + data privacy notice on every output

### v1.5 — Retention Layer ✅ Shipped
- [x] **Session history** — stores last 3 analyses as JSON locally
- [x] **Progress tracker** — compare any 2 sessions, see deltas (budget score, expenses, surplus, savings rate)
- [x] **Action completion tracking** — checkboxes to mark top-5 actions as done, completion % meter
- [x] **Tab-based navigation** — Analyze | History & Progress | Track Actions
- [x] **SessionManager class** — handles save/load of analyses
- [x] **ActionTracker class** — manages action completion state

### v2.0 — Personalization
- [ ] Persistent memory across sessions
- [ ] Goal-setting and milestone tracking (e.g., "Emergency fund: 43% complete")
- [ ] Behavioral nudges via email/notification (weekly check-in)
- [ ] Model experimentation: test Claude vs. Gemini on advice quality

---

## 7. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Hallucinated financial advice harms user | Low | Critical | Ground outputs in user data only; disclaimers; QA sampling |
| Users don't upload real data (privacy fear) | Medium | High | Clear data policy; local-only processing option in v2 |
| Low activation (users browse, don't engage) | Medium | High | Reduce friction: add quick-start template CSVs |
| API cost spike at scale | Low | Medium | Cost per session monitoring; prompt optimization |
| Regulatory risk (unlicensed advice) | Medium | High | Strong disclaimers; "educational only" framing throughout |

---

## 8. v1.5 Implementation Summary

### What We Built
**Tab 1: Analyze** — 4-agent analysis (unchanged from v1.0)
**Tab 2: History & Progress** — View past analyses, compare any 2 sessions, see deltas
**Tab 3: Track Actions** — Checkbox list of top-5 actions, completion %, completion badge

### Technical Details
- `SessionManager` class: Save/load analyses to `sessions.json`, keep last 3 only
- `ActionTracker` class: Checkbox state persisted to `actions_tracking.json`
- No backend required — everything local & privacy-preserving
- Estimated cost to run: <$0.01/session (4 GPT-4o calls)

### Hypothesis Being Tested
**H:** Users who see progress (budget score delta, expense delta) return at 2x the rate compared to one-time users.

**How we'll measure:**
- Retention rate (D7, D30) for sessions with visible progress (score ↑ 10+ points)
- vs. sessions with flat/negative progress
- Action completion rate as proxy for engagement

---

## 9. Open Questions (for next user research session)

1. Do users trust AI for financial advice, or do they need a human "in the loop"?
2. What's the biggest drop-off point — data upload, waiting for analysis, or reading results?
3. Would users pay for this? What's the WTP for Steph vs. Dan?
4. Is the 3-agent approach perceivably better than a single agent to users?
5. (Post v1.5) Does seeing progress increase re-engagement? What's the delta in D7/D30 retention?

---

## 10. v2.0 Roadmap — Personalization

### Features
- [ ] Persistent memory across browser sessions (localStorage)
- [ ] Goal-setting UI ("Save $500/mo for emergency fund by EOY")
- [ ] Progress visualization (sparkline showing 90-day trend in budget score)
- [ ] Email export of completion status + next month reminders
- [ ] Model experimentation — A/B test Claude vs. GPT-4o on advice quality

### Hypothesis
H: Users with explicit goals (e.g., "Hit 70 budget score by June") complete actions at 3x the rate of users without goals.

---

## 11. Go-to-Market Framing (for Portfolio)

**Positioning:** "The first AI coach that turns your transaction data into a prioritized financial action plan — in 2 minutes, not 2 hours."

**Target channel:** Personal finance communities (r/personalfinance, Bogleheads, YNAB subreddit)

**Portfolio story:**
- **Problem discovery**: 67% of Americans fail basic financial literacy; CFPs cost $150–500/hr
- **Solution design**: 4-agent architecture (Budget, Savings, Debt, Synthesis)
- **v1.0**: Core analysis engine + synthesis + dashboards
- **v1.5**: Retention layer (session history, progress tracking, action completion)
- **Metrics first**: North star is behavior change (% completing 1+ action in 7 days), not just engagement
- **Iteration plan**: v2.0 adds personalization (goals, email, memory)

The PRD + implementation shows both shipping speed and product thinking.

---

## 12. How to Talk About This Project (Portfolio Narrative)

### The Elevator Pitch (30 seconds)
> *"I built an AI financial coach that turns transaction data into prioritized actions. It's not just analysis — it's behavior change. I defined a north star metric (% completing 1+ action in 7 days), shipped v1.0 with 4 specialized agents, then v1.5 added session history + progress tracking to drive retention. The PR shows problem discovery, metrics thinking, and AI tradeoffs."*

### In a PM Interview (3–5 minutes)
1. **Problem:** "67% of Americans fail basic financial literacy. CFPs cost $150–500/hr, so access is the constraint."
2. **Solution:** "Multi-agent system — Budget, Savings, Debt agents each handle their domain, then synthesis agent prioritizes top 5 actions."
3. **What makes it product-focused:**
   - North star is behavior change (action completion), not engagement
   - v1.5 tests a hypothesis: progress visibility drives retention
   - Used session history + comparison UI to surface delta (score ↑10 points, expenses ↓5%)
4. **What would come next:** "v2.0 adds goal-setting. My hypothesis: users with explicit goals complete 3x more actions. We'd A/B test."

### In a Technical Interview (for PM + eng background)
- **Model choice:** "Chose GPT-4o for structured output reliability. Pydantic schemas give native enforcement."
- **Architecture:** "Agents are sequential functions, not a framework. Every decision is transparent in the code."
- **Why not build it differently:** "Could've used LangChain, but wanted every design choice visible. Better for explainability and interviews."

### What NOT to Say
- ❌ "I built an AI financial advisor" (too vague, sounds like all LLM apps)
- ❌ "It uses 4 agents so it's sophisticated" (so what?)
- ❌ "The model is GPT-4o so it's better" (better at what?)
- ✅ Say why your choices matter for the user outcome

### Red Flags to Avoid
- Don't claim the app "solves" financial literacy (it doesn't — it nudges behavior)
- Don't oversell AI as the differentiator (the retention strategy + metrics thinking is)
- Don't cite metrics you didn't actually measure (e.g., "users saved 40% on debt" — we haven't measured this in prod)

---

## 13. Success Criteria for This Portfolio Project

### Before You Show This to Employers, Verify:
- [ ] README is polished and tells a story (problem → solution → roadmap)
- [ ] PRD demonstrates metrics-first thinking (north star clearly defined)
- [ ] Code is readable — multi-agent pattern is obvious
- [ ] Architecture decisions document tradeoffs (not just "why we chose X")
- [ ] Session history works (users can compare analyses and see progress)
- [ ] Action completion tracker is functional (checkbox → persistence)
- [ ] Repo has >15 commits showing iteration (not one big dump)
- [ ] You can explain: why these 3 agents, why GPT-4o, why session-only memory in v1

### Portfolio Win Conditions:
1. **Interviewer asks:** "Walk me through your north star metric" → You explain clearly
2. **Interviewer asks:** "Why did you build this and not X?" → You cite the problem + user outcomes
3. **Interviewer looks at code:** → Says "clean, I understand the architecture"
4. **Interviewer sees PRD:** → Says "this is PM thinking, not just engineering"
5. **You get follow-up question:** "What would you do differently?" → You discuss v2.0 hypotheses
