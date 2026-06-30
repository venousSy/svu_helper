/** @type {import('tailwindcss').Config} */
/**
 * Tailwind Design Token Extension
 *
 * Tokens from `src/styles/tokens.css` are surfaced here as Tailwind classes.
 * This means you can use `bg-brand-primary`, `text-status-finished`, etc.
 * Rule: If you add a new token to tokens.css, extend it here too.
 */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary:  '#8b5cf6',
          dim:      '#6d28d9',
          accent:   '#0ea5e9',
          success:  '#10b981',
          warning:  '#f59e0b',
          danger:   '#ef4444',
        },
        status: {
          pending:  '#f59e0b',
          offered:  '#8b5cf6',
          accepted: '#0ea5e9',
          finished: '#10b981',
          denied:   '#ef4444',
        },
        surface: {
          base:     '#020617',
          DEFAULT:  '#0f172a',
          elevated: '#1e293b',
        },
        border: {
          DEFAULT: 'rgba(255, 255, 255, 0.08)',
          subtle:  'rgba(255, 255, 255, 0.03)',
        },
        text: {
          primary: '#f8fafc',
          secondary: '#94a3b8',
          muted: '#64748b',
        },
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        xl: 'var(--radius-xl)',
      },
      transitionDuration: {
        fast:   'var(--duration-fast)',
        normal: 'var(--duration-normal)',
        slow:   'var(--duration-slow)',
      },
      width: {
        sidebar: 'var(--sidebar-width)',
      },
      height: {
        header: 'var(--header-height)',
      },
    },
  },
  plugins: [],
}
