import { Grid, Paper, Typography, Box, Card, CardContent, Chip, Skeleton, Alert } from '@mui/material';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import {
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Business as BusinessIcon,
  Assignment as AssignmentIcon,
  OpenInNew as OpenInNewIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import {
  useDashboardSummary,
  useDashboardStatusDistribution,
  useDashboardRegionDistribution,
  useDashboardVendorPerformance,
  useDashboardNextActions,
  useDashboardRecentActivity,
} from '../hooks/useQueries';

// Color palette for charts - matches backend ProjectStatus values
const STATUS_COLORS: Record<string, string> = {
  authorized: '#2196F3',
  assigned_to_vendor: '#9C27B0',
  design_submitted: '#FF9800',
  qa_qc: '#00BCD4',
  approved: '#4CAF50',
  construction_ready: '#8BC34A',
};

const REGION_COLORS = ['#1976D2', '#388E3C', '#F57C00', '#7B1FA2', '#C2185B'];

interface SummaryCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  icon: React.ReactNode;
  color: string;
  loading?: boolean;
}

function SummaryCard({ title, value, subtitle, icon, color, loading }: SummaryCardProps) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box>
            <Typography color="text.secondary" variant="body2" gutterBottom>
              {title}
            </Typography>
            {loading ? (
              <Skeleton width={60} height={40} />
            ) : (
              <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
                {value}
              </Typography>
            )}
            {subtitle && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box
            sx={{
              backgroundColor: `${color}15`,
              borderRadius: 2,
              p: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Box sx={{ color }}>{icon}</Box>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

interface NextAction {
  type: string;
  priority: number;
  title: string;
  description: string;
  project_id: string;
  work_order_number?: string;
  alert_id?: string;
  milestone_id?: string;
  stage?: string;
  days_overdue?: number;
  days_until?: number;
  expected_date?: string;
  created_at?: string;
}

function NextActionsCard() {
  const { data, isLoading, error } = useDashboardNextActions(5);
  const navigate = useNavigate();

  const handleActionClick = (action: NextAction) => {
    if (action.project_id) {
      navigate(`/projects/${action.project_id}`);
    }
  };

  if (error) {
    return (
      <Paper sx={{ p: 2, height: '100%' }}>
        <Alert severity="error">Failed to load next actions</Alert>
      </Paper>
    );
  }

  const getActionColor = (type: string) => {
    switch (type) {
      case 'critical_alert':
        return { bg: '#FFEBEE', border: 'error.main' };
      case 'overdue_milestone':
        return { bg: '#FFF3E0', border: 'warning.main' };
      case 'approaching_milestone':
        return { bg: '#E3F2FD', border: 'info.main' };
      case 'warning_alert':
        return { bg: '#FFF8E1', border: 'warning.light' };
      default:
        return { bg: '#F5F5F5', border: 'grey.400' };
    }
  };

  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <ScheduleIcon color="primary" />
        Next Actions
      </Typography>
      {isLoading ? (
        Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} height={60} sx={{ mb: 1 }} />)
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
          {data?.data?.length === 0 ? (
            <Typography color="text.secondary">No pending actions</Typography>
          ) : (
            data?.data?.map((action: NextAction, index: number) => {
              const colors = getActionColor(action.type);
              return (
                <Box
                  key={`${action.project_id}-${action.type}-${index}`}
                  onClick={() => handleActionClick(action)}
                  sx={{
                    p: 1.5,
                    borderRadius: 1,
                    backgroundColor: colors.bg,
                    borderLeft: 4,
                    borderColor: colors.border,
                    cursor: 'pointer',
                    transition: 'all 0.2s ease-in-out',
                    '&:hover': {
                      transform: 'translateX(4px)',
                      boxShadow: 1,
                    },
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                  }}
                >
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="body2" fontWeight="medium">
                      {action.title}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {action.description}
                    </Typography>
                    {action.type === 'overdue_milestone' && action.days_overdue && (
                      <Chip
                        size="small"
                        label={`${action.days_overdue} days overdue`}
                        color="error"
                        sx={{ ml: 1, height: 20 }}
                      />
                    )}
                    {action.type === 'approaching_milestone' && action.days_until !== undefined && (
                      <Chip
                        size="small"
                        label={`${action.days_until} day(s) left`}
                        color="info"
                        sx={{ ml: 1, height: 20 }}
                      />
                    )}
                  </Box>
                  <OpenInNewIcon sx={{ fontSize: 16, color: 'text.secondary', ml: 1 }} />
                </Box>
              );
            })
          )}
        </Box>
      )}
    </Paper>
  );
}

interface RecentActivity {
  id: string;
  project_id: string;
  work_order_number?: string;
  action: string;
  description: string;
  user_email?: string;
  created_at?: string;
}

function RecentActivityCard() {
  const { data, isLoading, error } = useDashboardRecentActivity(5);
  const navigate = useNavigate();

  const handleActivityClick = (activity: RecentActivity) => {
    if (activity.project_id) {
      navigate(`/projects/${activity.project_id}`);
    }
  };

  if (error) {
    return (
      <Paper sx={{ p: 2, height: '100%' }}>
        <Alert severity="error">Failed to load recent activity</Alert>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <TrendingUpIcon color="primary" />
        Recent Activity
      </Typography>
      {isLoading ? (
        Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} height={50} sx={{ mb: 1 }} />)
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {data?.data?.length === 0 ? (
            <Typography color="text.secondary">No recent activity</Typography>
          ) : (
            data?.data?.map((activity: RecentActivity) => (
              <Box
                key={activity.id}
                onClick={() => handleActivityClick(activity)}
                sx={{
                  p: 1,
                  borderRadius: 1,
                  backgroundColor: '#F5F5F5',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    backgroundColor: '#EEEEEE',
                    transform: 'translateX(4px)',
                  },
                }}
              >
                <Box>
                  <Typography variant="body2" fontWeight="medium">
                    {activity.work_order_number || 'Project'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {activity.description}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    {activity.created_at ? new Date(activity.created_at).toLocaleDateString() : ''}
                  </Typography>
                  <OpenInNewIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
                </Box>
              </Box>
            ))
          )}
        </Box>
      )}
    </Paper>
  );
}

function StatusDistributionChart() {
  const { data, isLoading, error } = useDashboardStatusDistribution();

  if (error) {
    return (
      <Paper sx={{ p: 2, height: '100%' }}>
        <Alert severity="error">Failed to load status distribution</Alert>
      </Paper>
    );
  }

  const chartData = data?.data?.map((item: { status: string; count: number }) => ({
    name: item.status.replace('_', ' ').charAt(0).toUpperCase() + item.status.replace('_', ' ').slice(1),
    value: item.count,
    color: STATUS_COLORS[item.status] || '#9E9E9E',
  })) || [];

  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      <Typography variant="h6" gutterBottom>
        Project Status Distribution
      </Typography>
      {isLoading ? (
        <Skeleton variant="circular" width={200} height={200} sx={{ mx: 'auto' }} />
      ) : (
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={90}
              paddingAngle={2}
              dataKey="value"
              label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
            >
              {chartData.map((entry: { name: string; value: number; color: string }, index: number) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      )}
    </Paper>
  );
}

function RegionDistributionChart() {
  const { data, isLoading, error } = useDashboardRegionDistribution();

  if (error) {
    return (
      <Paper sx={{ p: 2, height: '100%' }}>
        <Alert severity="error">Failed to load region distribution</Alert>
      </Paper>
    );
  }

  const chartData = data?.data || [];

  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      <Typography variant="h6" gutterBottom>
        Projects by Region
      </Typography>
      {isLoading ? (
        <Skeleton variant="rectangular" height={250} />
      ) : (
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="region" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill="#1976D2">
              {chartData.map((_: unknown, index: number) => (
                <Cell key={`cell-${index}`} fill={REGION_COLORS[index % REGION_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </Paper>
  );
}

function VendorPerformanceChart() {
  const { data, isLoading, error } = useDashboardVendorPerformance(5);

  if (error) {
    return (
      <Paper sx={{ p: 2, height: '100%' }}>
        <Alert severity="error">Failed to load vendor performance</Alert>
      </Paper>
    );
  }

  const chartData = data?.data || [];

  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <BusinessIcon color="primary" />
        Top Vendor Performance
      </Typography>
      {isLoading ? (
        <Skeleton variant="rectangular" height={250} />
      ) : (
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={chartData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" domain={[0, 100]} />
            <YAxis dataKey="vendor_name" type="category" width={100} />
            <Tooltip formatter={(value: number) => [`${value}%`, 'On-Time %']} />
            <Legend />
            <Bar dataKey="on_time_percentage" fill="#4CAF50" name="On-Time %" />
          </BarChart>
        </ResponsiveContainer>
      )}
    </Paper>
  );
}

export default function Dashboard() {
  const { data: summaryData, isLoading: summaryLoading, error: summaryError } = useDashboardSummary();

  if (summaryError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to connect to API. Please ensure the backend is running.
        </Alert>
      </Box>
    );
  }

  const summary = summaryData?.data || {};
  const projects = summary.projects || {};
  const alerts = summary.alerts || {};

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        GPC Reliability Project Workflow Overview
      </Typography>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <SummaryCard
            title="Total Projects"
            value={projects.total || 0}
            subtitle="Active tracking"
            icon={<AssignmentIcon />}
            color="#1976D2"
            loading={summaryLoading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <SummaryCard
            title="In Progress"
            value={projects.active || 0}
            subtitle="Currently active"
            icon={<TrendingUpIcon />}
            color="#FF9800"
            loading={summaryLoading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <SummaryCard
            title="Completed"
            value={projects.completed || 0}
            subtitle="Successfully delivered"
            icon={<CheckCircleIcon />}
            color="#4CAF50"
            loading={summaryLoading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <SummaryCard
            title="Active Alerts"
            value={alerts.unacknowledged || 0}
            subtitle="Require attention"
            icon={<WarningIcon />}
            color="#F44336"
            loading={summaryLoading}
          />
        </Grid>
      </Grid>

      {/* Charts Row */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <StatusDistributionChart />
        </Grid>
        <Grid item xs={12} md={4}>
          <RegionDistributionChart />
        </Grid>
        <Grid item xs={12} md={4}>
          <VendorPerformanceChart />
        </Grid>
      </Grid>

      {/* Bottom Row - Next Actions and Recent Activity */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <NextActionsCard />
        </Grid>
        <Grid item xs={12} md={6}>
          <RecentActivityCard />
        </Grid>
      </Grid>
    </Box>
  );
}
