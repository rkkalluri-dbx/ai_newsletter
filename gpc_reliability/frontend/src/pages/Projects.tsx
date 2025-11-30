import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
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
  TextField,
  MenuItem,
  Button,
  Grid,
  Skeleton,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  Visibility as ViewIcon,
  Edit as EditIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  Download as DownloadIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { useProjects, useVendors } from '../hooks/useQueries';
import { projectsApi, ProjectListParams } from '../services/api';
import ProjectFormModal from '../components/projects/ProjectFormModal';

// Status color mapping - matches backend ProjectStatus values
const STATUS_COLORS: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
  authorized: 'info',
  assigned_to_vendor: 'primary',
  design_submitted: 'warning',
  qa_qc: 'secondary',
  approved: 'success',
  construction_ready: 'success',
};

// Priority color mapping - matches backend Priority values
const PRIORITY_COLORS: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
  critical: 'error',
  high: 'warning',
  normal: 'info',
  low: 'default',
};

// Regions match actual values in database
const REGIONS = ['Augusta Area', 'Central Georgia', 'Coastal', 'Coastal Georgia', 'East Georgia', 'Metro Atlanta', 'North Georgia', 'South Georgia', 'West Georgia'];
// Statuses match backend ProjectStatus.ALL
const STATUSES = ['authorized', 'assigned_to_vendor', 'design_submitted', 'qa_qc', 'approved', 'construction_ready'];
// Priorities match backend Priority.ALL
const PRIORITIES = ['low', 'normal', 'high', 'critical'];

interface Project {
  project_id: string;
  project_name: string;
  vendor_name: string;
  region: string;
  status: string;
  priority: string;
  start_date: string;
  target_completion_date: string;
  budget: number;
  actual_spend: number;
  progress_percentage: number;
}

export default function Projects() {
  const navigate = useNavigate();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [showFilters, setShowFilters] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);

  // Filter state
  const [filters, setFilters] = useState<ProjectListParams>({
    status: undefined,
    vendor_id: undefined,
    region: undefined,
    priority: undefined,
    search: undefined,
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
  const { data, isLoading, error, refetch } = useProjects(queryParams);
  const { data: vendorsData } = useVendors({ active_only: true });

  const projects = data?.data || [];
  const totalCount = data?.total || 0;
  const vendors = vendorsData?.data || [];

  const handleOpenCreate = () => {
    setEditingProject(null);
    setModalOpen(true);
  };

  const handleOpenEdit = (project: Project) => {
    setEditingProject(project);
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setEditingProject(null);
  };

  const handleModalSuccess = () => {
    refetch();
  };

  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleFilterChange = (key: keyof ProjectListParams, value: string | undefined) => {
    setFilters((prev) => ({ ...prev, [key]: value || undefined }));
    setPage(0);
  };

  const clearFilters = () => {
    setFilters({
      status: undefined,
      vendor_id: undefined,
      region: undefined,
      priority: undefined,
      search: undefined,
    });
    setPage(0);
  };

  const handleExport = async () => {
    try {
      const response = await projectsApi.export(queryParams);
      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `projects_export_${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

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

  if (error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Projects
        </Typography>
        <Alert severity="error">
          Failed to load projects. Please ensure the backend is running.
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
            Projects
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage and track all reliability projects
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
          <Button variant="outlined" startIcon={<DownloadIcon />} onClick={handleExport}>
            Export
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={handleOpenCreate}>
            New Project
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      {showFilters && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={2}>
              <TextField
                fullWidth
                size="small"
                label="Search"
                value={filters.search || ''}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                placeholder="Project name..."
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
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
                    {status.replace('_', ' ').charAt(0).toUpperCase() + status.replace('_', ' ').slice(1)}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
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
            <Grid item xs={12} sm={6} md={2}>
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
            <Grid item xs={12} sm={6} md={2}>
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

      {/* Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Project Name</TableCell>
                <TableCell>Vendor</TableCell>
                <TableCell>Region</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Priority</TableCell>
                <TableCell>Start Date</TableCell>
                <TableCell>Target Date</TableCell>
                <TableCell align="right">Budget</TableCell>
                <TableCell align="center">Progress</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                Array.from({ length: rowsPerPage }).map((_, index) => (
                  <TableRow key={index}>
                    {Array.from({ length: 10 }).map((_, cellIndex) => (
                      <TableCell key={cellIndex}>
                        <Skeleton />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : projects.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={10} align="center">
                    <Typography color="text.secondary" sx={{ py: 3 }}>
                      No projects found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                projects.map((project: Project) => (
                  <TableRow
                    key={project.project_id}
                    hover
                    sx={{ cursor: 'pointer' }}
                    onClick={() => navigate(`/projects/${project.project_id}`)}
                  >
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {project.project_name}
                      </Typography>
                    </TableCell>
                    <TableCell>{project.vendor_name}</TableCell>
                    <TableCell>{project.region}</TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={project.status.replace('_', ' ')}
                        color={STATUS_COLORS[project.status] || 'default'}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={project.priority}
                        color={PRIORITY_COLORS[project.priority] || 'default'}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>{formatDate(project.start_date)}</TableCell>
                    <TableCell>{formatDate(project.target_completion_date)}</TableCell>
                    <TableCell align="right">{formatCurrency(project.budget)}</TableCell>
                    <TableCell align="center">
                      <Box
                        sx={{
                          width: 60,
                          height: 8,
                          bgcolor: '#E0E0E0',
                          borderRadius: 1,
                          overflow: 'hidden',
                          display: 'inline-block',
                        }}
                      >
                        <Box
                          sx={{
                            width: `${project.progress_percentage || 0}%`,
                            height: '100%',
                            bgcolor: project.progress_percentage >= 75 ? 'success.main' : project.progress_percentage >= 50 ? 'warning.main' : 'info.main',
                          }}
                        />
                      </Box>
                      <Typography variant="caption" sx={{ ml: 1 }}>
                        {project.progress_percentage || 0}%
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Tooltip title="View Details">
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/projects/${project.project_id}`);
                          }}
                        >
                          <ViewIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit">
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleOpenEdit(project);
                          }}
                        >
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
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

      {/* Project Form Modal */}
      <ProjectFormModal
        open={modalOpen}
        onClose={handleCloseModal}
        project={editingProject ? { ...editingProject, project_id: editingProject.project_id } : undefined}
        onSuccess={handleModalSuccess}
      />
    </Box>
  );
}
