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
          primary:  'var(--color-brand-primary)',
          dim:      'var(--color-brand-primary-dim)',
          accent:   'var(--color-brand-accent)',
          success:  'var(--color-brand-success)',
          warning:  'var(--color-brand-warning)',
          danger:   'var(--color-brand-danger)',
        },
        status: {
          pending:  'var(--color-status-pending)',
          offered:  'var(--color-status-offered)',
          accepted: 'var(--color-status-accepted)',
          finished: 'var(--color-status-finished)',
          denied:   'var(--color-status-denied)',
        },
        surface: {
          base:     'var(--color-bg-base)',
          DEFAULT:  'var(--color-bg-surface)',
          elevated: 'var(--color-bg-elevated)',
        },
        border: {
          DEFAULT: 'var(--color-border-default)',
          subtle:  'var(--color-border-subtle)',
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
