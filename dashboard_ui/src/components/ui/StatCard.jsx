export default function StatCard({ title, value, subtitle, icon: Icon, color = 'blue', trend }) {
  const colorMap = {
    blue: {
      bg: 'bg-brand-primary/10',
      icon: 'text-brand-primary',
      border: 'border-brand-primary/20',
    },
    green: {
      bg: 'bg-brand-success/10',
      icon: 'text-brand-success',
      border: 'border-brand-success/20',
    },
    purple: {
      bg: 'bg-brand-accent/10',
      icon: 'text-brand-accent',
      border: 'border-brand-accent/20',
    },
    amber: {
      bg: 'bg-brand-warning/10',
      icon: 'text-brand-warning',
      border: 'border-brand-warning/20',
    },
  };

  const colors = colorMap[color] || colorMap.blue;

  return (
    <div className={`glass rounded-xl p-6 border ${colors.border} hover:scale-[1.02] transition-transform duration-normal`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-text-secondary">{title}</p>
          <p className="mt-2 text-3xl font-bold text-text-primary tracking-tight">{value}</p>
          {subtitle && <p className="mt-1 text-xs text-text-muted">{subtitle}</p>}
        </div>
        {Icon && (
          <div className={`p-3 rounded-lg ${colors.bg}`}>
            <Icon size={22} className={colors.icon} />
          </div>
        )}
      </div>
      {trend !== undefined && (
        <p className={`mt-4 text-sm font-medium ${trend >= 0 ? 'text-brand-success' : 'text-brand-danger'}`}>
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}% from last period
        </p>
      )}
    </div>
  );
}
