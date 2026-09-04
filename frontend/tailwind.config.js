/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        trust: {
          bg: '#090B10',
          surface: '#10141F',
          card: '#161B28',
          border: '#21293B',
          muted: '#8B949E',
          accent: '#8B5CF6',
          'accent-hover': '#7C3AED',
          cyan: '#06B6D4',
          green: '#10B981',
          'green-bg': 'rgba(16, 185, 129, 0.12)',
          amber: '#F59E0B',
          'amber-bg': 'rgba(245, 158, 11, 0.12)',
          red: '#EF4444',
          'red-bg': 'rgba(239, 68, 68, 0.12)',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace']
      },
      animation: {
        'pulse-subtle': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 10px rgba(139, 92, 246, 0.2)' },
          '100%': { boxShadow: '0 0 25px rgba(139, 92, 246, 0.5)' },
        }
      }
    },
  },
  plugins: [],
}
