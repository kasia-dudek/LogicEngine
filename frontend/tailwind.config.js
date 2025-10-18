module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: false, // or 'media' or 'class'
  theme: {
    extend: {},
  },
  variants: {
    extend: {},
  },
  plugins: [],
  safelist: [
    // Print-specific classes
    'print:hidden',
    'print:block',
    'print:bg-blue-100',
    'print:bg-green-100', 
    'print:bg-yellow-100',
    'print:bg-purple-100',
    'print:bg-gray-200',
    'print:shadow-none',
    'print:page-break-inside-avoid',
    'print:page-break-after-always',
    'print:scale-90',
    'print-container',
    'print-only',
  ],
}
