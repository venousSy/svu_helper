import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import SkeletonLoader from './SkeletonLoader';

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
    <div className="flex flex-col w-full bg-surface-elevated/50 backdrop-blur-md border border-border rounded-xl overflow-hidden shadow-[0_8px_32px_rgba(0,0,0,0.4)]">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-base/80 border-b border-border text-xs uppercase tracking-widest text-text-muted font-bold">
              {columns.map((col, i) => (
                <th key={i} className="px-6 py-5">
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border/50 text-sm text-text-secondary relative">
            <AnimatePresence mode="wait">
              {loading ? (
                <motion.tr
                  key="loading"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <td colSpan={columns.length} className="p-0">
                    <div className="divide-y divide-border/50">
                      {[1, 2, 3, 4, 5].map(i => (
                        <div key={i} className="flex px-6 py-4 gap-4">
                          {columns.map((_, j) => (
                            <SkeletonLoader key={j} className="h-5 flex-1" />
                          ))}
                        </div>
                      ))}
                    </div>
                  </td>
                </motion.tr>
              ) : data.length === 0 ? (
                <motion.tr
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <td colSpan={columns.length} className="px-6 py-16 text-center">
                    <p className="text-text-muted text-lg">No records found.</p>
                  </td>
                </motion.tr>
              ) : (
                data.map((row, rowIndex) => (
                  <motion.tr 
                    key={row.id || rowIndex} 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: rowIndex * 0.03, duration: 0.2 }}
                    className="hover:bg-brand-primary/5 transition-colors duration-normal group"
                  >
                    {columns.map((col, colIndex) => (
                      <td key={colIndex} className="px-6 py-4 whitespace-nowrap transition-colors group-hover:text-text-primary">
                        {col.render ? col.render(row) : row[col.accessor]}
                      </td>
                    ))}
                  </motion.tr>
                ))
              )}
            </AnimatePresence>
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {!loading && total > 0 && (
        <div className="flex items-center justify-between px-6 py-4 border-t border-border bg-surface-base/80">
          <p className="text-sm text-text-muted">
            Showing <span className="font-semibold text-text-primary">{(page - 1) * pageSize + 1}</span> to{' '}
            <span className="font-semibold text-text-primary">
              {Math.min(page * pageSize, total)}
            </span>{' '}
            of <span className="font-semibold text-text-primary">{total}</span>
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="p-2 rounded-lg text-text-secondary hover:text-white hover:bg-surface-elevated disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft size={18} />
            </button>
            <span className="text-sm text-text-primary font-medium px-3 py-1 bg-surface-elevated rounded-md border border-border">
              {page} / {totalPages}
            </span>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="p-2 rounded-lg text-text-secondary hover:text-white hover:bg-surface-elevated disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
