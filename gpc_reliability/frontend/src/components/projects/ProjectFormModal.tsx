import { useState, useEffect } from 'react';
import {
  Grid,
  TextField,
  MenuItem,
  InputAdornment,
} from '@mui/material';
import FormModal from '../common/FormModal';
import { useVendors, useCreateProject, useUpdateProject } from '../../hooks/useQueries';

interface ProjectFormData {
  project_name: string;
  vendor_id: string;
  region: string;
  status: string;
  priority: string;
  start_date: string;
  target_completion_date: string;
  budget: number;
  description: string;
  notes: string;
}

interface ProjectFormModalProps {
  open: boolean;
  onClose: () => void;
  project?: {
    project_id?: string;
    project_name?: string;
    vendor_id?: string;
    region?: string;
    status?: string;
    priority?: string;
    start_date?: string;
    target_completion_date?: string;
    budget?: number;
    description?: string;
    notes?: string;
  };
  onSuccess?: () => void;
}

const REGIONS = ['Metro', 'North', 'South', 'Coastal', 'Mountain'];
const STATUSES = ['planning', 'in_progress', 'on_hold', 'completed', 'cancelled'];
const PRIORITIES = ['critical', 'high', 'medium', 'low'];

const initialFormData: ProjectFormData = {
  project_name: '',
  vendor_id: '',
  region: '',
  status: 'planning',
  priority: 'medium',
  start_date: '',
  target_completion_date: '',
  budget: 0,
  description: '',
  notes: '',
};

export default function ProjectFormModal({
  open,
  onClose,
  project,
  onSuccess,
}: ProjectFormModalProps) {
  const [formData, setFormData] = useState<ProjectFormData>(initialFormData);
  const [errors, setErrors] = useState<Partial<Record<keyof ProjectFormData, string>>>({});

  const { data: vendorsData } = useVendors({ active_only: true });
  const createProject = useCreateProject();
  const updateProject = useUpdateProject();

  const vendors = vendorsData?.data || [];
  const isEditing = !!project?.project_id;

  useEffect(() => {
    if (project) {
      setFormData({
        project_name: project.project_name || '',
        vendor_id: project.vendor_id || '',
        region: project.region || '',
        status: project.status || 'planning',
        priority: project.priority || 'medium',
        start_date: project.start_date || '',
        target_completion_date: project.target_completion_date || '',
        budget: project.budget || 0,
        description: project.description || '',
        notes: project.notes || '',
      });
    } else {
      setFormData(initialFormData);
    }
    setErrors({});
  }, [project, open]);

  const handleChange = (field: keyof ProjectFormData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = field === 'budget' ? parseFloat(e.target.value) || 0 : e.target.value;
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof ProjectFormData, string>> = {};

    if (!formData.project_name.trim()) {
      newErrors.project_name = 'Project name is required';
    }
    if (!formData.vendor_id) {
      newErrors.vendor_id = 'Vendor is required';
    }
    if (!formData.region) {
      newErrors.region = 'Region is required';
    }
    if (!formData.start_date) {
      newErrors.start_date = 'Start date is required';
    }
    if (!formData.target_completion_date) {
      newErrors.target_completion_date = 'Target completion date is required';
    }
    if (formData.start_date && formData.target_completion_date) {
      if (new Date(formData.start_date) > new Date(formData.target_completion_date)) {
        newErrors.target_completion_date = 'Target date must be after start date';
      }
    }
    if (formData.budget < 0) {
      newErrors.budget = 'Budget cannot be negative';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) return;

    try {
      if (isEditing && project?.project_id) {
        await updateProject.mutateAsync({
          id: project.project_id,
          data: formData as unknown as Record<string, unknown>,
        });
      } else {
        await createProject.mutateAsync(formData as unknown as Record<string, unknown>);
      }
      onSuccess?.();
      onClose();
    } catch (error) {
      console.error('Failed to save project:', error);
    }
  };

  const isSubmitting = createProject.isPending || updateProject.isPending;

  return (
    <FormModal
      open={open}
      onClose={onClose}
      title={isEditing ? 'Edit Project' : 'New Project'}
      onSubmit={handleSubmit}
      submitLabel={isEditing ? 'Update' : 'Create'}
      isSubmitting={isSubmitting}
      maxWidth="md"
    >
      <Grid container spacing={2} sx={{ mt: 0.5 }}>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Project Name"
            value={formData.project_name}
            onChange={handleChange('project_name')}
            error={!!errors.project_name}
            helperText={errors.project_name}
            required
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            select
            label="Vendor"
            value={formData.vendor_id}
            onChange={handleChange('vendor_id')}
            error={!!errors.vendor_id}
            helperText={errors.vendor_id}
            required
          >
            {vendors.map((vendor: { vendor_id: string; vendor_name: string }) => (
              <MenuItem key={vendor.vendor_id} value={vendor.vendor_id}>
                {vendor.vendor_name}
              </MenuItem>
            ))}
          </TextField>
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            select
            label="Region"
            value={formData.region}
            onChange={handleChange('region')}
            error={!!errors.region}
            helperText={errors.region}
            required
          >
            {REGIONS.map((region) => (
              <MenuItem key={region} value={region}>
                {region}
              </MenuItem>
            ))}
          </TextField>
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            select
            label="Status"
            value={formData.status}
            onChange={handleChange('status')}
          >
            {STATUSES.map((status) => (
              <MenuItem key={status} value={status}>
                {status.replace('_', ' ').charAt(0).toUpperCase() + status.replace('_', ' ').slice(1)}
              </MenuItem>
            ))}
          </TextField>
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            select
            label="Priority"
            value={formData.priority}
            onChange={handleChange('priority')}
          >
            {PRIORITIES.map((priority) => (
              <MenuItem key={priority} value={priority}>
                {priority.charAt(0).toUpperCase() + priority.slice(1)}
              </MenuItem>
            ))}
          </TextField>
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            type="date"
            label="Start Date"
            value={formData.start_date}
            onChange={handleChange('start_date')}
            error={!!errors.start_date}
            helperText={errors.start_date}
            InputLabelProps={{ shrink: true }}
            required
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            type="date"
            label="Target Completion Date"
            value={formData.target_completion_date}
            onChange={handleChange('target_completion_date')}
            error={!!errors.target_completion_date}
            helperText={errors.target_completion_date}
            InputLabelProps={{ shrink: true }}
            required
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            type="number"
            label="Budget"
            value={formData.budget}
            onChange={handleChange('budget')}
            error={!!errors.budget}
            helperText={errors.budget}
            InputProps={{
              startAdornment: <InputAdornment position="start">$</InputAdornment>,
            }}
          />
        </Grid>

        <Grid item xs={12}>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Description"
            value={formData.description}
            onChange={handleChange('description')}
          />
        </Grid>

        <Grid item xs={12}>
          <TextField
            fullWidth
            multiline
            rows={2}
            label="Notes"
            value={formData.notes}
            onChange={handleChange('notes')}
          />
        </Grid>
      </Grid>
    </FormModal>
  );
}
