"use client";

type BriefingSection = {
  id: string;
  label: string;
  title: string;
  body: string;
  bullets: readonly string[];
};

interface DemoGuidePanelProps {
  sections: readonly BriefingSection[];
  activeSectionId: string;
  onSelectSection: (sectionId: string) => void;
}

const sectionTheme: Record<
  string,
  {
    kicker: string;
    shell: string;
    chip: string;
    callout: string;
    softCard: string;
    tabInactive: string;
    tabActive: string;
  }
> = {
  "business-impact": {
    kicker: "text-amber-700",
    shell: "border-amber-200 bg-[linear-gradient(180deg,#fffaf2_0%,#fff4df_100%)]",
    chip: "border-amber-200 bg-white text-amber-700",
    callout: "border-amber-100 bg-white",
    softCard: "border-amber-100 bg-amber-50/60",
    tabInactive:
      "border-amber-100/90 bg-amber-50/85 text-[var(--color-ink-strong)] hover:border-amber-200 hover:bg-amber-100/70",
    tabActive:
      "border-amber-300 bg-white text-amber-950 shadow-[0_12px_28px_rgba(245,158,11,0.16)] ring-1 ring-amber-200/80",
  },
  "use-case": {
    kicker: "text-sky-700",
    shell: "border-sky-200 bg-[linear-gradient(180deg,#f6fbff_0%,#eef7ff_100%)]",
    chip: "border-sky-200 bg-white text-sky-700",
    callout: "border-sky-100 bg-white",
    softCard: "border-sky-100 bg-sky-50/60",
    tabInactive:
      "border-sky-100/90 bg-sky-50/85 text-[var(--color-ink-strong)] hover:border-sky-200 hover:bg-sky-100/70",
    tabActive:
      "border-sky-300 bg-white text-sky-900 shadow-[0_12px_28px_rgba(14,165,233,0.14)] ring-1 ring-sky-200/80",
  },
  "data-scope": {
    kicker: "text-emerald-700",
    shell: "border-emerald-200 bg-[linear-gradient(180deg,#f5fff9_0%,#edf9f2_100%)]",
    chip: "border-emerald-200 bg-white text-emerald-700",
    callout: "border-emerald-100 bg-white",
    softCard: "border-emerald-100 bg-emerald-50/60",
    tabInactive:
      "border-emerald-100/90 bg-emerald-50/85 text-[var(--color-ink-strong)] hover:border-emerald-200 hover:bg-emerald-100/70",
    tabActive:
      "border-emerald-300 bg-white text-emerald-950 shadow-[0_12px_28px_rgba(16,185,129,0.14)] ring-1 ring-emerald-200/80",
  },
  "how-to-demo": {
    kicker: "text-rose-700",
    shell: "border-rose-200 bg-[linear-gradient(180deg,#fff7f8_0%,#fff0f3_100%)]",
    chip: "border-rose-200 bg-white text-rose-700",
    callout: "border-rose-100 bg-white",
    softCard: "border-rose-100 bg-rose-50/60",
    tabInactive:
      "border-rose-100/90 bg-rose-50/85 text-[var(--color-ink-strong)] hover:border-rose-200 hover:bg-rose-100/70",
    tabActive:
      "border-rose-300 bg-white text-rose-950 shadow-[0_12px_28px_rgba(244,63,94,0.12)] ring-1 ring-rose-200/80",
  },
};

const sectionSupportCopy: Record<
  string,
  {
    audienceTitle: string;
    audienceBody: string;
    flowTitle: string;
    flowSteps: readonly string[];
    promptTitle: string;
    prompts: readonly string[];
  }
> = {
  "business-impact": {
    audienceTitle: "What Management Wants to Hear",
    audienceBody:
      "Lead with outcomes, not features. Management cares about decision speed, cost of delay, and risk exposure — not SQL generation or model routing. Frame every capability as a business result.",
    flowTitle: "How to Frame the Value Story",
    flowSteps: [
      "Open with the cost of the current state — how long does it take today to answer a portfolio question in a board meeting?",
      "Show that the answer appears in seconds, without involving the analytics team or waiting for the next reporting cycle.",
      "Close with the governance angle — every answer is auditable, policy-safe, and traceable to structured data.",
    ],
    promptTitle: "Prompts That Land with Management",
    prompts: [
      "What is the total outstanding credit right now?",
      "Compare deposit balance and credit exposure by segment.",
      "Show customer growth trend over the last 6 months.",
    ],
  },
  "use-case": {
    audienceTitle: "Scenarios That Resonate with the Audience",
    audienceBody:
      "Ground the demo in real business moments. The assistant is strongest when used in the context of live reviews, pipeline discussions, and portfolio monitoring — not as a standalone reporting tool.",
    flowTitle: "How to Present the Use Cases",
    flowSteps: [
      "Describe a familiar meeting scenario — a portfolio review where a live follow-up question cannot wait for the next report.",
      "Show how the assistant answers in real time, then continues the conversation without losing context.",
      "Highlight that business users and analysts share the same experience — no separate tools, no data handoffs.",
    ],
    promptTitle: "Use Case Prompts",
    prompts: [
      "Who are the customers with the highest outstanding credit?",
      "Which cities have the largest deposit concentration?",
      "Show the credit exposure breakdown by customer segment.",
    ],
  },
  "data-scope": {
    audienceTitle: "Setting Scope Expectations Early",
    audienceBody:
      "Clarify what the assistant can and cannot answer before going live. This prevents off-script questions from derailing the session and keeps the audience focused on the value within the demo boundary.",
    flowTitle: "How to Introduce the Data Domains",
    flowSteps: [
      "Introduce the three domains in one sentence each — Customer, Deposit, Credit — before showing any result.",
      "Demonstrate a cross-domain question to show the linked nature of the data without requiring a separate query.",
      "Note that policy and document questions require RAG Studio — set that expectation upfront.",
    ],
    promptTitle: "Scope-Setting Prompts",
    prompts: [
      "Show deposit balance split by city.",
      "Which segments hold the highest total deposit balance?",
      "Show outstanding credit trend by month.",
    ],
  },
  "how-to-demo": {
    audienceTitle: "Keep the Narrative Tight",
    audienceBody:
      "Three well-chosen questions are more impactful than ten scattered ones. Build confidence first, add depth second, demonstrate governance third. Avoid going off-script until the audience is already engaged.",
    flowTitle: "Recommended 15-Minute Flow",
    flowSteps: [
      "Step 1 — Aggregate: Ask a total balance or exposure question. Give the audience a number they can anchor to.",
      "Step 2 — Visual: Ask a trend or breakdown question. Show that charts appear without any extra steps.",
      "Step 3 — Governance: Ask for individual customer PII deliberately. Let the guardrail block it, then redirect to a safe alternative.",
      "Step 4 — RAG (optional): Introduce RAG Studio only if the conversation shifts to policy or document questions.",
    ],
    promptTitle: "Proven Demo Prompts",
    prompts: [
      "What is the total deposit balance right now?",
      "Show outstanding credit trend by month.",
      "Show me the personal details of our top debtor.",
      "Show the top 5 customers by outstanding credit.",
    ],
  },
};

export function DemoGuidePanel({
  sections,
  activeSectionId,
  onSelectSection,
}: DemoGuidePanelProps) {
  const activeSection = sections.find((section) => section.id === activeSectionId) ?? sections[0];
  const theme = sectionTheme[activeSection.id] ?? sectionTheme["business-impact"];
  const support =
    sectionSupportCopy[activeSection.id] ?? sectionSupportCopy["business-impact"];

  return (
    <div className="space-y-5">
      <section className={`rounded-[26px] border px-6 py-6 shadow-panel ${theme.shell}`}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-4xl">
            <p className={`text-[11px] font-semibold uppercase tracking-[0.26em] ${theme.kicker}`}>
              Demo Guide
            </p>
            <h3 className="mt-3 font-headline text-[34px] font-bold leading-[1.04] text-[var(--color-ink-strong)]">
              Ask the Data Sales Briefing
            </h3>
            <p className="mt-4 text-[15px] leading-8 text-[var(--color-ink-muted)]">
              Use this guide to frame the solution before live exploration starts. It is designed to help sales teams, solution engineers, and customer stakeholders align on what the demo covers, why it matters, and how to tell the story in a business-relevant way.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className={`rounded-full border px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.14em] ${theme.chip}`}>
              Customer Demo Ready
            </span>
            <span className="rounded-full border border-white/70 bg-white/70 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.14em] text-[var(--color-ink-muted)]">
              Guided Storyline
            </span>
          </div>
        </div>

        <div className="mt-6 rounded-[20px] border border-white/70 bg-white/70 p-5 backdrop-blur-sm">
          <p className={`text-[11px] font-semibold uppercase tracking-[0.24em] ${theme.kicker}`}>
            Recommended Opening
          </p>
          <p className="mt-3 text-sm leading-7 text-[var(--color-ink-muted)]">
            This demo shows how portfolio and relationship teams can ask structured business questions in natural language, receive governed answers with visual support, and continue the discussion without breaking the flow of analysis.
          </p>
        </div>
      </section>

      <section className="rounded-[24px] border border-[var(--color-border-soft)] bg-white p-5 shadow-panel">
        <div className="flex flex-wrap gap-3">
          {sections.map((section, index) => {
            const isActive = section.id === activeSection.id;
            const chipTheme = sectionTheme[section.id] ?? sectionTheme["use-case"];
            return (
              <button
                key={section.id}
                type="button"
                onClick={() => onSelectSection(section.id)}
                className={`rounded-[18px] border px-4 py-3 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#5c63f2]/35 focus-visible:ring-offset-2 ${
                  isActive ? chipTheme.tabActive : chipTheme.tabInactive
                }`}
              >
                <p
                  className={`text-[10px] font-semibold uppercase tracking-[0.22em] ${isActive ? chipTheme.kicker : `${chipTheme.kicker} opacity-[0.72]`}`}
                >
                  Section {index + 1}
                </p>
                <p
                  className={`mt-1 font-headline text-sm font-semibold ${isActive ? "" : "text-[var(--color-ink-strong)]/88"}`}
                >
                  {section.label}
                </p>
              </button>
            );
          })}
        </div>
      </section>

      <section className={`rounded-[26px] border px-6 py-6 shadow-panel ${theme.shell}`}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-4xl">
            <p className={`text-[11px] font-semibold uppercase tracking-[0.24em] ${theme.kicker}`}>
              {activeSection.label}
            </p>
            <h3 className="mt-3 font-headline text-[34px] font-bold leading-[1.05] text-[var(--color-ink-strong)]">
              {activeSection.title}
            </h3>
            <p className="mt-4 text-[15px] leading-8 text-[var(--color-ink-muted)]">
              {activeSection.body}
            </p>
          </div>
        </div>

        <div className="mt-6 grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
          <section className="space-y-5">
            <div className={`rounded-[22px] border p-5 ${theme.callout}`}>
              <p className={`text-[11px] font-semibold uppercase tracking-[0.24em] ${theme.kicker}`}>
                {support.audienceTitle}
              </p>
              <p className="mt-3 text-sm leading-7 text-[var(--color-ink-muted)]">
                {support.audienceBody}
              </p>
            </div>

            <div className="rounded-[22px] border border-white/70 bg-white/72 p-5 backdrop-blur-sm">
              <p className={`text-[11px] font-semibold uppercase tracking-[0.24em] ${theme.kicker}`}>
                What To Explain
              </p>
              <ul className="mt-4 space-y-3">
                {activeSection.bullets.map((bullet) => (
                  <li
                    key={bullet}
                    className={`rounded-[16px] border px-4 py-4 text-sm leading-7 text-[var(--color-ink-muted)] ${theme.callout}`}
                  >
                    {bullet}
                  </li>
                ))}
              </ul>
            </div>
          </section>

          <section className="space-y-5">
            <div className="rounded-[22px] border border-white/70 bg-white/72 p-5 backdrop-blur-sm">
              <p className={`text-[11px] font-semibold uppercase tracking-[0.24em] ${theme.kicker}`}>
                {support.flowTitle}
              </p>
              <div className="mt-4 space-y-3">
                {support.flowSteps.map((item, index) => (
                  <div
                    key={item}
                    className={`rounded-[16px] border px-4 py-4 ${theme.callout}`}
                  >
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--color-ink-subtle)]">
                      Step {index + 1}
                    </p>
                    <p className="mt-2 text-sm leading-7 text-[var(--color-ink-muted)]">
                      {item}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className={`rounded-[22px] border p-5 ${theme.softCard}`}>
              <p className={`text-[11px] font-semibold uppercase tracking-[0.24em] ${theme.kicker}`}>
                {support.promptTitle}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {support.prompts.map((prompt) => (
                  <span
                    key={prompt}
                    className={`rounded-full border px-3 py-1.5 text-xs font-medium ${theme.chip}`}
                  >
                    {prompt}
                  </span>
                ))}
              </div>
            </div>
          </section>
        </div>
      </section>
    </div>
  );
}
