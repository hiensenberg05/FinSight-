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
          base: '#0B0F17',
          sidebar: '#0D111A',
          surface: '#111622',
          bubble: '#151D2E',
          raised: '#1A2338',
          activePill: '#1E293B',
        },
        brand: {
          violet: '#6366F1',
          purpleLight: '#A5B4FC',
          pink: '#F43F5E',
          cyan: '#06B6D4',
          indigo: '#4F46E5',
        },
        text: {
          primary: '#F8FAFC',
          secondary: '#94A3B8',
          muted: '#64748B',
          subtle: '#475569',
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
