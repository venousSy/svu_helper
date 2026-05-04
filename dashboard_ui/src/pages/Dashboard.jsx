import { useState } from 'react';
import AppLayout from '../components/layout/AppLayout';
import StatCard from '../components/ui/StatCard';
import { useStats } from '../hooks/useStats';
import { useUrgentProjects } from '../hooks/useProjects';
import ProjectDetailsModal from '../components/projects/ProjectDetailsModal';
import { colors, chart } from '../styles/tokens';
import {
  AreaChart, Area, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { Banknote, FolderOpen, TrendingUp, CheckCircle, Loader2, AlertCircle, BarChart2, AlertOctagon, ExternalLink, Calendar, Clock } from 'lucide-react';

// All color values come from src/styles/tokens.js — no hardcoded hex here
const STATUS_COLORS = colors.status;
const STATUS_LABELS = {
  pending: 'قيد الانتظار',
  offered: 'تم التقديم',
  accepted: 'مقبول',
  finished: 'منتهي',
  denied: 'مرفوض',
};
const PIE_FALLBACK_COLORS = Object.values(colors.status);

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center h-64">
      <Loader2 className="w-10 h-10 text-brand-primary animate-spin" />
    </div>
  );
}

function ErrorMessage({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 gap-4">
      <AlertCircle className="w-10 h-10 text-brand-danger" />
      <p className="text-text-secondary">{message}</p>
      <button onClick={onRetry} className="px-4 py-2 text-sm rounded-lg bg-brand-primary hover:bg-brand-primary text-text-primary transition-colors">
        Retry
      </button>
    </div>
  );
}

function SectionTitle({ children }) {
  return <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-widest mb-5">{children}</h2>;
}

function EmptyChart({ label }) {
  return (
    <div className="flex flex-col items-center justify-center h-48 gap-3 rounded-lg border border-dashed border-border">
      <BarChart2 className="w-8 h-8 text-text-muted" />
      <p className="text-text-muted text-sm">{label}</p>
    </div>
  );
}

// Custom tooltip for charts
function ChartTooltip({ active, payload, label, valuePrefix = '', valueSuffix = '' }) {
  if (active && payload && payload.length) {
    return (
      <div className="glass rounded-lg px-4 py-3 border border-border text-sm">
        <p className="text-text-secondary mb-1">{label}</p>
        {payload.map((entry) => (
          <p key={entry.name} className="font-semibold" style={{ color: entry.color }}>
            {valuePrefix}{entry.value.toLocaleString()}{valueSuffix}
          </p>
        ))}
      </div>
    );
  }
  return null;
}

export default function Dashboard() {
  const { data, isLoading, error, refetch } = useStats();
  const { data: urgentProjects, isLoading: isLoadingUrgent } = useUrgentProjects();
  
  const [selectedProjectId, setSelectedProjectId] = useState(null);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);

  // --- Derived stats ---
  const totalProjects = data?.project_volume?.reduce((sum, d) => sum + d.count, 0) ?? 0;
  const totalRevenue = data?.revenue?.reduce((sum, d) => sum + d.revenue, 0) ?? 0;
  const finishedCount = data?.conversion_rates?.find(s => s._id === 'finished')?.count ?? 0;
  const conversionRate = totalProjects > 0 ? ((finishedCount / totalProjects) * 100).toFixed(1) : '0.0';

  // --- Chart data transformations ---
  const revenueData = data?.revenue?.map(d => ({ date: d._id, revenue: d.revenue })) ?? [];
  const volumeData = data?.project_volume?.map(d => ({ date: d._id, projects: d.count })) ?? [];
  const pieData = data?.conversion_rates?.map(d => ({
    name: STATUS_LABELS[d._id] || d._id,
    value: d.count,
    fill: STATUS_COLORS[d._id] || '#94a3b8',
  })) ?? [];

  return (
    <AppLayout title="Overview">
      {isLoading && <LoadingSpinner />}
      {error && <ErrorMessage message={error} onRetry={refetch} />}

      {!isLoading && !error && (
        <div className="space-y-8">

          {/* --- Stat Cards --- */}
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5">
            <StatCard
              title="Total Revenue"
              value={`${totalRevenue.toLocaleString()} SP`}
              subtitle="From accepted & finished projects"
              icon={Banknote}
              color="green"
            />
            <StatCard
              title="Total Projects"
              value={totalProjects.toLocaleString()}
              subtitle="All submissions ever"
              icon={FolderOpen}
              color="blue"
            />
            <StatCard
              title="Conversion Rate"
              value={`${conversionRate}%`}
              subtitle="Finished / Total projects"
              icon={TrendingUp}
              color="purple"
            />
            <StatCard
              title="Finished Projects"
              value={finishedCount.toLocaleString()}
              subtitle="Successfully delivered"
              icon={CheckCircle}
              color="amber"
            />
          </div>

          {/* --- Urgent Cases Section --- */}
          <div className="glass rounded-xl p-6 border border-brand-danger/30 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-brand-danger" />
            <div className="flex items-center gap-2 mb-5">
              <AlertOctagon className="w-5 h-5 text-brand-danger" />
              <h2 className="text-sm font-semibold text-text-primary uppercase tracking-widest">Urgent Cases</h2>
              <span className="bg-brand-danger/20 text-brand-danger text-xs px-2 py-0.5 rounded-full font-medium ml-2">
                {urgentProjects?.length || 0}
              </span>
            </div>
            
            {isLoadingUrgent ? (
              <div className="flex justify-center p-4"><Loader2 className="w-6 h-6 text-brand-danger animate-spin" /></div>
            ) : !urgentProjects || urgentProjects.length === 0 ? (
              <p className="text-sm text-text-muted">No urgent projects requiring attention right now.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {urgentProjects.map(project => (
                  <div key={project.id} className="bg-surface-elevated border border-border rounded-lg p-4 flex flex-col justify-between hover:border-brand-danger/50 transition-colors">
                    <div>
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-xs font-semibold text-text-muted">#{project.id}</span>
                        <span className="text-[10px] uppercase font-bold px-2 py-1 rounded bg-brand-danger/10 text-brand-danger">
                          {STATUS_LABELS[project.status] || project.status}
                        </span>
                      </div>
                      <h3 className="text-sm font-medium text-text-primary mb-1 line-clamp-1">{project.subject_name}</h3>
                      <p className="text-xs text-text-secondary mb-3">{project.user_full_name || project.username || `User ${project.user_id}`}</p>
                      
                      <div className="space-y-1.5 mb-4">
                        {project.delivery_date && (
                          <div className="flex items-center gap-1.5 text-xs text-text-secondary">
                            <Calendar className="w-3.5 h-3.5" />
                            <span>Delivery: <span className="font-medium text-text-primary">{project.delivery_date}</span></span>
                          </div>
                        )}
                        <div className="flex items-center gap-1.5 text-xs text-text-secondary">
                          <Clock className="w-3.5 h-3.5" />
                          <span>Submitted: <span className="font-medium text-text-primary">{new Date(project.created_at).toLocaleDateString()}</span></span>
                        </div>
                      </div>
                    </div>
                    
                    <button 
                      onClick={() => {
                        setSelectedProjectId(project.id);
                        setIsDetailsModalOpen(true);
                      }}
                      className="w-full flex items-center justify-center gap-1.5 py-1.5 text-xs font-medium text-text-primary bg-surface border border-border rounded-md hover:bg-border transition-colors"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      View Details
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* --- Charts Row --- */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">

            {/* Revenue Area Chart */}
            <div className="glass rounded-xl p-6 border border-border">
              <SectionTitle>Revenue Over Time (SP)</SectionTitle>
              {revenueData.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={revenueData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                    <defs>
                      <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25} />
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} width={60} />
                    <Tooltip content={<ChartTooltip valueSuffix=" SP" />} />
                    <Area type="monotone" dataKey="revenue" stroke={colors.brand.primary} strokeWidth={2} fill="url(#revenueGrad)" dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <EmptyChart label="Revenue data will appear as projects are completed" />
              )}
            </div>

            {/* Volume Line Chart */}
            <div className="glass rounded-xl p-6 border border-border">
              <SectionTitle>Project Volume Over Time</SectionTitle>
              {volumeData.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={volumeData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
                    <Tooltip content={<ChartTooltip valueSuffix=" projects" />} />
                    <Line type="monotone" dataKey="projects" stroke={colors.brand.accent} strokeWidth={2} dot={{ fill: colors.brand.accent, r: chart.dotRadius }} activeDot={{ r: chart.activeDotRadius }} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <EmptyChart label="Project volume will appear as submissions come in" />
              )}
            </div>
          </div>

          {/* --- Status Pie Chart --- */}
          <div className="glass rounded-xl p-6 border border-border">
            <SectionTitle>Project Status Breakdown</SectionTitle>
            {pieData.length > 0 ? (
              <div className="flex flex-col md:flex-row items-center gap-8">
                <ResponsiveContainer width="100%" height={chart.heightPie} className="max-w-xs">
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={chart.innerRadius} outerRadius={chart.outerRadius} paddingAngle={3} dataKey="value">
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill || PIE_FALLBACK_COLORS[index % PIE_FALLBACK_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      content={({ active, payload }) => active && payload?.length ? (
                        <div className="glass rounded-lg px-4 py-3 border border-border text-sm">
                          <p className="font-semibold" style={{ color: payload[0].payload.fill }}>{payload[0].name}</p>
                          <p className="text-text-primary">{payload[0].value} projects</p>
                        </div>
                      ) : null}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex flex-col gap-3 flex-1">
                  {pieData.map((entry) => (
                    <div key={entry.name} className="flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.fill }} />
                        <span className="text-sm text-text-primary">{entry.name}</span>
                      </div>
                      <span className="text-sm font-semibold text-text-primary">{entry.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <EmptyChart label="Status breakdown will appear once projects exist" />
            )}
          </div>

        </div>
      )}

      {/* Reused Modal for Project Details */}
      <ProjectDetailsModal 
        isOpen={isDetailsModalOpen}
        onClose={() => setIsDetailsModalOpen(false)}
        projectId={selectedProjectId}
      />
    </AppLayout>
  );
}
