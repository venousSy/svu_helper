import { useState, useEffect } from 'react';
import { X } from 'lucide-react';

export default function OfferModal({ isOpen, onClose, onSubmit, project }) {
  const [price, setPrice] = useState('');
  const [delivery, setDelivery] = useState('');
  const [notes, setNotes] = useState('');
  
  useEffect(() => {
    if (isOpen) {
      setPrice('');
      setDelivery('');
      setNotes('');
    }
  }, [isOpen]);

  if (!isOpen || !project) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!price || !delivery) return;
    onSubmit({ price: parseInt(price, 10), delivery, notes });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
      <div className="bg-surface border border-border rounded-xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="flex justify-between items-center p-4 border-b border-border">
          <h3 className="text-lg font-semibold text-text-primary">Send Offer: #{project.id}</h3>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary transition-colors">
            <X size={20} />
          </button>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">Price (SP) *</label>
              <input
                type="number"
                required
                min="0"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="e.g. 50000"
                className="w-full px-3 py-2 bg-surface-elevated border border-border rounded-lg text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/50 transition-all"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">Delivery Date *</label>
              <input
                type="date"
                required
                value={delivery}
                onChange={(e) => setDelivery(e.target.value)}
                className="w-full px-3 py-2 bg-surface-elevated border border-border rounded-lg text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/50 transition-all"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">Notes (Optional)</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add any additional notes for the student..."
                rows={3}
                className="w-full px-3 py-2 bg-surface-elevated border border-border rounded-lg text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/50 transition-all resize-none"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 p-4 border-t border-border bg-surface-elevated">
            <button 
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-sm font-medium text-text-secondary hover:text-text-primary bg-transparent hover:bg-surface transition-colors"
            >
              Cancel
            </button>
            <button 
              type="submit"
              disabled={!price || !delivery}
              className="px-4 py-2 rounded-lg text-sm font-medium text-white shadow-sm bg-brand-primary hover:bg-brand-secondary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send Offer
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
