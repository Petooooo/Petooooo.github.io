/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        ink: "#08090d",
        panel: "#10131a",
        line: "rgba(255,255,255,0.12)",
        signal: "#66e3ff",
        mint: "#8df2c8",
        amber: "#ffd166"
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "SFMono-Regular", "Consolas", "monospace"]
      },
      boxShadow: {
        glow: "0 0 60px rgba(102, 227, 255, 0.15)"
      }
    }
  },
  plugins: []
};
