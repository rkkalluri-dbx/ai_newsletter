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
  Tab,
  Tabs,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  Business as BusinessIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  Person as PersonIcon,
  Assignment as ProjectIcon,
  TrendingUp as TrendingUpIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { useState } from 'react';
import { useVendor, useVendorMetrics, useVendorProjects } from '../hooks/useQueries';
import VendorFormModal from '../components/vendors/VendorFormModal';

// Status color mapping - matches backend ProjectStatus values
const STATUS_COLORS: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
  authorized: 'info',
  assigned_to_vendor: 'primary',
  design_submitted: 'warning',
  qa_qc: 'secondary',
  approved: 'success',
  construction_ready: 'success',
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

interface VendorData {
  vendor_id: string;
  vendor_name: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  project_stats?: {
    total: number;
    completed: number;
    active: number;
  };
}

interface VendorMetrics {
  vendor_id: string;
  vendor_name: string;
  total_projects: number;
  completed_projects: number;
  active_projects: number;
  overdue_projects?: number;
  on_time_rate?: number;
  avg_cycle_time_days?: number;
  revision_rate?: number;
  sla_compliance_rate?: number;
}

interface VendorProject {
  id: string;
  work_order_number: string;
  description?: string;
  region?: string;
  status: string;
  priority: string;
  authorized_date?: string;
  created_at?: string;
}

export default function VendorDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);
  const [modalOpen, setModalOpen] = useState(false);

  const { data: vendorData, isLoading: vendorLoading, error: vendorError, refetch } = useVendor(id!);
  const { data: metricsData, isLoading: metricsLoading } = useVendorMetrics(id!);
  const { data: projectsData, isLoading: projectsLoading } = useVendorProjects(id!);

  const vendor: VendorData | undefined = vendorData?.data;
  const metrics: VendorMetrics | undefined = metricsData?.data;
  const projects: VendorProject[] = projectsData?.data || [];

  const formatDate = (dateString: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const handleOpenEdit = () => {
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
  };

  const handleModalSuccess = () => {
    refetch();
  };

  if (vendorError) {
    return (
      <Box>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/vendors')} sx={{ mb: 2 }}>
          Back to Vendors
        </Button>
        <Alert severity="error">Failed to load vendor details.</Alert>
      </Box>
    );
  }

  if (vendorLoading) {
    return (
      <Box>
        <Skeleton variant="text" width={200} height={40} />
        <Skeleton variant="rectangular" height={200} sx={{ mt: 2 }} />
        <Skeleton variant="rectangular" height={300} sx={{ mt: 2 }} />
      </Box>
    );
  }

  if (!vendor) {
    return (
      <Box>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/vendors')} sx={{ mb: 2 }}>
          Back to Vendors
        </Button>
        <Alert severity="warning">Vendor not found.</Alert>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/vendors')}>
            Back
          </Button>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <BusinessIcon color="primary" sx={{ fontSize: 32 }} />
              <Typography variant="h4">{vendor.vendor_name}</Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
              <Chip
                size="small"
                label={vendor.is_active ? 'Active' : 'Inactive'}
                color={vendor.is_active ? 'success' : 'default'}
              />
            </Box>
          </Box>
        </Box>
        <Button variant="contained" startIcon={<EditIcon />} onClick={handleOpenEdit}>
          Edit Vendor
        </Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <PersonIcon color="primary" />
                <Typography variant="body2" color="text.secondary">
                  Contact
                </Typography>
              </Box>
              <Typography variant="h6">{vendor.contact_name || 'Not specified'}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <ProjectIcon color="primary" />
                <Typography variant="body2" color="text.secondary">
                  Projects
                </Typography>
              </Box>
              <Typography variant="h6">
                {metrics?.active_projects || vendor.project_stats?.active || 0}
                <Typography variant="caption" color="text.secondary">
                  {' '}active / {metrics?.total_projects || vendor.project_stats?.total || 0} total
                </Typography>
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <TrendingUpIcon color="primary" />
                <Typography variant="body2" color="text.secondary">
                  On-Time Rate
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ flexGrow: 1 }}>
                  <LinearProgress
                    variant="determinate"
                    value={metrics?.on_time_rate || 0}
                    color={
                      (metrics?.on_time_rate || 0) >= 80
                        ? 'success'
                        : (metrics?.on_time_rate || 0) >= 60
                        ? 'warning'
                        : 'error'
                    }
                    sx={{ height: 10, borderRadius: 5 }}
                  />
                </Box>
                <Typography variant="h6">{metrics?.on_time_rate || 0}%</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <ScheduleIcon color="primary" />
                <Typography variant="body2" color="text.secondary">
                  Avg Cycle Time
                </Typography>
              </Box>
              <Typography variant="h6">
                {metrics?.avg_cycle_time_days?.toFixed(0) || '-'}
                <Typography variant="caption" color="text.secondary">
                  {' '}days
                </Typography>
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="Projects" />
          <Tab label="Metrics" />
          <Tab label="Contact Info" />
        </Tabs>
        <Divider />

        {/* Projects Tab */}
        <TabPanel value={tabValue} index={0}>
          {projectsLoading ? (
            <Skeleton variant="rectangular" height={200} />
          ) : projects.length === 0 ? (
            <Typography color="text.secondary" align="center" sx={{ py: 4 }}>
              No projects found for this vendor.
            </Typography>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Work Order</TableCell>
                    <TableCell>Description</TableCell>
                    <TableCell>Region</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Priority</TableCell>
                    <TableCell>Authorized</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {projects.map((project) => (
                    <TableRow
                      key={project.id}
                      hover
                      sx={{ cursor: 'pointer' }}
                      onClick={() => navigate(`/projects/${project.id}`)}
                    >
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {project.work_order_number}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ maxWidth: 300 }} noWrap>
                          {project.description || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>{project.region || '-'}</TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={project.status.replace(/_/g, ' ')}
                          color={STATUS_COLORS[project.status] || 'default'}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={project.priority}
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>{project.authorized_date ? formatDate(project.authorized_date) : '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </TabPanel>

        {/* Metrics Tab */}
        <TabPanel value={tabValue} index={1}>
          {metricsLoading ? (
            <Skeleton variant="rectangular" height={200} />
          ) : !metrics ? (
            <Typography color="text.secondary" align="center" sx={{ py: 4 }}>
              No metrics available for this vendor.
            </Typography>
          ) : (
            <Grid container spacing={3} sx={{ px: 2 }}>
              <Grid item xs={12} sm={6} md={3}>
                <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h3" color="primary">
                    {metrics.total_projects}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Projects
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h3" color="success.main">
                    {metrics.completed_projects}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Completed
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h3" color="warning.main">
                    {metrics.active_projects}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Active
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h3" color="error.main">
                    {metrics.overdue_projects || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Overdue
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
              </Grid>
              <Grid item xs={12} sm={4}>
                <Typography variant="subtitle2" color="text.secondary">
                  On-Time Rate
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                  <Box sx={{ flexGrow: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={metrics.on_time_rate || 0}
                      sx={{ height: 10, borderRadius: 5 }}
                    />
                  </Box>
                  <Typography variant="body1" fontWeight="medium">
                    {metrics.on_time_rate || 0}%
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Typography variant="subtitle2" color="text.secondary">
                  SLA Compliance
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                  <Box sx={{ flexGrow: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={metrics.sla_compliance_rate || 0}
                      color="secondary"
                      sx={{ height: 10, borderRadius: 5 }}
                    />
                  </Box>
                  <Typography variant="body1" fontWeight="medium">
                    {metrics.sla_compliance_rate || 0}%
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Typography variant="subtitle2" color="text.secondary">
                  Revision Rate
                </Typography>
                <Typography variant="h6" sx={{ mt: 1 }}>
                  {metrics.revision_rate?.toFixed(2) || '-'}
                </Typography>
              </Grid>
            </Grid>
          )}
        </TabPanel>

        {/* Contact Info Tab */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3} sx={{ px: 2 }}>
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <PersonIcon color="action" />
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Contact Name
                  </Typography>
                  <Typography variant="body1">
                    {vendor.contact_name || 'Not specified'}
                  </Typography>
                </Box>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <EmailIcon color="action" />
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Email
                  </Typography>
                  <Typography variant="body1">
                    {vendor.contact_email ? (
                      <a href={`mailto:${vendor.contact_email}`}>{vendor.contact_email}</a>
                    ) : (
                      'Not specified'
                    )}
                  </Typography>
                </Box>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <PhoneIcon color="action" />
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Phone
                  </Typography>
                  <Typography variant="body1">
                    {vendor.contact_phone ? (
                      <a href={`tel:${vendor.contact_phone}`}>{vendor.contact_phone}</a>
                    ) : (
                      'Not specified'
                    )}
                  </Typography>
                </Box>
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Vendor ID
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                {vendor.vendor_id}
              </Typography>
              <Typography variant="subtitle2" color="text.secondary">
                Created
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                {formatDate(vendor.created_at)}
              </Typography>
              {vendor.updated_at && (
                <>
                  <Typography variant="subtitle2" color="text.secondary">
                    Last Updated
                  </Typography>
                  <Typography variant="body2">
                    {formatDate(vendor.updated_at)}
                  </Typography>
                </>
              )}
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>

      {/* Vendor Form Modal */}
      <VendorFormModal
        open={modalOpen}
        onClose={handleCloseModal}
        vendor={vendor ? { ...vendor, vendor_id: vendor.vendor_id } : undefined}
        onSuccess={handleModalSuccess}
      />
    </Box>
  );
}
