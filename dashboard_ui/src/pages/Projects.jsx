import { useState, useEffect } from 'react';
import AppLayout from '../components/layout/AppLayout';
import DataTable from '../components/ui/DataTable';
import apiClient from '../api/client';
import { Search, AlertCircle } from 'lucide-react';

export default function Projects() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState('');
  const [studentId, setStudentId] = useState('');

  const fetchProjects = async () => {
    setLoading(true);
    setApiError(null);
    try {
      const params = { page, size: pageSize };
      if (statusFilter) params.status = statusFilter;
      if (studentId) params.student_id = studentId;

      const res = await apiClient.get('/projects/', { params });
      setData(Array.isArray(res.data?.items) ? res.data.items : []);
      setTotal(res.data?.total ?? 0);
    } catch (err) {
      console.error('Failed to fetch projects', err);
      setApiError('Failed to load projects. Please try again.');
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [page, statusFilter]);

  // Use a delay for search to avoid spamming the backend
  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (page !== 1) {
        setPage(1); // will trigger the other effect
      } else {
        fetchProjects();
      }
    }, 500);

    return () => clearTimeout(delayDebounceFn);
  }, [studentId]);

  const handleSearchChange = (e) => {
    setStudentId(e.target.value);
  };

  const handleStatusChange = (e) => {
    setStatusFilter(e.target.value);
    setPage(1);
  };

  const columns = [
    { header: 'ID', accessor: 'id' },
    { 
      header: 'Student', 
      render: (row) => (
        <div>
          <p className="text-text-primary font-medium">{row.user_full_name || row.username || 'Unknown'}</p>
          <p className="text-xs text-text-muted">{row.user_id}</p>
        </div>
      )
    },
    { header: 'Subject', accessor: 'subject_name' },
    { 
      header: 'Status', 
      render: (row) => {
        const bgColors = {
          pending: 'bg-status-pending/20 text-status-pending',
          offered: 'bg-status-offered/20 text-status-offered',
          accepted: 'bg-status-accepted/20 text-status-accepted',
          finished: 'bg-status-finished/20 text-status-finished',
          denied: 'bg-status-denied/20 text-status-denied',
        };
        const colorClass = bgColors[row.status] || 'bg-surface-elevated text-text-secondary';
        return (
          <span className={`px-2.5 py-1 rounded-full text-xs font-medium uppercase tracking-wider ${colorClass}`}>
            {row.status}
          </span>
        );
      }
    },
    { 
      header: 'Deadline', 
      render: (row) => <span className="text-text-secondary">{row.deadline}</span>
    },
    { 
      header: 'Price', 
      render: (row) => <span className="text-text-primary font-medium">{row.price ? `${row.price.toLocaleString()} SP` : '-'}</span>
    },
  ];

  return (
    <AppLayout title="Projects">
      {apiError && (
        <div className="flex items-center gap-3 mb-6 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          <AlertCircle size={18} className="shrink-0" />
          {apiError}
          <button onClick={fetchProjects} className="ml-auto underline hover:no-underline">Retry</button>
        </div>
      )}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="relative flex-1 max-w-sm">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search size={18} className="text-text-muted" />
          </div>
          <input
            type="number"
            placeholder="Search by Student ID..."
            value={studentId}
            onChange={handleSearchChange}
            className="w-full pl-10 pr-4 py-2.5 bg-surface-elevated border border-border rounded-lg text-sm text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-brand-primary/50 transition-all"
          />
        </div>
        
        <div className="relative">
            <select
            value={statusFilter}
            onChange={handleStatusChange}
            className="px-4 py-2.5 bg-surface-elevated border border-border rounded-lg text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/50 transition-all appearance-none pr-10"
            >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="offered">Offered</option>
            <option value="accepted">Accepted</option>
            <option value="finished">Finished</option>
            <option value="denied">Denied</option>
            </select>
        </div>
      </div>

      <DataTable 
        columns={columns} 
        data={data} 
        loading={loading} 
        total={total} 
        page={page} 
        pageSize={pageSize} 
        onPageChange={setPage} 
      />
    </AppLayout>
  );
}
