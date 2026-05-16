"use client";

type BriefingSection = {
  id: string;
  label: string;
  labelId: string;
  title: string;
  titleId: string;
  body: string;
  bodyId: string;
  bullets: readonly string[];
  bulletsId: readonly string[];
};

interface DemoGuidePanelProps {
  sections: readonly BriefingSection[];
  activeSectionId: string;
  onSelectSection: (sectionId: string) => void;
  lang: "en" | "id";
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
};

const sectionSupport: Record<
  string,
  {
    audienceTitle: { en: string; id: string };
    audienceBody: { en: string; id: string };
    flowTitle: { en: string; id: string };
    flowSteps: { en: readonly string[]; id: readonly string[] };
    promptTitle: { en: string; id: string };
    prompts: readonly string[];
  }
> = {
  "use-case": {
    audienceTitle: {
      en: "Scenarios That Resonate with the Audience",
      id: "Skenario yang Relevan bagi Audiens",
    },
    audienceBody: {
      en: "Ground the demo in real business moments. The assistant is strongest during portfolio reviews, dormancy monitoring, and campaign planning — when decisions are made live and follow-up questions cannot wait.",
      id: "Perkuat demo dengan momen bisnis nyata. Asisten paling efektif saat review portofolio, pemantauan dormant, dan perencanaan kampanye — ketika keputusan dibuat langsung dan pertanyaan lanjutan tidak bisa menunggu.",
    },
    flowTitle: {
      en: "How to Present the Use Cases",
      id: "Cara Menyajikan Use Case",
    },
    flowSteps: {
      en: [
        "Describe a familiar meeting scenario — a portfolio review where a live dormancy question cannot wait for the next report.",
        "Show how the assistant answers in real time with a chart, then continues the conversation without losing context.",
        "Highlight that business users share the same governed experience as analysts — no separate tools, no data handoffs.",
      ],
      id: [
        "Gambarkan skenario rapat yang familiar — review portofolio di mana pertanyaan dormant tidak bisa menunggu laporan berikutnya.",
        "Tunjukkan bagaimana asisten menjawab secara real time dengan grafik, lalu melanjutkan percakapan tanpa kehilangan konteks.",
        "Tekankan bahwa pengguna bisnis mendapatkan pengalaman terkelola yang sama seperti analis — tanpa tooling terpisah, tanpa serah terima data.",
      ],
    },
    promptTitle: {
      en: "Use Case Prompts",
      id: "Prompt Use Case",
    },
    prompts: [
      "Tampilkan jumlah nasabah berdasarkan customer segment.",
      "Segmen mana yang memiliki risiko dormant paling tinggi?",
      "Berapa total saldo deposito untuk nasabah dormant risk high?",
    ],
  },
  "business-impact": {
    audienceTitle: {
      en: "What Management Wants to Hear",
      id: "Yang Ingin Didengar Manajemen",
    },
    audienceBody: {
      en: "Lead with outcomes, not features. Management cares about decision speed, cost of delay, and risk exposure — not SQL generation or model routing. Frame every capability as a measurable business result.",
      id: "Mulai dengan hasil, bukan fitur. Manajemen peduli pada kecepatan keputusan, biaya keterlambatan, dan eksposur risiko — bukan pembuatan SQL atau routing model. Framing setiap kemampuan sebagai hasil bisnis yang terukur.",
    },
    flowTitle: {
      en: "How to Frame the Value Story",
      id: "Cara Membingkai Narasi Nilai",
    },
    flowSteps: {
      en: [
        "Open with the cost of the current state — how long does it take today to answer a dormancy question in a board meeting?",
        "Show that the answer appears in seconds without involving the analytics team or waiting for the reporting cycle.",
        "Close with the governance angle — every answer is auditable, policy-safe, and traceable to structured data.",
      ],
      id: [
        "Buka dengan biaya kondisi saat ini — berapa lama waktu yang dibutuhkan untuk menjawab pertanyaan dormant dalam rapat direksi?",
        "Tunjukkan bahwa jawaban muncul dalam hitungan detik tanpa melibatkan tim analitik atau menunggu siklus pelaporan.",
        "Tutup dengan sudut pandang tata kelola — setiap jawaban dapat diaudit, aman sesuai kebijakan, dan dapat dilacak ke data terstruktur.",
      ],
    },
    promptTitle: {
      en: "Prompts That Land with Management",
      id: "Prompt yang Efektif untuk Manajemen",
    },
    prompts: [
      "Tampilkan distribusi nasabah berdasarkan segment.",
      "Segmen mana yang paling berisiko dormant?",
      "Berapa total saldo nasabah di segmen high-value?",
    ],
  },
};

export function DemoGuidePanel({
  sections,
  activeSectionId,
  onSelectSection,
  lang,
}: DemoGuidePanelProps) {
  const activeSection = sections.find((s) => s.id === activeSectionId) ?? sections[0];
  const theme = sectionTheme[activeSection.id] ?? sectionTheme["use-case"];
  const support = sectionSupport[activeSection.id] ?? sectionSupport["use-case"];

  const headerText = {
    en: {
      kicker: "Demo Guide",
      title: "Customer Segmentation Intelligence",
      subtitle:
        "Use this guide before live exploration to align on what the demo covers, why it matters, and how to tell the story in a business-relevant way.",
      openingKicker: "Recommended Opening",
      openingBody:
        "This demo shows how portfolio and relationship teams can analyze customer segmentation and dormancy data in natural language — receiving governed, chart-ready answers instantly.",
      chipReady: "Customer Demo Ready",
      chipGuided: "Guided Storyline",
    },
    id: {
      kicker: "Demo Guide",
      title: "Kecerdasan Segmentasi Nasabah",
      subtitle:
        "Gunakan panduan ini sebelum eksplorasi langsung untuk menyelaraskan apa yang dicakup demo, mengapa itu penting, dan bagaimana menyampaikan cerita dengan cara yang relevan secara bisnis.",
      openingKicker: "Pembukaan yang Disarankan",
      openingBody:
        "Demo ini menunjukkan bagaimana tim portofolio dan relationship dapat menganalisis data segmentasi nasabah dan risiko dormant dalam bahasa alami — mendapatkan jawaban terkelola dan siap grafik secara instan.",
      chipReady: "Siap Demo Nasabah",
      chipGuided: "Storyline Terpandu",
    },
  };

  const h = headerText[lang];

  return (
    <div className="space-y-5">
      {/* Hero header */}
      <section className={`rounded-[26px] border px-6 py-6 shadow-panel ${theme.shell}`}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-4xl">
            <p className={`text-[11px] font-semibold uppercase tracking-[0.26em] ${theme.kicker}`}>
              {h.kicker}
            </p>
            <h3 className="mt-3 font-headline text-[34px] font-bold leading-[1.04] text-[var(--color-ink-strong)]">
              {h.title}
            </h3>
            <p className="mt-4 text-[15px] leading-8 text-[var(--color-ink-muted)]">
              {h.subtitle}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className={`rounded-full border px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.14em] ${theme.chip}`}>
              {h.chipReady}
            </span>
            <span className="rounded-full border border-white/70 bg-white/70 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.14em] text-[var(--color-ink-muted)]">
              {h.chipGuided}
            </span>
          </div>
        </div>

        <div className="mt-6 rounded-[20px] border border-white/70 bg-white/70 p-5 backdrop-blur-sm">
          <p className={`text-[11px] font-semibold uppercase tracking-[0.24em] ${theme.kicker}`}>
            {h.openingKicker}
          </p>
          <p className="mt-3 text-sm leading-7 text-[var(--color-ink-muted)]">
            {h.openingBody}
          </p>
        </div>
      </section>

      {/* Section tabs */}
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
                  {lang === "id" ? `Bagian ${index + 1}` : `Section ${index + 1}`}
                </p>
                <p
                  className={`mt-1 font-headline text-sm font-semibold ${isActive ? "" : "text-[var(--color-ink-strong)]/88"}`}
                >
                  {lang === "id" ? section.labelId : section.label}
                </p>
              </button>
            );
          })}
        </div>
      </section>

      {/* Active section content */}
      <section className={`rounded-[26px] border px-6 py-6 shadow-panel ${theme.shell}`}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-4xl">
            <p className={`text-[11px] font-semibold uppercase tracking-[0.24em] ${theme.kicker}`}>
              {lang === "id" ? activeSection.labelId : activeSection.label}
            </p>
            <h3 className="mt-3 font-headline text-[34px] font-bold leading-[1.05] text-[var(--color-ink-strong)]">
              {lang === "id" ? activeSection.titleId : activeSection.title}
            </h3>
            <p className="mt-4 text-[15px] leading-8 text-[var(--color-ink-muted)]">
              {lang === "id" ? activeSection.bodyId : activeSection.body}
            </p>
          </div>
        </div>

        <div className="mt-6 grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
          <section className="space-y-5">
            <div className={`rounded-[22px] border p-5 ${theme.callout}`}>
              <p className={`text-[11px] font-semibold uppercase tracking-[0.24em] ${theme.kicker}`}>
                {support.audienceTitle[lang]}
              </p>
              <p className="mt-3 text-sm leading-7 text-[var(--color-ink-muted)]">
                {support.audienceBody[lang]}
              </p>
            </div>

            <div className="rounded-[22px] border border-white/70 bg-white/72 p-5 backdrop-blur-sm">
              <p className={`text-[11px] font-semibold uppercase tracking-[0.24em] ${theme.kicker}`}>
                {lang === "id" ? "Yang Perlu Dijelaskan" : "What To Explain"}
              </p>
              <ul className="mt-4 space-y-3">
                {(lang === "id" ? activeSection.bulletsId : activeSection.bullets).map((bullet) => (
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
                {support.flowTitle[lang]}
              </p>
              <div className="mt-4 space-y-3">
                {support.flowSteps[lang].map((item, index) => (
                  <div
                    key={item}
                    className={`rounded-[16px] border px-4 py-4 ${theme.callout}`}
                  >
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--color-ink-subtle)]">
                      {lang === "id" ? `Langkah ${index + 1}` : `Step ${index + 1}`}
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
                {support.promptTitle[lang]}
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
