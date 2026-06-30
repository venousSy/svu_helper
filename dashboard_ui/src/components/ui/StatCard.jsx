import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';

export default function StatCard({ title, value, subtitle, icon: Icon, color = 'blue', trend, to }) {
  const colorMap = {
    blue: {
      bg: 'bg-brand-primary/10',
      icon: 'text-brand-primary',
      border: 'border-brand-primary/20',
      shadow: 'hover:shadow-[0_4px_20px_rgba(139,92,246,0.3)]',
    },
    green: {
      bg: 'bg-brand-success/10',
      icon: 'text-brand-success',
      border: 'border-brand-success/20',
      shadow: 'hover:shadow-[0_4px_20px_rgba(16,185,129,0.3)]',
    },
    purple: {
      bg: 'bg-brand-accent/10',
      icon: 'text-brand-accent',
      border: 'border-brand-accent/20',
      shadow: 'hover:shadow-[0_4px_20px_rgba(14,165,233,0.3)]',
    },
    amber: {
      bg: 'bg-brand-warning/10',
      icon: 'text-brand-warning',
      border: 'border-brand-warning/20',
      shadow: 'hover:shadow-[0_4px_20px_rgba(245,158,11,0.3)]',
    },
  };

  const colors = colorMap[color] || colorMap.blue;

  const CardContent = (
    <motion.div 
      whileHover={{ y: -4, scale: 1.01 }}
      whileTap={{ scale: 0.98 }}
      className={`glass rounded-xl p-6 border ${colors.border} ${colors.shadow} transition-shadow duration-normal relative overflow-hidden h-full`}
    >
      {/* Background glow mesh */}
      <div className={`absolute -right-4 -top-4 w-24 h-24 rounded-full blur-2xl opacity-20 ${colors.bg}`} />
      
      <div className="flex items-start justify-between relative z-10">
        <div>
          <p className="text-sm font-medium text-text-secondary">{title}</p>
          <p className="mt-2 text-3xl font-bold text-text-primary tracking-tight">{value}</p>
          {subtitle && <p className="mt-1 text-xs text-text-muted">{subtitle}</p>}
        </div>
        {Icon && (
          <div className={`p-3 rounded-lg ${colors.bg} backdrop-blur-sm`}>
            <Icon size={22} className={colors.icon} />
          </div>
        )}
      </div>
      {trend !== undefined && (
        <p className={`mt-4 text-sm font-medium relative z-10 ${trend >= 0 ? 'text-brand-success' : 'text-brand-danger'}`}>
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}% from last period
        </p>
      )}
    </motion.div>
  );

  if (to) {
    return <Link to={to} className="block h-full">{CardContent}</Link>;
  }

  return CardContent;
}
