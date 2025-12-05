import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography,
  Box,
  Paper,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  TextField,
  Chip,
  Skeleton,
  Alert,
  InputAdornment,
  FormControlLabel,
  Switch,
  LinearProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Search as SearchIcon,
  Business as BusinessIcon,
  Add as AddIcon,
  TrendingUp as TrendingUpIcon,
  Assignment as ProjectIcon,
  Edit as EditIcon,
} from '@mui/icons-material';
import { useVendors } from '../hooks/useQueries';
import VendorFormModal from '../components/vendors/VendorFormModal';

interface Vendor {
  vendor_id: string;
  vendor_name: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  is_active: boolean;
  total_projects?: number;
  active_projects?: number;
  on_time_percentage?: number;
  created_at: string;
}

export default function Vendors() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [activeOnly, setActiveOnly] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingVendor, setEditingVendor] = useState<Vendor | null>(null);

  const { data, isLoading, error, refetch } = useVendors({
    search: search || undefined,
    active_only: activeOnly || undefined,
  });

  const vendors: Vendor[] = data?.data || [];

  const handleOpenCreate = () => {
    setEditingVendor(null);
    setModalOpen(true);
  };

  const handleOpenEdit = (vendor: Vendor) => {
    setEditingVendor(vendor);
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setEditingVendor(null);
  };

  const handleModalSuccess = () => {
    refetch();
  };

  if (error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Vendors
        </Typography>
        <Alert severity="error">
          Failed to load vendors. Please ensure the backend is running.
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
            Vendors
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage vendor relationships and performance
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleOpenCreate}>
          Add Vendor
        </Button>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              size="small"
              placeholder="Search vendors..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon color="action" />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <FormControlLabel
              control={
                <Switch
                  checked={activeOnly}
                  onChange={(e) => setActiveOnly(e.target.checked)}
                />
              }
              label="Active vendors only"
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Vendor Cards */}
      {isLoading ? (
        <Grid container spacing={3}>
          {Array.from({ length: 6 }).map((_, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <Card>
                <CardContent>
                  <Skeleton variant="text" width="60%" height={32} />
                  <Skeleton variant="text" width="40%" />
                  <Skeleton variant="rectangular" height={60} sx={{ mt: 2 }} />
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : vendors.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <BusinessIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            No vendors found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {search ? 'Try adjusting your search criteria' : 'Get started by adding your first vendor'}
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {vendors.map((vendor) => (
            <Grid item xs={12} sm={6} md={4} key={vendor.vendor_id}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  cursor: 'pointer',
                  '&:hover': {
                    boxShadow: 4,
                  },
                }}
                onClick={() => navigate(`/vendors/${vendor.vendor_id}`)}
              >
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <BusinessIcon color="primary" />
                      <Typography variant="h6" component="div">
                        {vendor.vendor_name}
                      </Typography>
                    </Box>
                    <Chip
                      size="small"
                      label={vendor.is_active ? 'Active' : 'Inactive'}
                      color={vendor.is_active ? 'success' : 'default'}
                    />
                  </Box>

                  {vendor.contact_name && (
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Contact: {vendor.contact_name}
                    </Typography>
                  )}
                  {vendor.contact_email && (
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {vendor.contact_email}
                    </Typography>
                  )}

                  {/* Metrics */}
                  <Box sx={{ mt: 2 }}>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <ProjectIcon fontSize="small" color="action" />
                          <Typography variant="body2" color="text.secondary">
                            Projects
                          </Typography>
                        </Box>
                        <Typography variant="h6">
                          {vendor.active_projects || 0}
                          <Typography variant="caption" color="text.secondary">
                            {' '}/ {vendor.total_projects || 0}
                          </Typography>
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <TrendingUpIcon fontSize="small" color="action" />
                          <Typography variant="body2" color="text.secondary">
                            On-Time
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Box sx={{ flexGrow: 1 }}>
                            <LinearProgress
                              variant="determinate"
                              value={vendor.on_time_percentage || 0}
                              color={
                                (vendor.on_time_percentage || 0) >= 80
                                  ? 'success'
                                  : (vendor.on_time_percentage || 0) >= 60
                                  ? 'warning'
                                  : 'error'
                              }
                              sx={{ height: 6, borderRadius: 3 }}
                            />
                          </Box>
                          <Typography variant="body2" fontWeight="medium">
                            {vendor.on_time_percentage || 0}%
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  </Box>
                </CardContent>
                <CardActions sx={{ justifyContent: 'space-between' }}>
                  <Button
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/vendors/${vendor.vendor_id}`);
                    }}
                  >
                    View Details
                  </Button>
                  <Tooltip title="Edit Vendor">
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleOpenEdit(vendor);
                      }}
                    >
                      <EditIcon />
                    </IconButton>
                  </Tooltip>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Vendor Form Modal */}
      <VendorFormModal
        open={modalOpen}
        onClose={handleCloseModal}
        vendor={editingVendor ? { ...editingVendor, vendor_id: editingVendor.vendor_id } : undefined}
        onSuccess={handleModalSuccess}
      />
    </Box>
  );
}
