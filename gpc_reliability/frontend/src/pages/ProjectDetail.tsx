import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Box,
  Paper,
  Grid,
  Chip,
  Button,
  Divider,
  LinearProgress,
  Skeleton,
  Alert,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
  Tab,
  Tabs,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Schedule as ScheduleIcon,
  Business as BusinessIcon,
  AttachMoney as MoneyIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';
import { useState, useRef } from 'react';
import { useProject, useProjectHistory, useMilestones, useCompleteMilestone } from '../hooks/useQueries';

// Status and priority colors - matches backend model values
const STATUS_COLORS: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
  authorized: 'info',
  assigned_to_vendor: 'primary',
  design_submitted: 'warning',
  qa_qc: 'secondary',
  approved: 'success',
  construction_ready: 'success',
};

const PRIORITY_COLORS: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
  critical: 'error',
  high: 'warning',
  normal: 'info',
  low: 'default',
};

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

interface ProjectData {
  project_id: string;
  project_name: string;
  vendor_id: string;
  vendor_name: string;
  region: string;
  status: string;
  priority: string;
  start_date: string;
  target_completion_date: string;
  actual_completion_date?: string;
  budget: number;
  actual_spend: number;
  progress_percentage: number;
  description?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface Milestone {
  milestone_id: string;
  milestone_name: string;
  stage: string;
  target_date: string;
  actual_date?: string;
  completed: boolean;
  notes?: string;
}

interface HistoryEvent {
  id: string;
  event_type: string;
  old_value?: string;
  new_value?: string;
  changed_by?: string;
  changed_at: string;
  details?: string;
}

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);

  const { data: projectData, isLoading: projectLoading, error: projectError } = useProject(id!);
  const { data: milestonesData, isLoading: milestonesLoading } = useMilestones({ project_id: id });
  const { data: historyData, isLoading: historyLoading } = useProjectHistory(id!);
  const completeMilestone = useCompleteMilestone();
  const completingMilestoneId = useRef<string | null>(null);

  const project: ProjectData | undefined = projectData?.data;
  const milestones: Milestone[] = milestonesData?.data || [];
  const history: HistoryEvent[] = historyData?.data || [];

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const handleCompleteMilestone = async (milestoneId: string) => {
    completingMilestoneId.current = milestoneId;
    try {
      await completeMilestone.mutateAsync({ id: milestoneId });
    } catch (err) {
      console.error('Failed to complete milestone:', err);
    } finally {
      completingMilestoneId.current = null;
    }
  };

  if (projectError) {
    return (
      <Box>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/projects')} sx={{ mb: 2 }}>
          Back to Projects
        </Button>
        <Alert severity="error">Failed to load project details.</Alert>
      </Box>
    );
  }

  if (projectLoading) {
    return (
      <Box>
        <Skeleton variant="text" width={200} height={40} />
        <Skeleton variant="rectangular" height={200} sx={{ mt: 2 }} />
        <Skeleton variant="rectangular" height={300} sx={{ mt: 2 }} />
      </Box>
    );
  }

  if (!project) {
    return (
      <Box>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/projects')} sx={{ mb: 2 }}>
          Back to Projects
        </Button>
        <Alert severity="warning">Project not found.</Alert>
      </Box>
    );
  }

  const budgetUsagePercent = project.budget > 0 ? (project.actual_spend / project.budget) * 100 : 0;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/projects')}>
            Back
          </Button>
          <Box>
            <Typography variant="h4">{project.project_name}</Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
              <Chip
                size="small"
                label={(project.status || 'unknown').replace('_', ' ')}
                color={STATUS_COLORS[project.status] || 'default'}
              />
              <Chip
                size="small"
                label={project.priority}
                color={PRIORITY_COLORS[project.priority] || 'default'}
                variant="outlined"
              />
              <Chip size="small" label={project.region} variant="outlined" />
            </Box>
          </Box>
        </Box>
        <Button variant="contained" startIcon={<EditIcon />}>
          Edit Project
        </Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <BusinessIcon color="primary" />
                <Typography variant="body2" color="text.secondary">
                  Vendor
                </Typography>
              </Box>
              <Typography variant="h6">{project.vendor_name}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <ScheduleIcon color="primary" />
                <Typography variant="body2" color="text.secondary">
                  Timeline
                </Typography>
              </Box>
              <Typography variant="body2">
                {formatDate(project.start_date)} - {formatDate(project.target_completion_date)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <MoneyIcon color="primary" />
                <Typography variant="body2" color="text.secondary">
                  Budget
                </Typography>
              </Box>
              <Typography variant="h6">{formatCurrency(project.budget)}</Typography>
              <Typography variant="caption" color="text.secondary">
                Spent: {formatCurrency(project.actual_spend)} ({budgetUsagePercent.toFixed(0)}%)
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <TimelineIcon color="primary" />
                <Typography variant="body2" color="text.secondary">
                  Progress
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ flexGrow: 1 }}>
                  <LinearProgress
                    variant="determinate"
                    value={project.progress_percentage || 0}
                    sx={{ height: 10, borderRadius: 5 }}
                  />
                </Box>
                <Typography variant="h6">{project.progress_percentage || 0}%</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="Milestones" />
          <Tab label="History" />
          <Tab label="Details" />
        </Tabs>
        <Divider />

        {/* Milestones Tab */}
        <TabPanel value={tabValue} index={0}>
          {milestonesLoading ? (
            <Skeleton variant="rectangular" height={200} />
          ) : milestones.length === 0 ? (
            <Typography color="text.secondary" align="center">
              No milestones found for this project.
            </Typography>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Milestone</TableCell>
                    <TableCell>Stage</TableCell>
                    <TableCell>Target Date</TableCell>
                    <TableCell>Actual Date</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {milestones.map((milestone) => (
                    <TableRow key={milestone.milestone_id}>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {milestone.milestone_name}
                        </Typography>
                      </TableCell>
                      <TableCell>{milestone.stage}</TableCell>
                      <TableCell>{formatDate(milestone.target_date)}</TableCell>
                      <TableCell>{milestone.actual_date ? formatDate(milestone.actual_date) : '-'}</TableCell>
                      <TableCell>
                        {milestone.completed ? (
                          <Chip
                            size="small"
                            icon={<CheckCircleIcon />}
                            label="Completed"
                            color="success"
                          />
                        ) : new Date(milestone.target_date) < new Date() ? (
                          <Chip
                            size="small"
                            icon={<WarningIcon />}
                            label="Overdue"
                            color="error"
                          />
                        ) : (
                          <Chip size="small" label="Pending" variant="outlined" />
                        )}
                      </TableCell>
                      <TableCell align="center">
                        {!milestone.completed && (
                          <Tooltip title="Mark as Complete">
                            <IconButton
                              size="small"
                              color="success"
                              onClick={() => handleCompleteMilestone(milestone.milestone_id)}
                              disabled={completeMilestone.isPending && completingMilestoneId.current === milestone.milestone_id}
                            >
                              <CheckCircleIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </TabPanel>

        {/* History Tab */}
        <TabPanel value={tabValue} index={1}>
          {historyLoading ? (
            <Skeleton variant="rectangular" height={200} />
          ) : history.length === 0 ? (
            <Typography color="text.secondary" align="center">
              No history available for this project.
            </Typography>
          ) : (
            <Box sx={{ px: 2 }}>
              {history.map((event, index) => (
                <Box
                  key={event.id}
                  sx={{
                    display: 'flex',
                    gap: 2,
                    pb: 2,
                    mb: 2,
                    borderBottom: index < history.length - 1 ? 1 : 0,
                    borderColor: 'divider',
                  }}
                >
                  <Box
                    sx={{
                      width: 40,
                      height: 40,
                      borderRadius: '50%',
                      bgcolor: 'primary.light',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                    }}
                  >
                    <TimelineIcon sx={{ color: 'primary.main', fontSize: 20 }} />
                  </Box>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="body2" fontWeight="medium">
                      {(event.event_type || 'Unknown').replace('_', ' ')}
                    </Typography>
                    {event.details && (
                      <Typography variant="body2" color="text.secondary">
                        {event.details}
                      </Typography>
                    )}
                    {event.old_value && event.new_value && (
                      <Typography variant="caption" color="text.secondary">
                        Changed from "{event.old_value}" to "{event.new_value}"
                      </Typography>
                    )}
                    <Typography variant="caption" display="block" color="text.secondary">
                      {formatDate(event.changed_at)} {event.changed_by && `by ${event.changed_by}`}
                    </Typography>
                  </Box>
                </Box>
              ))}
            </Box>
          )}
        </TabPanel>

        {/* Details Tab */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3} sx={{ px: 2 }}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Description
              </Typography>
              <Typography variant="body1" sx={{ mt: 1 }}>
                {project.description || 'No description provided.'}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Notes
              </Typography>
              <Typography variant="body1" sx={{ mt: 1 }}>
                {project.notes || 'No notes available.'}
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Grid container spacing={2}>
                <Grid item xs={6} sm={3}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Project ID
                  </Typography>
                  <Typography variant="body2">{project.project_id}</Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Vendor ID
                  </Typography>
                  <Typography variant="body2">{project.vendor_id}</Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Created
                  </Typography>
                  <Typography variant="body2">{formatDate(project.created_at)}</Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Last Updated
                  </Typography>
                  <Typography variant="body2">{formatDate(project.updated_at)}</Typography>
                </Grid>
              </Grid>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>
    </Box>
  );
}
