import React from 'react';
import { ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';

export default function DataTable({ 
  columns, 
  data, 
  loading, 
  total, 
  page, 
  pageSize, 
  onPageChange 
}) {
  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="flex flex-col w-full bg-surface-elevated border border-border rounded-xl overflow-hidden shadow-lg">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-base border-b border-border text-xs uppercase tracking-wider text-text-muted">
              {columns.map((col, i) => (
                <th key={i} className="px-6 py-4 font-semibold">
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border text-sm text-text-secondary">
            {loading ? (
              <tr>
                <td colSpan={columns.length} className="px-6 py-12 text-center">
                  <div className="flex flex-col items-center justify-center gap-3">
                    <Loader2 className="w-8 h-8 text-brand-primary animate-spin" />
                    <p className="text-text-muted">Loading data...</p>
                  </div>
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-6 py-12 text-center">
                  <p className="text-text-muted">No records found.</p>
                </td>
              </tr>
            ) : (
              data.map((row, rowIndex) => (
                <tr key={rowIndex} className="hover:bg-surface-base/50 transition-colors duration-fast">
                  {columns.map((col, colIndex) => (
                    <td key={colIndex} className="px-6 py-4 whitespace-nowrap">
                      {col.render ? col.render(row) : row[col.accessor]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {!loading && total > 0 && (
        <div className="flex items-center justify-between px-6 py-4 border-t border-border bg-surface-base">
          <p className="text-sm text-text-muted">
            Showing <span className="font-medium text-text-primary">{(page - 1) * pageSize + 1}</span> to{' '}
            <span className="font-medium text-text-primary">
              {Math.min(page * pageSize, total)}
            </span>{' '}
            of <span className="font-medium text-text-primary">{total}</span> results
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-elevated disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft size={18} />
            </button>
            <span className="text-sm text-text-primary font-medium px-2">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-elevated disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
