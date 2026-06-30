/**
 * tokens.js — JavaScript mirror of src/styles/tokens.css
 *
 * Use this whenever you need design token values inside JavaScript logic
 * (e.g., Recharts fill arrays, canvas drawing, dynamic style objects).
 *
 * Rule: Never hardcode a hex value in a JS/JSX file.
 * Always import from here so that ONE change in tokens.css + here stays in sync.
 */

export const colors = {
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
  text: {
    primary:   '#f8fafc',
    secondary: '#94a3b8',
    muted:     '#64748b',
  },
  border: {
    default: 'rgba(255, 255, 255, 0.08)',
  },
};

export const chart = {
  height:          250,
  heightPie:       260,
  innerRadius:     70,
  outerRadius:     110,
  dotRadius:       4,
  activeDotRadius: 6,
};

export const duration = {
  fast:   150,
  normal: 200,
  slow:   300,
};
