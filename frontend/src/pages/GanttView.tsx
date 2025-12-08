import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
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
  ToggleButtonGroup,
  ToggleButton,
} from '@mui/material';
import {
  FilterList as FilterIcon,
  Clear as ClearIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  Today as TodayIcon,
  ViewWeek as ViewWeekIcon,
  CalendarMonth as CalendarMonthIcon,
  DateRange as DateRangeIcon,
  Timeline as TimelineIcon,
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
  status_periods?: {  // NEW: Full lifecycle timeline
    status: string;
    status_label: string;
    start_date: string;
    end_date: string | null;
    is_completed: boolean;
    is_current: boolean;
    duration_days: number;
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
  const [viewMode, setViewMode] = useState<'week' | 'month' | 'quarter' | 'full'>('month');

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

  // Calculate timeline range based on view mode
  const today = new Date();

  const { timelineStart, timelineEnd, periodHeaders } = useMemo(() => {
    const startOfWeek = new Date(today);
    startOfWeek.setDate(today.getDate() - today.getDay());

    const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    const startOfQuarter = new Date(today.getFullYear(), Math.floor(today.getMonth() / 3) * 3, 1);

    let start: Date, end: Date, periods: { start: Date; label: string }[] = [];

    if (viewMode === 'week') {
      start = new Date(startOfWeek);
      start.setDate(start.getDate() + (timeOffset * 7));
      end = new Date(start);
      end.setDate(end.getDate() + 27); // 4 weeks

      for (let i = 0; i < 4; i++) {
        const weekStart = new Date(start);
        weekStart.setDate(weekStart.getDate() + (i * 7));
        periods.push({
          start: new Date(weekStart),
          label: weekStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        });
      }
    } else if (viewMode === 'month') {
      start = new Date(startOfMonth);
      start.setMonth(start.getMonth() + (timeOffset * 3));
      end = new Date(start);
      end.setMonth(end.getMonth() + 3); // 3 months

      for (let i = 0; i < 3; i++) {
        const monthStart = new Date(start);
        monthStart.setMonth(monthStart.getMonth() + i);
        periods.push({
          start: new Date(monthStart),
          label: monthStart.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
        });
      }
    } else if (viewMode === 'quarter') {
      start = new Date(startOfQuarter);
      start.setMonth(start.getMonth() + (timeOffset * 12));
      end = new Date(start);
      end.setFullYear(end.getFullYear() + 1); // 4 quarters = 1 year

      for (let i = 0; i < 4; i++) {
        const qtrStart = new Date(start);
        qtrStart.setMonth(qtrStart.getMonth() + (i * 3));
        const qtr = Math.floor(qtrStart.getMonth() / 3) + 1;
        periods.push({
          start: new Date(qtrStart),
          label: `Q${qtr} ${qtrStart.getFullYear()}`,
        });
      }
    } else { // 'full'
      // Show full project lifecycle - find min/max dates from projects
      const allDates = projects.flatMap(p =>
        p.status_periods?.map(sp => sp.start_date) || [p.start_date]
      );
      start = allDates.length > 0 ? new Date(Math.min(...allDates.map(d => new Date(d).getTime()))) : new Date();
      end = new Date();
      end.setDate(end.getDate() + 30); // Show 30 days into future

      // Generate monthly periods for full view
      const months = Math.ceil((end.getTime() - start.getTime()) / (30 * 24 * 60 * 60 * 1000));
      for (let i = 0; i < Math.min(months, 12); i++) {
        const monthStart = new Date(start);
        monthStart.setMonth(monthStart.getMonth() + i);
        periods.push({
          start: new Date(monthStart),
          label: monthStart.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
        });
      }
    }

    return {
      timelineStart: start,
      timelineEnd: end,
      periodHeaders: periods,
    };
  }, [viewMode, timeOffset, projects, today]);

  // Backwards compatibility
  const weekHeaders = periodHeaders;

  const handleFilterChange = (key: keyof FilterState, value: string | undefined) => {
    setFilters((prev) => ({ ...prev, [key]: value || undefined }));
  };

  const clearFilters = () => {
    setFilters({});
  };

  const goToToday = () => {
    setTimeOffset(0);
  };

  const handleViewModeChange = (_: React.MouseEvent<HTMLElement>, newMode: 'week' | 'month' | 'quarter' | 'full' | null) => {
    if (newMode !== null) {
      setViewMode(newMode);
      setTimeOffset(0); // Reset to current period when switching modes
    }
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

  // Calculate position and width for a status period segment
  const calculateSegmentStyle = (
    period: { start_date: string; end_date: string | null; is_current?: boolean },
    rangeStart: Date,
    rangeEnd: Date
  ) => {
    const totalDays = dayjs(rangeEnd).diff(dayjs(rangeStart), 'day');
    const segmentStart = dayjs(period.start_date);
    const segmentEnd = period.end_date ? dayjs(period.end_date) : dayjs(rangeEnd);

    const daysFromStart = segmentStart.diff(dayjs(rangeStart), 'day');
    const segmentDuration = segmentEnd.diff(segmentStart, 'day');

    const left = Math.max(0, (daysFromStart / totalDays) * 100);
    const width = Math.min(100 - left, (segmentDuration / totalDays) * 100);

    return { left, width };
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
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {/* View Mode Toggle */}
          <Box sx={{ display: 'flex', justifyContent: 'center' }}>
            <ToggleButtonGroup
              value={viewMode}
              exclusive
              onChange={handleViewModeChange}
              size="small"
              aria-label="timeline view mode"
            >
              <ToggleButton value="week" aria-label="weekly view">
                <Tooltip title="Weekly View (4 weeks)">
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <ViewWeekIcon fontSize="small" />
                    <Typography variant="caption">Week</Typography>
                  </Box>
                </Tooltip>
              </ToggleButton>
              <ToggleButton value="month" aria-label="monthly view">
                <Tooltip title="Monthly View (3 months)">
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <CalendarMonthIcon fontSize="small" />
                    <Typography variant="caption">Month</Typography>
                  </Box>
                </Tooltip>
              </ToggleButton>
              <ToggleButton value="quarter" aria-label="quarterly view">
                <Tooltip title="Quarterly View (1 year)">
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <DateRangeIcon fontSize="small" />
                    <Typography variant="caption">Quarter</Typography>
                  </Box>
                </Tooltip>
              </ToggleButton>
              <ToggleButton value="full" aria-label="full timeline view">
                <Tooltip title="Full Timeline (All projects)">
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <TimelineIcon fontSize="small" />
                    <Typography variant="caption">Full</Typography>
                  </Box>
                </Tooltip>
              </ToggleButton>
            </ToggleButtonGroup>
          </Box>

          {/* Navigation and Date Range */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {viewMode !== 'full' && (
                <>
                  <IconButton onClick={() => setTimeOffset(timeOffset - 1)}>
                    <ChevronLeftIcon />
                  </IconButton>
                  <Button startIcon={<TodayIcon />} onClick={goToToday}>
                    Today
                  </Button>
                  <IconButton onClick={() => setTimeOffset(timeOffset + 1)}>
                    <ChevronRightIcon />
                  </IconButton>
                </>
              )}
            </Box>
            <Typography variant="body2" color="text.secondary">
              {timelineStart.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
              {' - '}
              {timelineEnd.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {stages.map((stage: { id: string; label: string }) => (
                <Chip
                  key={stage.id}
                  size="small"
                  label={stage.label}
                  sx={{ bgcolor: STATUS_COLORS[stage.id] || '#ccc', color: 'white', fontSize: '0.7rem' }}
                />
              ))}
            </Box>
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

                  {/* Project Bar - Multi-segment Timeline */}
                  <Box sx={{ position: 'relative', height: '32px', width: '100%' }}>
                    {project.status_periods && project.status_periods.length > 0 ? (
                      // Multi-segment timeline showing full project lifecycle
                      project.status_periods.map((period, idx) => {
                        const { left, width } = calculateSegmentStyle(period, timelineStart, timelineEnd);

                        // Skip segments that are completely outside the visible range
                        if (width <= 0) return null;

                        return (
                          <Tooltip
                            key={idx}
                            title={`${period.status_label}: ${period.start_date} - ${period.end_date || 'Present'} (${period.duration_days} days)`}
                            placement="top"
                            arrow
                          >
                            <Box
                              sx={{
                                position: 'absolute',
                                left: `${left}%`,
                                width: `${width}%`,
                                height: '24px',
                                top: '4px',
                                backgroundColor: STATUS_COLORS[period.status] || '#2196F3',
                                border: period.is_current ? '3px solid #000' : 'none',
                                boxSizing: 'border-box',
                                borderRight: idx < (project.status_periods?.length || 0) - 1 ? '1px solid rgba(255,255,255,0.8)' : 'none',
                                borderRadius: idx === 0 ? '4px 0 0 4px' : (idx === (project.status_periods?.length || 0) - 1 ? '0 4px 4px 0' : '0'),
                                transition: 'all 0.2s ease',
                                cursor: 'pointer',
                                '&:hover': {
                                  opacity: 0.85,
                                  transform: 'scaleY(1.1)',
                                  zIndex: 10,
                                },
                                zIndex: period.is_current ? 2 : 1,
                              }}
                              onClick={() => navigate(`/projects/${project.id}`)}
                            />
                          </Tooltip>
                        );
                      })
                    ) : (
                      // Fallback: Single bar for projects without status_periods
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
                            top: '4px',
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
                    )}
                  </Box>
                </Box>
              </Box>
            );
          })
        )}
      </Paper>

      {/* Legend */}
      <Paper sx={{ p: 2, mt: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle2">
            Legend
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Timeline shows project lifecycle with color-coded status transitions
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ width: 20, height: 2, bgcolor: 'error.main' }} />
            <Typography variant="caption">Today</Typography>
          </Box>
          <Box sx={{ width: 1, height: 20, bgcolor: 'divider' }} />
          {Object.entries(STATUS_COLORS).map(([status, color]) => (
            <Box key={status} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box sx={{ width: 20, height: 16, bgcolor: color, borderRadius: 0.5 }} />
              <Typography variant="caption">
                {status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </Typography>
            </Box>
          ))}
          <Box sx={{ width: 1, height: 20, bgcolor: 'divider' }} />
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ width: 20, height: 16, bgcolor: '#4CAF50', border: '3px solid #000', boxSizing: 'border-box', borderRadius: 0.5 }} />
            <Typography variant="caption">Current Status</Typography>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
}
