/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class', // 다크 모드 지원
  content: [
    './src/**/*.{js,jsx,ts,tsx}',
    './node_modules/@headlessui/react/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#1A73E8',
        secondary: '#34A853',
        danger: '#D93025',
        warning: '#FBBC05',
        // 추가 색상 정의
      },
      fontFamily: {
        sans: ['Roboto', 'Helvetica', 'Arial', 'sans-serif'],
        serif: ['Merriweather', 'serif'],
        // 추가 폰트 정의
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};
