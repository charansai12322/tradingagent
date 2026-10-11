/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/features/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#252821",
        bone: "#E9E4D9",
        chalk: "#F5F1E8",
        oxide: "#A34F3F",
        moss: "#68765A",
        stone: "#C9C2B5",
        muted: "#77766D",
        positive: "#357A52",
        negative: "#A34F3F",
        warning: "#966A24",
      },
      fontFamily: {
        serif: ["var(--font-serif)", "DM Serif Display", "Georgia", "serif"],
        sans: ["var(--font-sans)", "Manrope", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "IBM Plex Mono", "Menlo", "monospace"],
      },
      borderColor: {
        DEFAULT: "#C9C2B5",
      },
      boxShadow: {
        sm: "0 1px 2px 0 rgba(37, 40, 33, 0.05)",
        card: "0 1px 3px 0 rgba(37, 40, 33, 0.06), 0 1px 2px -1px rgba(37, 40, 33, 0.06)",
        dropdown: "0 4px 6px -1px rgba(37, 40, 33, 0.08), 0 2px 4px -2px rgba(37, 40, 33, 0.08)",
        modal: "0 10px 15px -3px rgba(37, 40, 33, 0.12), 0 4px 6px -4px rgba(37, 40, 33, 0.1)",
      },
      animation: {
        "fade-in": "fadeIn 180ms ease-out forwards",
        "slide-down": "slideDown 200ms ease-out forwards",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideDown: {
          "0%": { opacity: "0", transform: "translateY(-6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
