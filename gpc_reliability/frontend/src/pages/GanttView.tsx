import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography,
  Box,
  Paper,
  Grid,
  TextField,
  MenuItem,
  Button,
  Chip,
  Skeleton,
  Alert,
  Tooltip,
  LinearProgress,
  IconButton,
} from '@mui/material';
import {
  FilterList as FilterIcon,
  Clear as ClearIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  Today as TodayIcon,
} from '@mui/icons-material';
import { useGanttData, useVendors } from '../hooks/useQueries';

// Status color mapping
const STATUS_COLORS: Record<string, string> = {
  authorized: '#2196F3',
  assigned_to_vendor: '#9C27B0',
  design_submitted: '#FF9800',
  qa_qc: '#00BCD4',
  approved: '#4CAF50',
  construction_ready: '#8BC34A',
};

const PRIORITY_COLORS: Record<string, string> = {
  critical: '#f44336',
  high: '#ff9800',
  normal: '#2196f3',
  low: '#9e9e9e',
};

// Regions match actual values in database
const REGIONS = ['Augusta Area', 'Central Georgia', 'Coastal', 'Coastal Georgia', 'East Georgia', 'Metro Atlanta', 'North Georgia', 'South Georgia', 'West Georgia'];
const STATUSES = ['authorized', 'assigned_to_vendor', 'design_submitted', 'qa_qc', 'approved', 'construction_ready'];
const PRIORITIES = ['critical', 'high', 'normal', 'low'];

interface GanttProject {
  id: string;
  work_order_number: string;
  description?: string;
  vendor_id?: string;
  vendor_name?: string;
  region?: string;
  status: string;
  status_label: string;
  priority: string;
  start_date: string;
  end_date: string;
  progress: number;
  total_milestones: number;
  completed_milestones: number;
  has_overdue: boolean;
  milestones: {
    stage: string;
    stage_label: string;
    expected_date?: string;
    actual_date?: string;
    is_complete: boolean;
    is_current: boolean;
    is_overdue: boolean;
  }[];
}

interface FilterState {
  vendor_id?: string;
  region?: string;
  status?: string;
  priority?: string;
}

export default function GanttView() {
  const navigate = useNavigate();
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<FilterState>({});
  const [timeOffset, setTimeOffset] = useState(0); // Weeks offset from current

  const queryParams = useMemo(() => ({
    ...Object.fromEntries(
      Object.entries(filters).filter(([_, value]) => value !== undefined && value !== '')
    ),
    limit: 50,
  }), [filters]);

  const { data, isLoading, error } = useGanttData(queryParams);
  const { data: vendorsData } = useVendors({ active_only: true });

  const projects: GanttProject[] = data?.data || [];
  const stages = data?.stages || [];
  const vendors = vendorsData?.data || [];

  // Calculate timeline range
  const today = new Date();
  const startOfWeek = new Date(today);
  startOfWeek.setDate(today.getDate() - today.getDay() + (timeOffset * 7));

  const timelineStart = new Date(startOfWeek);
  const timelineEnd = new Date(startOfWeek);
  timelineEnd.setDate(timelineEnd.getDate() + 27); // 4 weeks

  // Generate week headers
  const weekHeaders: { start: Date; label: string }[] = [];
  for (let i = 0; i < 4; i++) {
    const weekStart = new Date(timelineStart);
    weekStart.setDate(weekStart.getDate() + (i * 7));
    weekHeaders.push({
      start: new Date(weekStart),
      label: weekStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    });
  }

  const handleFilterChange = (key: keyof FilterState, value: string | undefined) => {
    setFilters((prev) => ({ ...prev, [key]: value || undefined }));
  };

  const clearFilters = () => {
    setFilters({});
  };

  const goToToday = () => {
    setTimeOffset(0);
  };

  // Calculate bar position and width for a project
  const calculateBarStyle = (project: GanttProject) => {
    const projectStart = new Date(project.start_date);
    const projectEnd = new Date(project.end_date);

    const totalDays = (timelineEnd.getTime() - timelineStart.getTime()) / (1000 * 60 * 60 * 24);

    // Calculate start position (clamped to timeline)
    const daysFromStart = Math.max(0, (projectStart.getTime() - timelineStart.getTime()) / (1000 * 60 * 60 * 24));
    const left = Math.min(100, (daysFromStart / totalDays) * 100);

    // Calculate end position
    const daysToEnd = (projectEnd.getTime() - timelineStart.getTime()) / (1000 * 60 * 60 * 24);
    const right = Math.min(100, Math.max(0, (daysToEnd / totalDays) * 100));

    // Calculate width
    const width = Math.max(2, right - left);

    return {
      left: `${left}%`,
      width: `${width}%`,
    };
  };

  // Check if date is within timeline
  const isDateInTimeline = (dateStr: string) => {
    const date = new Date(dateStr);
    return date >= timelineStart && date <= timelineEnd;
  };

  // Calculate position for a specific date
  const getDatePosition = (dateStr: string) => {
    const date = new Date(dateStr);
    const totalDays = (timelineEnd.getTime() - timelineStart.getTime()) / (1000 * 60 * 60 * 24);
    const daysFromStart = (date.getTime() - timelineStart.getTime()) / (1000 * 60 * 60 * 24);
    return (daysFromStart / totalDays) * 100;
  };

  if (error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Gantt View
        </Typography>
        <Alert severity="error">
          Failed to load Gantt data. Please ensure the backend is running.
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Gantt View
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Project timeline visualization
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<FilterIcon />}
            onClick={() => setShowFilters(!showFilters)}
          >
            {showFilters ? 'Hide Filters' : 'Show Filters'}
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      {showFilters && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={2.5}>
              <TextField
                fullWidth
                size="small"
                select
                label="Vendor"
                value={filters.vendor_id || ''}
                onChange={(e) => handleFilterChange('vendor_id', e.target.value)}
              >
                <MenuItem value="">All Vendors</MenuItem>
                {vendors.map((vendor: { vendor_id: string; vendor_name: string }) => (
                  <MenuItem key={vendor.vendor_id} value={vendor.vendor_id}>
                    {vendor.vendor_name}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6} md={2.5}>
              <TextField
                fullWidth
                size="small"
                select
                label="Region"
                value={filters.region || ''}
                onChange={(e) => handleFilterChange('region', e.target.value)}
              >
                <MenuItem value="">All Regions</MenuItem>
                {REGIONS.map((region) => (
                  <MenuItem key={region} value={region}>
                    {region}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6} md={2.5}>
              <TextField
                fullWidth
                size="small"
                select
                label="Status"
                value={filters.status || ''}
                onChange={(e) => handleFilterChange('status', e.target.value)}
              >
                <MenuItem value="">All Statuses</MenuItem>
                {STATUSES.map((status) => (
                  <MenuItem key={status} value={status}>
                    {status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6} md={2.5}>
              <TextField
                fullWidth
                size="small"
                select
                label="Priority"
                value={filters.priority || ''}
                onChange={(e) => handleFilterChange('priority', e.target.value)}
              >
                <MenuItem value="">All Priorities</MenuItem>
                {PRIORITIES.map((priority) => (
                  <MenuItem key={priority} value={priority}>
                    {priority.charAt(0).toUpperCase() + priority.slice(1)}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<ClearIcon />}
                onClick={clearFilters}
              >
                Clear
              </Button>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Timeline Navigation */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton onClick={() => setTimeOffset(timeOffset - 4)}>
              <ChevronLeftIcon />
            </IconButton>
            <Button startIcon={<TodayIcon />} onClick={goToToday}>
              Today
            </Button>
            <IconButton onClick={() => setTimeOffset(timeOffset + 4)}>
              <ChevronRightIcon />
            </IconButton>
          </Box>
          <Typography variant="body2" color="text.secondary">
            {timelineStart.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
            {' - '}
            {timelineEnd.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            {stages.slice(0, 4).map((stage: { id: string; label: string }) => (
              <Chip
                key={stage.id}
                size="small"
                label={stage.label}
                sx={{ bgcolor: STATUS_COLORS[stage.id] || '#ccc', color: 'white', fontSize: '0.7rem' }}
              />
            ))}
          </Box>
        </Box>
      </Paper>

      {/* Gantt Chart */}
      <Paper sx={{ overflow: 'hidden' }}>
        {/* Header Row */}
        <Box sx={{ display: 'flex', borderBottom: 1, borderColor: 'divider', bgcolor: 'grey.100' }}>
          <Box sx={{ width: 280, minWidth: 280, p: 1.5, borderRight: 1, borderColor: 'divider' }}>
            <Typography variant="subtitle2" fontWeight="bold">
              Project
            </Typography>
          </Box>
          <Box sx={{ flex: 1, display: 'flex' }}>
            {weekHeaders.map((week, index) => (
              <Box
                key={index}
                sx={{
                  flex: 1,
                  p: 1,
                  textAlign: 'center',
                  borderRight: index < weekHeaders.length - 1 ? 1 : 0,
                  borderColor: 'divider',
                }}
              >
                <Typography variant="caption" fontWeight="medium">
                  Week of {week.label}
                </Typography>
              </Box>
            ))}
          </Box>
        </Box>

        {/* Project Rows */}
        {isLoading ? (
          Array.from({ length: 10 }).map((_, index) => (
            <Box key={index} sx={{ display: 'flex', borderBottom: 1, borderColor: 'divider' }}>
              <Box sx={{ width: 280, minWidth: 280, p: 1.5, borderRight: 1, borderColor: 'divider' }}>
                <Skeleton variant="text" width="80%" />
                <Skeleton variant="text" width="60%" />
              </Box>
              <Box sx={{ flex: 1, p: 1.5 }}>
                <Skeleton variant="rectangular" height={24} />
              </Box>
            </Box>
          ))
        ) : projects.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography color="text.secondary">
              No projects found matching the current filters.
            </Typography>
          </Box>
        ) : (
          projects.map((project) => {
            const barStyle = calculateBarStyle(project);

            return (
              <Box
                key={project.id}
                sx={{
                  display: 'flex',
                  borderBottom: 1,
                  borderColor: 'divider',
                  '&:hover': { bgcolor: 'action.hover' },
                }}
              >
                {/* Project Info */}
                <Box
                  sx={{
                    width: 280,
                    minWidth: 280,
                    p: 1.5,
                    borderRight: 1,
                    borderColor: 'divider',
                    cursor: 'pointer',
                  }}
                  onClick={() => navigate(`/projects/${project.id}`)}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                    <Typography variant="body2" fontWeight="medium" noWrap sx={{ maxWidth: 150 }}>
                      {project.work_order_number}
                    </Typography>
                    <Chip
                      size="small"
                      label={project.priority}
                      sx={{
                        height: 18,
                        fontSize: '0.65rem',
                        bgcolor: PRIORITY_COLORS[project.priority] || '#ccc',
                        color: 'white',
                      }}
                    />
                    {project.has_overdue && (
                      <Chip
                        size="small"
                        label="!"
                        sx={{ height: 18, bgcolor: 'error.main', color: 'white' }}
                      />
                    )}
                  </Box>
                  <Typography variant="caption" color="text.secondary" noWrap display="block">
                    {project.vendor_name || 'No vendor'} • {project.region || 'No region'}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
                    <LinearProgress
                      variant="determinate"
                      value={project.progress}
                      sx={{ flex: 1, height: 4, borderRadius: 2 }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {project.progress}%
                    </Typography>
                  </Box>
                </Box>

                {/* Timeline Bar */}
                <Box
                  sx={{
                    flex: 1,
                    position: 'relative',
                    display: 'flex',
                    alignItems: 'center',
                    p: 1,
                  }}
                >
                  {/* Week grid lines */}
                  {weekHeaders.map((_, index) => (
                    <Box
                      key={index}
                      sx={{
                        position: 'absolute',
                        left: `${(index / 4) * 100}%`,
                        top: 0,
                        bottom: 0,
                        borderLeft: index > 0 ? 1 : 0,
                        borderColor: 'divider',
                      }}
                    />
                  ))}

                  {/* Today line */}
                  {today >= timelineStart && today <= timelineEnd && (
                    <Box
                      sx={{
                        position: 'absolute',
                        left: `${getDatePosition(today.toISOString())}%`,
                        top: 0,
                        bottom: 0,
                        width: 2,
                        bgcolor: 'error.main',
                        zIndex: 2,
                      }}
                    />
                  )}

                  {/* Project Bar */}
                  <Tooltip
                    title={
                      <Box>
                        <Typography variant="body2" fontWeight="bold">
                          {project.work_order_number}
                        </Typography>
                        <Typography variant="caption" display="block">
                          Status: {project.status_label}
                        </Typography>
                        <Typography variant="caption" display="block">
                          Progress: {project.completed_milestones}/{project.total_milestones} milestones
                        </Typography>
                        <Typography variant="caption" display="block">
                          {project.start_date} to {project.end_date}
                        </Typography>
                      </Box>
                    }
                    placement="top"
                    arrow
                  >
                    <Box
                      sx={{
                        position: 'absolute',
                        ...barStyle,
                        height: 24,
                        bgcolor: STATUS_COLORS[project.status] || '#2196F3',
                        borderRadius: 1,
                        display: 'flex',
                        alignItems: 'center',
                        overflow: 'hidden',
                        cursor: 'pointer',
                        '&:hover': { opacity: 0.9 },
                        zIndex: 1,
                      }}
                      onClick={() => navigate(`/projects/${project.id}`)}
                    >
                      {/* Progress fill */}
                      <Box
                        sx={{
                          position: 'absolute',
                          left: 0,
                          top: 0,
                          bottom: 0,
                          width: `${project.progress}%`,
                          bgcolor: 'rgba(255,255,255,0.3)',
                        }}
                      />

                      {/* Milestone markers */}
                      {project.milestones.map((milestone, mIndex) => {
                        const dateToUse = milestone.actual_date || milestone.expected_date;
                        if (!dateToUse || !isDateInTimeline(dateToUse)) return null;

                        const position = getDatePosition(dateToUse);
                        const barLeft = parseFloat(barStyle.left);
                        const barWidth = parseFloat(barStyle.width);
                        const relativePosition = ((position - barLeft) / barWidth) * 100;

                        if (relativePosition < 0 || relativePosition > 100) return null;

                        return (
                          <Tooltip
                            key={mIndex}
                            title={`${milestone.stage_label}: ${dateToUse}`}
                            placement="top"
                          >
                            <Box
                              sx={{
                                position: 'absolute',
                                left: `${relativePosition}%`,
                                width: 6,
                                height: 6,
                                borderRadius: '50%',
                                bgcolor: milestone.is_complete ? 'white' : (milestone.is_overdue ? 'error.main' : 'rgba(255,255,255,0.5)'),
                                border: milestone.is_current ? 2 : 0,
                                borderColor: 'white',
                                transform: 'translateX(-50%)',
                              }}
                            />
                          </Tooltip>
                        );
                      })}
                    </Box>
                  </Tooltip>
                </Box>
              </Box>
            );
          })
        )}
      </Paper>

      {/* Legend */}
      <Paper sx={{ p: 2, mt: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          Legend
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ width: 20, height: 2, bgcolor: 'error.main' }} />
            <Typography variant="caption">Today</Typography>
          </Box>
          {Object.entries(STATUS_COLORS).map(([status, color]) => (
            <Box key={status} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box sx={{ width: 16, height: 16, bgcolor: color, borderRadius: 0.5 }} />
              <Typography variant="caption">
                {status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </Typography>
            </Box>
          ))}
        </Box>
      </Paper>
    </Box>
  );
}
