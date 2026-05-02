import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/client';

export const projectKeys = {
  all: ['projects'],
  list: (params) => [...projectKeys.all, 'list', params],
};

export function useProjects(page, pageSize, statusFilter, studentId) {
  return useQuery({
    queryKey: projectKeys.list({ page, pageSize, statusFilter, studentId }),
    queryFn: async () => {
      const params = { page, size: pageSize };
      if (statusFilter) params.status = statusFilter;
      if (studentId) params.student_id = studentId;

      const res = await apiClient.get('/projects/', { params });
      return {
        items: Array.isArray(res.data?.items) ? res.data.items : [],
        total: res.data?.total ?? 0,
      };
    },
    keepPreviousData: true,
  });
}
