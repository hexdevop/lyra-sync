export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#050508',
        surface: '#0d0d18',
        border: 'rgba(124,106,247,0.15)',
        accent: '#7c6af7',
        'accent-2': '#a599ff',
        active: '#f0e96b',
        muted: '#5a5a90',
        faint: '#e8e8f0',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        glow: '0 0 40px rgba(124,106,247,0.25)',
        'glow-sm': '0 0 20px rgba(124,106,247,0.15)',
      },
    },
  },
  plugins: [],
}
