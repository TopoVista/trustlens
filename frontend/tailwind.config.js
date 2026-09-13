/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        trust: {
          bg: '#f7f3ed', surface: '#fffcf7', card: '#fffcf7', border: '#ddd5c8', muted: '#6d665d',
          accent: '#b56f52', 'accent-hover': '#914e38', cyan: '#4c695c', green: '#4c695c',
          'green-bg': '#dfe8df', amber: '#d28f45', 'amber-bg': '#f8ead5',
          red: '#b14f45', 'red-bg': '#f7dfdb'
        }
      },
      fontFamily: {
        sans: ['Manrope', 'Avenir Next', 'Avenir', 'Segoe UI', 'sans-serif'],
        mono: ['DM Mono', 'ui-monospace', 'SFMono-Regular', 'monospace']
      }
    }
  },
  plugins: []
};
