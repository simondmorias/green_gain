/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'spiro': '#1FC1F0',
        'bluebonnet': '#1821ED',
        'purple-x11': '#A034F9',
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #1FC1F0 0%, #1821ED 50%, #A034F9 100%)',
      },
    },
  },
  plugins: [],
}