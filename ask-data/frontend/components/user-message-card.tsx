"use client";

interface UserMessageCardProps {
  content: string;
}

export function UserMessageCard({ content }: UserMessageCardProps) {
  return (
    <section className="flex w-full justify-end">
      <div className="flex w-full max-w-[46rem] items-end gap-3 lg:max-w-[78%]">
        <div className="min-w-0 flex-1 rounded-[26px] rounded-br-[10px] border border-[#123d63] bg-[linear-gradient(135deg,#0a3a57_0%,#081645_58%,#14005e_100%)] px-5 py-4 text-white shadow-[0_20px_40px_rgba(8,0,77,0.18)]">
          <div className="mb-2 flex items-center gap-2">
            <span className="inline-flex h-6 items-center rounded-full border border-white/12 bg-white/10 px-2.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-white/78">
              You
            </span>
          </div>
          <p className="whitespace-pre-wrap text-[15px] leading-7 text-white/96">{content}</p>
        </div>
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-[#d7dfef] bg-[linear-gradient(180deg,#ffffff_0%,#eef2fb_100%)] text-[#11294a] shadow-[0_10px_22px_rgba(15,23,42,0.1)]">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden>
            <circle cx="10" cy="7" r="3.2" stroke="currentColor" strokeWidth="1.6" />
            <path d="M4.5 16c0-3.037 2.463-4.8 5.5-4.8s5.5 1.763 5.5 4.8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
          </svg>
        </div>
      </div>
    </section>
  );
}
