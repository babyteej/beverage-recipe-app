/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        cream: {
          50: '#faf8f5',
          100: '#f3efe8',
          200: '#e8e0d4',
        },
        sage: {
          400: '#7a917a',
          500: '#6b7f6b',
          600: '#556655',
          700: '#445544',
        },
        amber: {
          warn: '#c17f3a',
          soft: '#f5ebe0',
        },
        terracotta: {
          500: '#b85c38',
          soft: '#f7ece6',
        },
      },
      fontFamily: {
        serif: ['"Libre Baskerville"', 'Georgia', 'serif'],
        sans: ['"Source Sans 3"', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
