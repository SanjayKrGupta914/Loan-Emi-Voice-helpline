/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: '#FFFFFF',
          secondary: '#F7F8FA',
          sidebar: '#FFFFFF',
        },
        primaryText: '#202938',
        secondaryText: '#737B89',
        borderCustom: '#E8EBEF',
        brand: {
          blue: '#315E9E',
          blueSecondary: '#6D91BE',
          green: '#24865B',
          orange: '#D99A32',
          red: '#D9534F',
          lightBlue: '#F0F5FA',
          lightGreen: '#EAF6F0',
          lightOrange: '#FEF8EC',
          lightRed: '#FDF2F2',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        subtle: '0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.03)',
      },
      borderRadius: {
        DEFAULT: '8px',
      },
    },
  },
  plugins: [],
}

