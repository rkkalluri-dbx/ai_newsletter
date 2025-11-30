import { useState, useMemo } from 'react';
import {
  Typography,
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  Button,
  TextField,
  MenuItem,
  Grid,
  Skeleton,
  Alert,
  Tooltip,
  Checkbox,
  Card,
  CardContent,
} from '@mui/material';
import {
  CheckCircle as AcknowledgeIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { useAlerts, useAlertStats, useAcknowledgeAlert, useBulkAcknowledgeAlerts } from '../hooks/useQueries';
import { AlertListParams } from '../services/api';
import AlertFormModal from '../components/alerts/AlertFormModal';

// Severity color mapping - matches backend AlertSeverity values
const SEVERITY_COLORS: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
  critical: 'error',
  warning: 'warning',
  info: 'info',
};

const SEVERITY_ICONS: Record<string, React.ReactElement> = {
  critical: <ErrorIcon fontSize="small" />,
  warning: <WarningIcon fontSize="small" />,
  info: <InfoIcon fontSize="small" />,
};

// Severities match backend AlertSeverity.ALL
const SEVERITIES = ['info', 'warning', 'critical'];
// Alert types match backend AlertType.ALL
const ALERT_TYPES = ['milestone_overdue', 'milestone_approaching', 'status_change', 'revision_added'];

interface AlertItem {
  alert_id: string;
  alert_type: string;
  severity: string;
  title: string;
  message: string;
  project_id?: string;
  project_name?: string;
  vendor_id?: string;
  vendor_name?: string;
  acknowledged: boolean;
  acknowledged_by?: string;
  acknowledged_at?: string;
  created_at: string;
}

interface SeverityCount {
  severity: string;
  total: number;
  unacknowledged: number;
}

interface AlertStatsResponse {
  overall?: {
    total: number;
    unacknowledged: number;
    acknowledged: number;
  };
  by_severity?: SeverityCount[];
  by_type?: Array<{ alert_type: string; total: number; unacknowledged: number }>;
}

interface AlertStats {
  total: number;
  unacknowledged: number;
  critical: number;
  warning: number;
  high: number;
}

export default function Alerts() {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedAlerts, setSelectedAlerts] = useState<string[]>([]);
  const [modalOpen, setModalOpen] = useState(false);

  // Filter state
  const [filters, setFilters] = useState<AlertListParams>({
    severity: undefined,
    alert_type: undefined,
    acknowledged: undefined,
  });

  // Build query params
  const queryParams = useMemo(() => ({
    page: page + 1,
    per_page: rowsPerPage,
    ...Object.fromEntries(
      Object.entries(filters).filter(([_, value]) => value !== undefined && value !== '')
    ),
  }), [page, rowsPerPage, filters]);

  // Fetch data
  const { data, isLoading, error, refetch } = useAlerts(queryParams);
  const { data: statsData, refetch: refetchStats } = useAlertStats();
  const acknowledgeAlert = useAcknowledgeAlert();
  const bulkAcknowledge = useBulkAcknowledgeAlerts();

  const handleOpenCreate = () => {
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
  };

  const handleModalSuccess = () => {
    refetch();
    refetchStats();
  };

  const alerts: AlertItem[] = data?.data || [];
  const totalCount = data?.total || 0;

  // Parse stats from API response format
  const rawStats: AlertStatsResponse = statsData?.data || {};
  const stats: AlertStats = {
    total: rawStats.overall?.total || 0,
    unacknowledged: rawStats.overall?.unacknowledged || 0,
    critical: rawStats.by_severity?.find(s => s.severity === 'critical')?.unacknowledged || 0,
    warning: rawStats.by_severity?.find(s => s.severity === 'warning')?.unacknowledged || 0,
    high: rawStats.by_severity?.find(s => s.severity === 'high')?.unacknowledged || 0,
  };

  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleFilterChange = (key: keyof AlertListParams, value: string | boolean | undefined) => {
    setFilters((prev) => ({ ...prev, [key]: value === '' ? undefined : value }));
    setPage(0);
  };

  const clearFilters = () => {
    setFilters({
      severity: undefined,
      alert_type: undefined,
      acknowledged: undefined,
    });
    setPage(0);
  };

  const handleAcknowledge = async (alertId: string) => {
    try {
      await acknowledgeAlert.mutateAsync({ id: alertId });
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const handleBulkAcknowledge = async () => {
    if (selectedAlerts.length === 0) return;
    try {
      await bulkAcknowledge.mutateAsync({ alert_ids: selectedAlerts });
      setSelectedAlerts([]);
    } catch (err) {
      console.error('Failed to bulk acknowledge alerts:', err);
    }
  };

  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      const unacknowledgedIds = alerts
        .filter((alert) => !alert.acknowledged)
        .map((alert) => alert.alert_id);
      setSelectedAlerts(unacknowledgedIds);
    } else {
      setSelectedAlerts([]);
    }
  };

  const handleSelectAlert = (alertId: string) => {
    setSelectedAlerts((prev) =>
      prev.includes(alertId)
        ? prev.filter((id) => id !== alertId)
        : [...prev, alertId]
    );
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatAlertType = (type: string) => {
    return type
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  if (error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Alerts
        </Typography>
        <Alert severity="error">
          Failed to load alerts. Please ensure the backend is running.
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
            Alerts
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Monitor and manage system alerts
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
          {selectedAlerts.length > 0 && (
            <Button
              variant="contained"
              color="success"
              startIcon={<AcknowledgeIcon />}
              onClick={handleBulkAcknowledge}
              disabled={bulkAcknowledge.isPending}
            >
              Acknowledge ({selectedAlerts.length})
            </Button>
          )}
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleOpenCreate}
          >
            Create Alert
          </Button>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="text.primary">
                {stats.total}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Alerts
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="error.main">
                {stats.unacknowledged}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Unacknowledged
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="error.main">
                {stats.critical}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Critical
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="warning.main">
                {stats.warning}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Warning
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      {showFilters && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                size="small"
                select
                label="Severity"
                value={filters.severity || ''}
                onChange={(e) => handleFilterChange('severity', e.target.value)}
              >
                <MenuItem value="">All Severities</MenuItem>
                {SEVERITIES.map((severity) => (
                  <MenuItem key={severity} value={severity}>
                    {severity.charAt(0).toUpperCase() + severity.slice(1)}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                size="small"
                select
                label="Alert Type"
                value={filters.alert_type || ''}
                onChange={(e) => handleFilterChange('alert_type', e.target.value)}
              >
                <MenuItem value="">All Types</MenuItem>
                {ALERT_TYPES.map((type) => (
                  <MenuItem key={type} value={type}>
                    {formatAlertType(type)}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                size="small"
                select
                label="Status"
                value={filters.acknowledged === undefined ? '' : filters.acknowledged ? 'true' : 'false'}
                onChange={(e) => {
                  const value = e.target.value;
                  handleFilterChange('acknowledged', value === '' ? undefined : value === 'true');
                }}
              >
                <MenuItem value="">All Statuses</MenuItem>
                <MenuItem value="false">Pending</MenuItem>
                <MenuItem value="true">Acknowledged</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<ClearIcon />}
                onClick={clearFilters}
              >
                Clear Filters
              </Button>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox">
                  <Checkbox
                    indeterminate={
                      selectedAlerts.length > 0 &&
                      selectedAlerts.length < alerts.filter((a) => !a.acknowledged).length
                    }
                    checked={
                      alerts.filter((a) => !a.acknowledged).length > 0 &&
                      selectedAlerts.length === alerts.filter((a) => !a.acknowledged).length
                    }
                    onChange={handleSelectAll}
                  />
                </TableCell>
                <TableCell>Severity</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Title</TableCell>
                <TableCell>Related To</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                Array.from({ length: rowsPerPage }).map((_, index) => (
                  <TableRow key={index}>
                    {Array.from({ length: 8 }).map((_, cellIndex) => (
                      <TableCell key={cellIndex}>
                        <Skeleton />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : alerts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    <Box sx={{ py: 3 }}>
                      <AcknowledgeIcon sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
                      <Typography color="text.secondary">
                        No alerts found
                      </Typography>
                    </Box>
                  </TableCell>
                </TableRow>
              ) : (
                alerts.map((alert) => (
                  <TableRow
                    key={alert.alert_id}
                    sx={{
                      bgcolor: alert.acknowledged ? 'transparent' : 'action.hover',
                    }}
                  >
                    <TableCell padding="checkbox">
                      <Checkbox
                        checked={selectedAlerts.includes(alert.alert_id)}
                        onChange={() => handleSelectAlert(alert.alert_id)}
                        disabled={alert.acknowledged}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        icon={SEVERITY_ICONS[alert.severity]}
                        label={alert.severity}
                        color={SEVERITY_COLORS[alert.severity] || 'default'}
                      />
                    </TableCell>
                    <TableCell>{formatAlertType(alert.alert_type)}</TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {alert.title}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {alert.message}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {alert.project_name && (
                        <Typography variant="body2">{alert.project_name}</Typography>
                      )}
                      {alert.vendor_name && (
                        <Typography variant="caption" color="text.secondary">
                          {alert.vendor_name}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>{formatDate(alert.created_at)}</TableCell>
                    <TableCell>
                      {alert.acknowledged ? (
                        <Tooltip title={`Acknowledged by ${alert.acknowledged_by || 'user'} on ${formatDate(alert.acknowledged_at || '')}`}>
                          <Chip size="small" label="Acknowledged" color="success" />
                        </Tooltip>
                      ) : (
                        <Chip size="small" label="Pending" variant="outlined" />
                      )}
                    </TableCell>
                    <TableCell align="center">
                      {!alert.acknowledged && (
                        <Tooltip title="Acknowledge Alert">
                          <IconButton
                            size="small"
                            color="success"
                            onClick={() => handleAcknowledge(alert.alert_id)}
                            disabled={acknowledgeAlert.isPending}
                          >
                            <AcknowledgeIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={totalCount}
          page={page}
          onPageChange={handleChangePage}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          rowsPerPageOptions={[10, 25, 50, 100]}
        />
      </Paper>

      {/* Alert Form Modal */}
      <AlertFormModal
        open={modalOpen}
        onClose={handleCloseModal}
        onSuccess={handleModalSuccess}
      />
    </Box>
  );
}
