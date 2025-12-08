/**
 * TypeScript type definitions for the GPC Reliability Tracker
 */

// Project lifecycle status
export type ProjectStatus =
  | 'authorized'
  | 'assigned_to_vendor'
  | 'design_submitted'
  | 'qa_qc'
  | 'approved'
  | 'construction_ready';

// Priority levels
export type Priority = 'low' | 'normal' | 'high' | 'critical';

// Alert severity
export type AlertSeverity = 'info' | 'warning' | 'critical';

// User roles
export type UserRole = 'viewer' | 'editor' | 'admin';

// Base entity with common fields
export interface BaseEntity {
  id: string;
  created_at: string;
  updated_at: string;
}

// Vendor entity
export interface Vendor extends BaseEntity {
  name: string;
  code: string;
  contact_name?: string;
  contact_email?: string;
  is_active: boolean;
}

// Project entity
export interface Project extends BaseEntity {
  work_order_number: string;
  vendor_id: string;
  vendor?: Vendor;
  description?: string;
  region?: string;
  status: ProjectStatus;
  priority: Priority;
  authorized_date?: string;
  sent_to_vendor_date?: string;
  received_from_vendor_date?: string;
  target_completion_date?: string;
  actual_completion_date?: string;
  revision_count: number;
  version: number;
}

// Milestone entity
export interface Milestone extends BaseEntity {
  project_id: string;
  stage: string;
  expected_date?: string;
  actual_date?: string;
  sla_days: number;
  is_overdue: boolean;
  days_overdue: number;
}

// Alert entity
export interface Alert extends BaseEntity {
  project_id: string;
  project?: Project;
  alert_type: string;
  message: string;
  severity: AlertSeverity;
  is_acknowledged: boolean;
}

// Vendor metrics
export interface VendorMetric extends BaseEntity {
  vendor_id: string;
  period_start: string;
  period_end: string;
  on_time_rate: number;
  avg_turnaround_days: number;
  revision_rate: number;
  total_projects: number;
}

// Audit log entry
export interface AuditLog extends BaseEntity {
  project_id: string;
  user_id: string;
  action: 'create' | 'update' | 'delete';
  field_changed?: string;
  old_value?: string;
  new_value?: string;
}

// API response wrapper
export interface ApiResponse<T> {
  data: T;
  total?: number;
  page?: number;
  per_page?: number;
}

// Dashboard summary
export interface DashboardSummary {
  total_projects: number;
  active_projects: number;
  overdue_projects: number;
  completed_projects: number;
}

// Next action item
export interface NextAction {
  project: Project;
  action: string;
  urgency: 'high' | 'medium' | 'low';
  days_overdue: number;
}

// Status period for Gantt chart timeline (represents a period in a specific status)
export interface StatusPeriod {
  status: string;
  status_label: string;
  start_date: string;
  end_date: string | null; // null if current/ongoing status
  is_completed: boolean;
  is_current: boolean;
  duration_days: number;
}

// View mode for Gantt chart timeline granularity
export type ViewMode = 'week' | 'month' | 'quarter' | 'year';
