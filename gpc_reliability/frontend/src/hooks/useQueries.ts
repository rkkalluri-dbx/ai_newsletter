/**
 * React Query hooks for data fetching
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  dashboardApi,
  projectsApi,
  vendorsApi,
  alertsApi,
  milestonesApi,
  ganttApi,
  ProjectListParams,
  AlertListParams,
} from '../services/api';

// Query keys for cache management
export const queryKeys = {
  // Dashboard
  dashboardSummary: ['dashboard', 'summary'] as const,
  dashboardNextActions: (limit?: number) => ['dashboard', 'next-actions', limit] as const,
  dashboardStatusDistribution: ['dashboard', 'status-distribution'] as const,
  dashboardRegionDistribution: ['dashboard', 'region-distribution'] as const,
  dashboardVendorPerformance: (limit?: number) => ['dashboard', 'vendor-performance', limit] as const,
  dashboardRecentActivity: (limit?: number) => ['dashboard', 'recent-activity', limit] as const,

  // Projects
  projects: (params?: ProjectListParams) => ['projects', params] as const,
  project: (id: string) => ['projects', id] as const,
  projectHistory: (id: string) => ['projects', id, 'history'] as const,

  // Vendors
  vendors: (params?: { active_only?: boolean; search?: string }) => ['vendors', params] as const,
  vendor: (id: string) => ['vendors', id] as const,
  vendorMetrics: (id: string) => ['vendors', id, 'metrics'] as const,
  vendorProjects: (id: string) => ['vendors', id, 'projects'] as const,

  // Alerts
  alerts: (params?: AlertListParams) => ['alerts', params] as const,
  alert: (id: string) => ['alerts', id] as const,
  alertStats: ['alerts', 'stats'] as const,

  // Milestones
  milestones: (params?: Record<string, unknown>) => ['milestones', params] as const,
  milestone: (id: string) => ['milestones', id] as const,
  milestonesOverdue: (limit?: number) => ['milestones', 'overdue', limit] as const,
  milestonesUpcoming: (days?: number, limit?: number) => ['milestones', 'upcoming', days, limit] as const,

  // Gantt
  ganttData: (params?: Record<string, unknown>) => ['gantt', params] as const,
  ganttTimeline: (params?: Record<string, unknown>) => ['gantt', 'timeline', params] as const,
};

// Dashboard hooks
export function useDashboardSummary() {
  return useQuery({
    queryKey: queryKeys.dashboardSummary,
    queryFn: () => dashboardApi.getSummary().then((res) => res.data),
  });
}

export function useDashboardNextActions(limit?: number) {
  return useQuery({
    queryKey: queryKeys.dashboardNextActions(limit),
    queryFn: () => dashboardApi.getNextActions(limit).then((res) => res.data),
  });
}

export function useDashboardStatusDistribution() {
  return useQuery({
    queryKey: queryKeys.dashboardStatusDistribution,
    queryFn: () => dashboardApi.getStatusDistribution().then((res) => res.data),
  });
}

export function useDashboardRegionDistribution() {
  return useQuery({
    queryKey: queryKeys.dashboardRegionDistribution,
    queryFn: () => dashboardApi.getRegionDistribution().then((res) => res.data),
  });
}

export function useDashboardVendorPerformance(limit?: number) {
  return useQuery({
    queryKey: queryKeys.dashboardVendorPerformance(limit),
    queryFn: () => dashboardApi.getVendorPerformance(limit).then((res) => res.data),
  });
}

export function useDashboardRecentActivity(limit?: number) {
  return useQuery({
    queryKey: queryKeys.dashboardRecentActivity(limit),
    queryFn: () => dashboardApi.getRecentActivity(limit).then((res) => res.data),
  });
}

// Projects hooks
export function useProjects(params?: ProjectListParams) {
  return useQuery({
    queryKey: queryKeys.projects(params),
    queryFn: () => projectsApi.list(params).then((res) => res.data),
  });
}

export function useProject(id: string) {
  return useQuery({
    queryKey: queryKeys.project(id),
    queryFn: () => projectsApi.get(id).then((res) => res.data),
    enabled: !!id,
  });
}

export function useProjectHistory(id: string) {
  return useQuery({
    queryKey: queryKeys.projectHistory(id),
    queryFn: () => projectsApi.getHistory(id).then((res) => res.data),
    enabled: !!id,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => projectsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}

export function useUpdateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      projectsApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.project(id) });
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => projectsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}

// Vendors hooks
export function useVendors(params?: { active_only?: boolean; search?: string }) {
  return useQuery({
    queryKey: queryKeys.vendors(params),
    queryFn: () => vendorsApi.list(params).then((res) => res.data),
  });
}

export function useVendor(id: string) {
  return useQuery({
    queryKey: queryKeys.vendor(id),
    queryFn: () => vendorsApi.get(id).then((res) => res.data),
    enabled: !!id,
  });
}

export function useVendorMetrics(id: string) {
  return useQuery({
    queryKey: queryKeys.vendorMetrics(id),
    queryFn: () => vendorsApi.getMetrics(id).then((res) => res.data),
    enabled: !!id,
  });
}

export function useVendorProjects(id: string) {
  return useQuery({
    queryKey: queryKeys.vendorProjects(id),
    queryFn: () => vendorsApi.getProjects(id).then((res) => res.data),
    enabled: !!id,
  });
}

export function useCreateVendor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => vendorsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendors'] });
    },
  });
}

export function useUpdateVendor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      vendorsApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.vendor(id) });
      queryClient.invalidateQueries({ queryKey: ['vendors'] });
    },
  });
}

// Alerts hooks
export function useAlerts(params?: AlertListParams) {
  return useQuery({
    queryKey: queryKeys.alerts(params),
    queryFn: () => alertsApi.list(params).then((res) => res.data),
  });
}

export function useAlert(id: string) {
  return useQuery({
    queryKey: queryKeys.alert(id),
    queryFn: () => alertsApi.get(id).then((res) => res.data),
    enabled: !!id,
  });
}

export function useAlertStats() {
  return useQuery({
    queryKey: queryKeys.alertStats,
    queryFn: () => alertsApi.getStats().then((res) => res.data),
  });
}

export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, user_email }: { id: string; user_email?: string }) =>
      alertsApi.acknowledge(id, user_email),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}

export function useBulkAcknowledgeAlerts() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ alert_ids, user_email }: { alert_ids: string[]; user_email?: string }) =>
      alertsApi.bulkAcknowledge(alert_ids, user_email),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}

export function useCreateAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { project_id: string; alert_type: string; message: string; severity?: string }) =>
      alertsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}

// Milestones hooks
export function useMilestones(params?: { project_id?: string; stage?: string; is_overdue?: boolean; completed?: boolean }) {
  return useQuery({
    queryKey: queryKeys.milestones(params),
    queryFn: () => milestonesApi.list(params).then((res) => res.data),
    placeholderData: (previousData) => previousData, // Keep previous data during refetch
  });
}

export function useMilestone(id: string) {
  return useQuery({
    queryKey: queryKeys.milestone(id),
    queryFn: () => milestonesApi.get(id).then((res) => res.data),
    enabled: !!id,
  });
}

export function useOverdueMilestones(limit?: number) {
  return useQuery({
    queryKey: queryKeys.milestonesOverdue(limit),
    queryFn: () => milestonesApi.getOverdue(limit).then((res) => res.data),
  });
}

export function useUpcomingMilestones(days?: number, limit?: number) {
  return useQuery({
    queryKey: queryKeys.milestonesUpcoming(days, limit),
    queryFn: () => milestonesApi.getUpcoming(days, limit).then((res) => res.data),
  });
}

export function useCompleteMilestone() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, actual_date }: { id: string; actual_date?: string }) =>
      milestonesApi.complete(id, actual_date),
    onMutate: async ({ id }) => {
      // Cancel outgoing refetches to prevent overwriting optimistic update
      await queryClient.cancelQueries({ queryKey: ['milestones'] });

      // Snapshot previous milestones data for rollback
      const previousMilestones = queryClient.getQueriesData({ queryKey: ['milestones'] });

      // Optimistically update milestone to completed
      queryClient.setQueriesData({ queryKey: ['milestones'] }, (old: unknown) => {
        if (!old || typeof old !== 'object') return old;
        const data = old as { data?: Array<{ milestone_id?: string; id?: string; completed?: boolean; actual_date?: string | null }> };
        if (!data.data) return old;
        return {
          ...data,
          data: data.data.map((m) =>
            (m.milestone_id === id || m.id === id)
              ? { ...m, completed: true, actual_date: new Date().toISOString().split('T')[0] }
              : m
          ),
        };
      });

      return { previousMilestones };
    },
    onError: (_err, _vars, context) => {
      // Rollback on error
      if (context?.previousMilestones) {
        context.previousMilestones.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
    },
    onSettled: () => {
      // Refetch after mutation settles to ensure server state
      queryClient.invalidateQueries({ queryKey: ['milestones'] });
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}

// Gantt hooks
export function useGanttData(params?: { vendor_id?: string; region?: string; status?: string; priority?: string; limit?: number }) {
  return useQuery({
    queryKey: queryKeys.ganttData(params),
    queryFn: () => ganttApi.getData(params).then((res) => res.data),
  });
}

export function useGanttTimeline(params?: { start_date?: string; end_date?: string; view?: 'week' | 'month' | 'quarter' }) {
  return useQuery({
    queryKey: queryKeys.ganttTimeline(params),
    queryFn: () => ganttApi.getTimeline(params).then((res) => res.data),
  });
}
