/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        trust: {
          bg: '#070813', surface: '#101123', card: '#15172a', border: '#2b2e47', muted: '#999cb5',
          accent: '#8d6cff', 'accent-hover': '#a489ff', cyan: '#7ee8ef', green: '#61d9a8',
          'green-bg': 'rgba(97, 217, 168, 0.12)', amber: '#f5c86b', 'amber-bg': 'rgba(245, 200, 107, 0.12)',
          red: '#ff858f', 'red-bg': 'rgba(255, 133, 143, 0.12)'
        }
      },
      fontFamily: {
        sans: ['Manrope', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['DM Mono', 'ui-monospace', 'SFMono-Regular', 'monospace']
      }
    }
  },
  plugins: []
};
