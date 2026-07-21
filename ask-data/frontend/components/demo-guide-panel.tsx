"use client";

import { useState } from "react";

import { DemoGuideHeader } from "@/components/demo-guide-header";
import { DemoStageNavigation } from "@/components/demo-stage-navigation";
import { PresenterRunbook } from "@/components/presenter-runbook";
import { PresenterNotes } from "@/components/presenter-notes";
import { DemoStageActions } from "@/components/demo-stage-actions";

export interface DemoStageContent {
  id: string;
  label: { en: string; id: string };
  stageTitle: { en: string; id: string };
  say: { en: string; id: string };
  ask: string;
  highlight: { en: string; id: string };
  transition: { en: string; id: string };
  checklist: { en: readonly string[]; id: readonly string[] };
  focusNote: { en: string; id: string };
}

interface DemoGuidePanelProps {
  stages: readonly DemoStageContent[];
  activeStageId: string;
  onSelectStage: (stageId: string) => void;
  lang: "en" | "id";
}

const headerCopy = {
  en: {
    title: "Customer Segmentation & Dormancy",
    meta: "Live demo playbook · 8 min · Business audience",
    supportingText: "Identify dormant customer exposure and decide which segment should be prioritized.",
  },
  id: {
    title: "Segmentasi Nasabah & Risiko Dormant",
    meta: "Panduan demo langsung · 8 menit · Audiens bisnis",
    supportingText: "Identifikasi eksposur nasabah dormant dan tentukan segmen yang perlu diprioritaskan.",
  },
} as const;

export function DemoGuidePanel({ stages, activeStageId, onSelectStage, lang }: DemoGuidePanelProps) {
  const activeIndex = Math.max(
    0,
    stages.findIndex((s) => s.id === activeStageId),
  );
  const activeStage = stages[activeIndex] ?? stages[0];

  // Checklist state per stage, keyed by stage id — persists while navigating.
  const [checkedByStage, setCheckedByStage] = useState<Record<string, Record<number, boolean>>>({});

  function toggleChecklistItem(stageId: string, itemIndex: number) {
    setCheckedByStage((cur) => ({
      ...cur,
      [stageId]: {
        ...cur[stageId],
        [itemIndex]: !cur[stageId]?.[itemIndex],
      },
    }));
  }

  function goToStage(index: number) {
    const next = stages[Math.min(Math.max(index, 0), stages.length - 1)];
    if (next) onSelectStage(next.id);
  }

  const h = headerCopy[lang];

  return (
    <div className="mx-auto max-w-[72rem] rounded-[10px] border border-[var(--color-border-soft)] bg-[var(--color-surface)] px-6">
      <DemoGuideHeader
        title={h.title}
        meta={h.meta}
        supportingText={h.supportingText}
        stageIndex={activeIndex}
        stageCount={stages.length}
      />

      <DemoStageNavigation
        stages={stages}
        activeIndex={activeIndex}
        onSelect={goToStage}
        lang={lang}
      />

      <div className="grid gap-8 py-5 lg:grid-cols-[68%_32%]">
        <div className="min-w-0 lg:border-r lg:border-[var(--color-border-soft)] lg:pr-8">
          <PresenterRunbook
            stageTitle={activeStage.stageTitle[lang]}
            say={activeStage.say[lang]}
            ask={activeStage.ask}
            highlight={activeStage.highlight[lang]}
            transition={activeStage.transition[lang]}
            lang={lang}
          />
        </div>

        <PresenterNotes
          checklist={activeStage.checklist[lang]}
          checkedState={checkedByStage[activeStage.id] ?? {}}
          onToggle={(index) => toggleChecklistItem(activeStage.id, index)}
          focusNote={activeStage.focusNote[lang]}
          lang={lang}
        />
      </div>

      <DemoStageActions
        stageIndex={activeIndex}
        stageCount={stages.length}
        onPrevious={() => goToStage(activeIndex - 1)}
        onNext={() => goToStage(activeIndex + 1)}
        lang={lang}
      />
    </div>
  );
}
