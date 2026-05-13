import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#191c1f",
        slate: "#474650",
        mist: "#e6e9f2",
        cloud: "#f3f5fa",
        brand: "#ff7a2f",
        brandSoft: "#fff0e6",
        warn: "#a04100",
        danger: "#ba1a1a",
        indigo: "#5c63f2",
      },
      boxShadow: {
        panel: "0 18px 38px rgba(15, 23, 42, 0.06)",
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "SFMono-Regular", "monospace"],
        headline: ["Manrope", "Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
