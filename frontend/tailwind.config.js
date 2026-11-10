/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: {
          base: '#070512',
          sidebar: '#0A0917',
          surface: '#0D0B16',
          bubble: '#17152A',
          raised: '#14112E',
          activePill: '#160F42',
        },
        brand: {
          violet: '#6D4FFF',
          purpleLight: '#A78BFA',
          pink: '#FF4984',
          cyan: '#2ECB9E',
          indigo: '#3C34C8',
        },
        text: {
          primary: '#FFFFFF',
          secondary: '#C8C5DC',
          muted: '#7C7896',
          subtle: '#5A5675',
        },
        border: {
          card: 'rgba(255, 255, 255, 0.08)',
          active: 'rgba(109, 79, 255, 0.4)',
        },
      },
      borderRadius: {
        'card': '16px',
        'subcard': '12px',
        'input': '10px',
        'pill': '9999px',
      },
      fontSize: {
        'hero': ['31px', { lineHeight: '38px', fontWeight: '700' }],
        'kpi': ['28px', { lineHeight: '34px', fontWeight: '700' }],
        'title': ['15px', { lineHeight: '22px', fontWeight: '600' }],
        'body': ['14px', { lineHeight: '20px', fontWeight: '400' }],
        'label': ['13px', { lineHeight: '18px', fontWeight: '500' }],
        'caption': ['12px', { lineHeight: '16px', fontWeight: '400' }],
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'orb-glow': '0 0 60px rgba(109, 79, 255, 0.4), 0 0 100px rgba(255, 73, 132, 0.25)',
        'mic-glow': '0 0 20px rgba(109, 79, 255, 0.6)',
      },
    },
  },
  plugins: [],
}
