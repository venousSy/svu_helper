import { useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/client';
import { projectKeys } from './useProjects';

export function useProjectMutations() {
  const queryClient = useQueryClient();

  const updateCacheOptimistically = async (projId, updatedFields) => {
    await queryClient.cancelQueries({ queryKey: projectKeys.all });

    // Snapshot the previous value for rollback
    const previousQueries = queryClient.getQueriesData({ queryKey: projectKeys.all });

    // Optimistically update to the new value
    queryClient.setQueriesData({ queryKey: projectKeys.all }, (oldData) => {
      if (!oldData) return oldData;
      return {
        ...oldData,
        items: oldData.items.map(item => 
          item.id === projId ? { ...item, ...updatedFields } : item
        )
      };
    });

    return { previousQueries };
  };

  const onErrorRollback = (err, variables, context) => {
    if (context?.previousQueries) {
      context.previousQueries.forEach(([queryKey, oldData]) => {
        queryClient.setQueryData(queryKey, oldData);
      });
    }
  };

  const onSettledInvalidate = () => {
    queryClient.invalidateQueries({ queryKey: projectKeys.all });
  };

  const sendOffer = useMutation({
    mutationFn: async ({ projId, data }) => {
      const res = await apiClient.post(`/projects/${projId}/offer`, data);
      return res.data;
    },
    onMutate: async ({ projId, data }) => {
      return updateCacheOptimistically(projId, { 
        status: 'offered', 
        price: data.price, 
        delivery_date: data.delivery 
      });
    },
    onError: onErrorRollback,
    onSettled: onSettledInvalidate,
  });

  const denyProject = useMutation({
    mutationFn: async (projId) => {
      const res = await apiClient.post(`/projects/${projId}/deny`);
      return res.data;
    },
    onMutate: async (projId) => {
      return updateCacheOptimistically(projId, { status: 'denied' });
    },
    onError: onErrorRollback,
    onSettled: onSettledInvalidate,
  });

  const finishProject = useMutation({
    mutationFn: async (projId) => {
      const res = await apiClient.post(`/projects/${projId}/finish`);
      return res.data;
    },
    onMutate: async (projId) => {
      return updateCacheOptimistically(projId, { status: 'finished' });
    },
    onError: onErrorRollback,
    onSettled: onSettledInvalidate,
  });

  return { sendOffer, denyProject, finishProject };
}
