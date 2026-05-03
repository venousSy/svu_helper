import { useState, useEffect } from 'react';
import AppLayout from '../components/layout/AppLayout';
import DataTable from '../components/ui/DataTable';
import { Search, AlertCircle, CheckCircle, XCircle, X } from 'lucide-react';
import { useProjects } from '../hooks/useProjects';
import { useProjectMutations } from '../hooks/useProjectMutations';
import OfferModal from '../components/projects/OfferModal';
import ConfirmActionModal from '../components/projects/ConfirmActionModal';
import ProjectDetailsModal from '../components/projects/ProjectDetailsModal';

export default function Projects() {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState('');
  const [studentId, setStudentId] = useState('');
  const [debouncedStudentId, setDebouncedStudentId] = useState('');

  // Modals state
  const [selectedProject, setSelectedProject] = useState(null);
  const [isOfferModalOpen, setIsOfferModalOpen] = useState(false);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [confirmModalState, setConfirmModalState] = useState({ isOpen: false, action: null, title: '', message: '', confirmText: '', isDestructive: false });

  // Toast state
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      setDebouncedStudentId(studentId);
      setPage(1);
    }, 500);

    return () => clearTimeout(delayDebounceFn);
  }, [studentId]);

  const { data, isLoading, isError, error, refetch } = useProjects(page, pageSize, statusFilter, debouncedStudentId);
  const { sendOffer, denyProject, finishProject } = useProjectMutations();

  const handleSearchChange = (e) => setStudentId(e.target.value);
  const handleStatusChange = (e) => {
    setStatusFilter(e.target.value);
    setPage(1);
  };

  const handleSendOffer = (project) => {
    setSelectedProject(project);
    setIsOfferModalOpen(true);
  };

  const handleViewDetails = (project) => {
    setSelectedProject(project);
    setIsDetailsModalOpen(true);
  };

  const handleDeny = (project) => {
    setSelectedProject(project);
    setConfirmModalState({
      isOpen: true,
      action: 'deny',
      title: `Deny Project #${project.id}`,
      message: 'Are you sure you want to deny this project? The student will be notified and this action cannot be undone.',
      confirmText: 'Deny Project',
      isDestructive: true
    });
  };

  const handleFinish = (project) => {
    setSelectedProject(project);
    setConfirmModalState({
      isOpen: true,
      action: 'finish',
      title: `Finish Project #${project.id}`,
      message: 'Are you sure you want to mark this project as finished? The student will be notified to check their dashboard.',
      confirmText: 'Mark Finished',
      isDestructive: false
    });
  };

  const submitOffer = (offerData) => {
    sendOffer.mutate(
      { projId: selectedProject.id, data: offerData },
      {
        onSuccess: () => showToast(`Offer sent successfully for project #${selectedProject.id}`),
        onError: (err) => showToast(err.response?.data?.detail || 'Failed to send offer', 'error'),
      }
    );
  };

  const confirmAction = () => {
    if (confirmModalState.action === 'deny') {
      denyProject.mutate(selectedProject.id, {
        onSuccess: () => showToast(`Project #${selectedProject.id} denied successfully`),
        onError: (err) => showToast(err.response?.data?.detail || 'Failed to deny project', 'error'),
      });
    } else if (confirmModalState.action === 'finish') {
      finishProject.mutate(selectedProject.id, {
        onSuccess: () => showToast(`Project #${selectedProject.id} marked as finished`),
        onError: (err) => showToast(err.response?.data?.detail || 'Failed to finish project', 'error'),
      });
    }
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
    {
      header: 'Actions',
      render: (row) => (
        <div className="flex items-center gap-2">
          <button 
            onClick={() => handleViewDetails(row)}
            className="px-3 py-1 text-xs font-medium rounded-md bg-surface-elevated border border-border text-text-primary hover:bg-border transition-colors"
          >
            Details
          </button>
          {row.status === 'pending' && (
            <>
              <button 
                onClick={() => handleSendOffer(row)}
                className="px-3 py-1 text-xs font-medium rounded-md bg-brand-primary/10 text-brand-primary hover:bg-brand-primary/20 transition-colors"
              >
                Offer
              </button>
              <button 
                onClick={() => handleDeny(row)}
                className="px-3 py-1 text-xs font-medium rounded-md bg-red-500/10 text-red-500 hover:bg-red-500/20 transition-colors"
              >
                Deny
              </button>
            </>
          )}
          {row.status === 'accepted' && (
            <button 
              onClick={() => handleFinish(row)}
              className="px-3 py-1 text-xs font-medium rounded-md bg-status-finished/10 text-status-finished hover:bg-status-finished/20 transition-colors"
            >
              Finish
            </button>
          )}
        </div>
      )
    }
  ];

  return (
    <AppLayout title="Projects">
      {/* Toast Notification */}
      {toast && (
        <div className={`fixed bottom-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg border shadow-lg animate-in slide-in-from-bottom-5 ${
          toast.type === 'error' 
            ? 'bg-red-50 border-red-200 text-red-700' 
            : 'bg-green-50 border-green-200 text-green-700'
        }`}>
          {toast.type === 'error' ? <XCircle size={20} /> : <CheckCircle size={20} />}
          <span className="text-sm font-medium">{toast.message}</span>
          <button onClick={() => setToast(null)} className="ml-2 text-current opacity-70 hover:opacity-100">
            <X size={16} />
          </button>
        </div>
      )}

      {isError && (
        <div className="flex items-center gap-3 mb-6 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          <AlertCircle size={18} className="shrink-0" />
          Failed to load projects. {error?.message}
          <button onClick={refetch} className="ml-auto underline hover:no-underline">Retry</button>
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
        data={data?.items || []} 
        loading={isLoading} 
        total={data?.total || 0} 
        page={page} 
        pageSize={pageSize} 
        onPageChange={setPage} 
      />

      <OfferModal 
        isOpen={isOfferModalOpen}
        onClose={() => setIsOfferModalOpen(false)}
        onSubmit={submitOffer}
        project={selectedProject}
      />

      <ProjectDetailsModal 
        isOpen={isDetailsModalOpen}
        onClose={() => setIsDetailsModalOpen(false)}
        projectId={selectedProject?.id}
      />

      <ConfirmActionModal 
        isOpen={confirmModalState.isOpen}
        onClose={() => setConfirmModalState(prev => ({ ...prev, isOpen: false }))}
        onConfirm={confirmAction}
        title={confirmModalState.title}
        message={confirmModalState.message}
        confirmText={confirmModalState.confirmText}
        isDestructive={confirmModalState.isDestructive}
      />
    </AppLayout>
  );
}
