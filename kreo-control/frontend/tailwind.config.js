/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0d1117",
        panel: "#161b22",
        panelBorder: "#30363d",
        brandPrimary: "#a855f7",
        brandAccent: "#c084fc",
      },
    },
  },
  plugins: [],
}

