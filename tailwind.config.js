/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./src/**/*.{astro,html,js,jsx,ts,tsx,vue,svelte}"
  ],
  theme: {
    extend: {
      fontFamily: {
        rajdhani: ['"Rajdhani"', "sans-serif"],
        rubik: ['"Rubik"', "sans-serif"],
        slackey: ['"Slackey"', "sans-serif"],
        stack: ['"Stack Sans Notch"', "sans-serif"],
      },
      boxShadow: {
        soft: "0 2px 8px rgba(0, 0, 0, 0.05)",
        card: "0 0 5px rgba(0, 0, 0, 0.06)",
      },
      textShadow: {
        soft: "0 1px 2px rgba(0, 0, 0, 0.25)",
      },
    },
  },
  plugins: [
    ({ matchUtilities, theme }) => {
      matchUtilities(
        {
          "text-shadow": (value) => ({
            textShadow: value,
          }),
        },
        { values: theme("textShadow") }
      );
    },
    ({ addVariant }) => {
      addVariant('not-first', '&:not(:first-of-type)');
    }
  ],
}
