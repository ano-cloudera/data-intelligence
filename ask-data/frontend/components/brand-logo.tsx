import Image from "next/image";

interface BrandLogoProps {
  compact?: boolean;
}

export function BrandLogo({ compact = false }: BrandLogoProps) {
  if (compact) {
    return (
      <div className="relative h-7 w-28">
        <Image
          src="/Cloudera_logo.svg.png"
          alt="Cloudera"
          fill
          className="object-contain object-left"
          sizes="112px"
          priority
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-4 py-2">
      {/* Cloudera logo — centered, generous size */}
      <div className="relative h-11 w-[172px]">
        <Image
          src="/Cloudera_logo.svg.png"
          alt="Cloudera"
          fill
          className="object-contain"
          sizes="172px"
          priority
        />
      </div>

      {/* Divider */}
      <div className="h-px w-full bg-white/10" />

      {/* App title block — centered */}
      <div className="w-full text-center">
        <h1 className="font-headline text-[1.05rem] font-extrabold leading-tight tracking-[-0.01em] text-white">
          Data Intelligence
        </h1>
        <p className="mt-1 text-[10px] font-semibold uppercase tracking-[0.28em] text-[#8f94ff]">
          Assistant
        </p>
      </div>
    </div>
  );
}
