import { useState } from 'react';
import { X, FileText, Download, Calendar, DollarSign, Clock, User, FileImage, FileVideo, File } from 'lucide-react';
import { useProjectDetails } from '../../hooks/useProjects';
import apiClient from '../../api/client';

export default function ProjectDetailsModal({ isOpen, onClose, projectId }) {
  const { data: project, isLoading, isError } = useProjectDetails(isOpen ? projectId : null);
  const [downloading, setDownloading] = useState(null);

  if (!isOpen) return null;

  const handleDownload = async (fileId, fileName) => {
    setDownloading(fileId);
    try {
      const response = await apiClient.get(`/files/${fileId}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName || 'download');
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (err) {
      console.error('Download failed', err);
      alert('Failed to download file.');
    } finally {
      setDownloading(null);
    }
  };

  const getFileIcon = (fileType) => {
    if (!fileType) return <File size={16} />;
    if (fileType.includes('image')) return <FileImage size={16} />;
    if (fileType.includes('video')) return <FileVideo size={16} />;
    return <FileText size={16} />;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="bg-surface-base rounded-xl shadow-xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-200"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-border bg-surface-elevated">
          <div>
            <h2 className="text-lg font-semibold text-text-primary">Project Details</h2>
            <p className="text-sm text-text-muted">ID: {projectId}</p>
          </div>
          <button 
            onClick={onClose}
            className="p-2 text-text-muted hover:text-text-primary hover:bg-border rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-6 overflow-y-auto space-y-6">
          {isLoading ? (
            <div className="flex justify-center items-center py-12">
              <div className="w-8 h-8 border-4 border-brand-primary/30 border-t-brand-primary rounded-full animate-spin"></div>
            </div>
          ) : isError || !project ? (
            <div className="p-4 text-red-500 bg-red-500/10 rounded-lg border border-red-500/20 text-center">
              Failed to load project details.
            </div>
          ) : (
            <>
              {/* Header Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <div className="flex items-center text-sm text-text-muted gap-1.5"><User size={16} /> Student</div>
                  <div className="font-medium text-text-primary">{project.user_full_name || project.username || 'Unknown'}</div>
                  <div className="text-sm text-text-secondary">{project.user_id}</div>
                </div>
                <div className="space-y-1">
                  <div className="flex items-center text-sm text-text-muted gap-1.5"><FileText size={16} /> Subject</div>
                  <div className="font-medium text-text-primary">{project.subject_name}</div>
                  <div className="text-sm text-text-secondary">Tutor: {project.tutor_name}</div>
                </div>
              </div>

              {/* Status and Dates */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-surface-elevated rounded-lg border border-border">
                <div>
                  <div className="text-xs text-text-muted uppercase tracking-wider mb-1">Status</div>
                  <div className="font-medium text-text-primary uppercase">{project.status}</div>
                </div>
                <div>
                  <div className="text-xs text-text-muted uppercase tracking-wider mb-1 flex items-center gap-1"><Calendar size={12}/> Deadline</div>
                  <div className="font-medium text-text-primary">{project.deadline}</div>
                </div>
                <div>
                  <div className="text-xs text-text-muted uppercase tracking-wider mb-1 flex items-center gap-1"><DollarSign size={12}/> Price</div>
                  <div className="font-medium text-text-primary">{project.price ? `${project.price.toLocaleString()} SP` : '-'}</div>
                </div>
                <div>
                  <div className="text-xs text-text-muted uppercase tracking-wider mb-1 flex items-center gap-1"><Clock size={12}/> Delivery</div>
                  <div className="font-medium text-text-primary">{project.delivery_date || '-'}</div>
                </div>
              </div>

              {/* Details Text */}
              <div>
                <h3 className="text-sm font-medium text-text-muted mb-2 uppercase tracking-wider">Requirements</h3>
                <div className="p-4 bg-surface-elevated border border-border rounded-lg text-text-primary text-sm whitespace-pre-wrap">
                  {project.details || 'No details provided.'}
                </div>
              </div>

              {/* Attachments */}
              <div>
                <h3 className="text-sm font-medium text-text-muted mb-2 uppercase tracking-wider">Attachments ({project.attachments?.length || 0})</h3>
                {project.attachments?.length > 0 ? (
                  <div className="flex flex-col gap-2">
                    {project.attachments.map((file, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-surface-elevated border border-border rounded-lg">
                        <div className="flex items-center gap-3 text-sm text-text-primary truncate">
                          {getFileIcon(file.type || file.mime_type)}
                          <span className="truncate max-w-[200px] sm:max-w-[300px]">
                            {file.file_name || `Attachment ${idx + 1}`}
                          </span>
                        </div>
                        <button 
                          onClick={() => handleDownload(file.file_id, file.file_name || `attachment_${idx + 1}`)}
                          disabled={downloading === file.file_id}
                          className="flex items-center gap-1.5 px-3 py-1.5 bg-brand-primary/10 text-brand-primary hover:bg-brand-primary/20 rounded-md text-xs font-medium transition-colors disabled:opacity-50"
                        >
                          {downloading === file.file_id ? 'Downloading...' : <><Download size={14} /> Download</>}
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-text-secondary">No attachments.</div>
                )}
              </div>

              {/* Payment Proof */}
              {project.payment && (
                <div>
                  <h3 className="text-sm font-medium text-text-muted mb-2 uppercase tracking-wider">Payment Proof</h3>
                  <div className="flex items-center justify-between p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                    <div className="flex items-center gap-3 text-sm text-green-600 dark:text-green-400 font-medium">
                      {getFileIcon(project.payment.file_type)}
                      <span>Payment Screenshot ({project.payment.status})</span>
                    </div>
                    <button 
                      onClick={() => handleDownload(project.payment.file_id, `payment_${project.id}`)}
                      disabled={downloading === project.payment.file_id}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-green-500/20 text-green-700 dark:text-green-400 hover:bg-green-500/30 rounded-md text-xs font-medium transition-colors disabled:opacity-50"
                    >
                      {downloading === project.payment.file_id ? 'Downloading...' : <><Download size={14} /> Download</>}
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
