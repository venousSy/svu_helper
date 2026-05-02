import { useState } from 'react';
import { X } from 'lucide-react';

export default function ConfirmActionModal({ isOpen, onClose, onConfirm, title, message, confirmText, isDestructive }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
      <div className="bg-surface border border-border rounded-xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="flex justify-between items-center p-4 border-b border-border">
          <h3 className="text-lg font-semibold text-text-primary">{title}</h3>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary transition-colors">
            <X size={20} />
          </button>
        </div>
        
        <div className="p-6">
          <p className="text-text-secondary">{message}</p>
        </div>

        <div className="flex justify-end gap-3 p-4 border-t border-border bg-surface-elevated">
          <button 
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm font-medium text-text-secondary hover:text-text-primary bg-transparent hover:bg-surface transition-colors"
          >
            Cancel
          </button>
          <button 
            onClick={() => {
              onConfirm();
              onClose();
            }}
            className={`px-4 py-2 rounded-lg text-sm font-medium text-white shadow-sm transition-colors ${
              isDestructive 
                ? 'bg-red-500 hover:bg-red-600' 
                : 'bg-brand-primary hover:bg-brand-secondary'
            }`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
