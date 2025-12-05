/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0f172a', // Slate 950
        surface: '#1e293b',    // Slate 900
        textPrimary: '#f8fafc', // Slate 50
        textSecondary: '#94a3b8' // Slate 400
      }
    },
  },
  plugins: [],
}