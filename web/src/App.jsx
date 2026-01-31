import React, { useState, useEffect } from 'react';
import { Package, Clock, CheckCircle, XCircle, AlertCircle, FileText, Send } from 'lucide-react';

const API_URL = '/api'; // Proxied via Vite

export default function App() {
  const [projects, setProjects] = useState({
    "New / Pending": [],
    "Offered / Waiting": [],
    "Ongoing": [],
    "History": []
  });
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState(null);

  // Offer Form State
  const [price, setPrice] = useState('');
  const [delivery, setDelivery] = useState('');

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/projects`);
      const data = await res.json();
      setProjects(data);
    } catch (err) {
      console.error("Failed to fetch projects", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
    const interval = setInterval(fetchProjects, 10000); // Poll every 10s
    return () => clearInterval(interval);
  }, []);

  const handleSendOffer = async () => {
    if (!selectedProject || !price || !delivery) return;
    
    try {
      await fetch(`${API_URL}/projects/${selectedProject.id}/offer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ price, delivery_date: delivery })
      });
      alert("Offer sent!");
      setSelectedProject(null);
      fetchProjects();
    } catch (err) {
      alert("Failed to send offer");
    }
  };

  return (
    <div className="flex h-screen bg-background text-gray-100 font-sans">
      {/* Sidebar */}
      <div className="w-64 bg-surface border-r border-gray-700 p-4 flex flex-col">
        <h1 className="text-xl font-bold flex items-center gap-2 mb-8 text-primary">
          <Package /> SVU Admin
        </h1>
        <nav className="flex-1 space-y-2">
          <button onClick={fetchProjects} className="w-full text-left p-3 rounded hover:bg-gray-700 flex items-center gap-2">
             <Clock size={18} /> Refresh Data
          </button>
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-8">
        <header className="mb-8">
            <h2 className="text-3xl font-bold">Dashboard</h2>
            <p className="text-gray-400">Manage student requests and payments.</p>
        </header>

        {loading && <p>Loading...</p>}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatusColumn title="Pending" icon={<AlertCircle className="text-yellow-500"/>} items={projects["New / Pending"]} onSelect={setSelectedProject} />
            <StatusColumn title="Offered" icon={<FileText className="text-blue-500"/>} items={projects["Offered / Waiting"]} onSelect={setSelectedProject} />
            <StatusColumn title="Ongoing" icon={<CheckCircle className="text-green-500"/>} items={projects["Ongoing"]} onSelect={setSelectedProject} />
            <StatusColumn title="History" icon={<XCircle className="text-gray-500"/>} items={projects["History"]} onSelect={setSelectedProject} />
        </div>
      </div>

      {/* Modal / Detail View */}
      {selectedProject && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-surface p-6 rounded-xl w-full max-w-lg shadow-2xl border border-gray-700">
                <div className="flex justify-between items-start mb-4">
                    <h3 className="text-xl font-bold">Project #{selectedProject.id}</h3>
                    <button onClick={() => setSelectedProject(null)} className="text-gray-400 hover:text-white">✕</button>
                </div>
                
                <div className="space-y-3 mb-6">
                    <p><span className="text-gray-400">Subject:</span> {selectedProject.subject_name}</p>
                    <p><span className="text-gray-400">User:</span> {selectedProject.username || selectedProject.user_full_name}</p>
                    <p><span className="text-gray-400">Status:</span> <span className="px-2 py-0.5 rounded bg-gray-700 text-xs">{selectedProject.status}</span></p>
                    <div className="bg-black/30 p-3 rounded text-sm text-gray-300 max-h-32 overflow-auto">
                        {selectedProject.details}
                    </div>
                </div>

                {selectedProject.status === 'pending' && (
                    <div className="space-y-3 border-t border-gray-700 pt-4">
                        <h4 className="font-semibold text-primary">Make an Offer</h4>
                        <input 
                            placeholder="Price (e.g. 50,000 SYP)" 
                            className="w-full bg-black/30 border border-gray-600 rounded p-2 text-white"
                            value={price} onChange={e => setPrice(e.target.value)}
                        />
                        <input 
                            placeholder="Date (e.g. 2024-05-01)" 
                            className="w-full bg-black/30 border border-gray-600 rounded p-2 text-white"
                            value={delivery} onChange={e => setDelivery(e.target.value)}
                        />
                        <button onClick={handleSendOffer} className="w-full bg-primary hover:bg-blue-600 text-white font-bold py-2 rounded flex items-center justify-center gap-2">
                            <Send size={18}/> Send Offer
                        </button>
                    </div>
                )}
            </div>
        </div>
      )}
    </div>
  );
}

function StatusColumn({ title, icon, items, onSelect }) {
    return (
        <div className="bg-surface/50 rounded-xl p-4 min-h-[500px]">
            <h3 className="flex items-center gap-2 font-semibold mb-4 text-gray-300">{icon} {title} <span className="ml-auto bg-gray-700 px-2 rounded-full text-xs">{items?.length || 0}</span></h3>
            <div className="space-y-3">
                {items && items.map(p => (
                    <div key={p.id} onClick={() => onSelect(p)} className="bg-surface border border-gray-700 p-3 rounded hover:border-primary cursor-pointer transition-colors shadow-sm">
                        <div className="flex justify-between items-start">
                            <span className="font-bold text-sm">#{p.id}</span>
                            <span className="text-xs text-gray-500">{p.deadline}</span>
                        </div>
                        <p className="font-medium truncate mt-1">{p.subject_name}</p>
                        <p className="text-xs text-gray-400 mt-1 truncate">{p.user_full_name}</p>
                    </div>
                ))}
            </div>
        </div>
    )
}
