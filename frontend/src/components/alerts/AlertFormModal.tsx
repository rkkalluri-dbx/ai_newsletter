import { useState, useEffect } from 'react';
import {
  Grid,
  TextField,
  MenuItem,
} from '@mui/material';
import FormModal from '../common/FormModal';
import { useProjects, useCreateAlert } from '../../hooks/useQueries';

interface AlertFormData {
  project_id: string;
  alert_type: string;
  message: string;
  severity: string;
}

interface AlertFormModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const ALERT_TYPES = [
  { value: 'milestone_overdue', label: 'Milestone Overdue' },
  { value: 'milestone_approaching', label: 'Milestone Approaching' },
  { value: 'status_change', label: 'Status Change' },
  { value: 'revision_added', label: 'Revision Added' },
];

const SEVERITIES = [
  { value: 'info', label: 'Info', color: '#2196f3' },
  { value: 'warning', label: 'Warning', color: '#ff9800' },
  { value: 'critical', label: 'Critical', color: '#f44336' },
];

const initialFormData: AlertFormData = {
  project_id: '',
  alert_type: 'milestone_overdue',
  message: '',
  severity: 'info',
};

export default function AlertFormModal({
  open,
  onClose,
  onSuccess,
}: AlertFormModalProps) {
  const [formData, setFormData] = useState<AlertFormData>(initialFormData);
  const [errors, setErrors] = useState<Partial<Record<keyof AlertFormData, string>>>({});

  const { data: projectsData } = useProjects({ per_page: 100 });
  const createAlert = useCreateAlert();

  const projects = projectsData?.data || [];

  useEffect(() => {
    if (open) {
      setFormData(initialFormData);
      setErrors({});
    }
  }, [open]);

  const handleChange = (field: keyof AlertFormData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = e.target.value;
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof AlertFormData, string>> = {};

    if (!formData.project_id) {
      newErrors.project_id = 'Project is required';
    }
    if (!formData.alert_type) {
      newErrors.alert_type = 'Alert type is required';
    }
    if (!formData.message.trim()) {
      newErrors.message = 'Message is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) return;

    try {
      await createAlert.mutateAsync(formData);
      onSuccess?.();
      onClose();
    } catch (error) {
      console.error('Failed to create alert:', error);
    }
  };

  const isSubmitting = createAlert.isPending;

  return (
    <FormModal
      open={open}
      onClose={onClose}
      title="Create Alert"
      onSubmit={handleSubmit}
      submitLabel="Create"
      isSubmitting={isSubmitting}
    >
      <Grid container spacing={2} sx={{ mt: 0.5 }}>
        <Grid item xs={12}>
          <TextField
            fullWidth
            select
            label="Project"
            value={formData.project_id}
            onChange={handleChange('project_id')}
            error={!!errors.project_id}
            helperText={errors.project_id}
            required
          >
            {projects.map((project: { project_id: string; project_name: string }) => (
              <MenuItem key={project.project_id} value={project.project_id}>
                {project.project_name}
              </MenuItem>
            ))}
          </TextField>
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            select
            label="Alert Type"
            value={formData.alert_type}
            onChange={handleChange('alert_type')}
            error={!!errors.alert_type}
            helperText={errors.alert_type}
            required
          >
            {ALERT_TYPES.map((type) => (
              <MenuItem key={type.value} value={type.value}>
                {type.label}
              </MenuItem>
            ))}
          </TextField>
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            select
            label="Severity"
            value={formData.severity}
            onChange={handleChange('severity')}
          >
            {SEVERITIES.map((sev) => (
              <MenuItem key={sev.value} value={sev.value}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span
                    style={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      backgroundColor: sev.color,
                    }}
                  />
                  {sev.label}
                </span>
              </MenuItem>
            ))}
          </TextField>
        </Grid>

        <Grid item xs={12}>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Message"
            value={formData.message}
            onChange={handleChange('message')}
            error={!!errors.message}
            helperText={errors.message}
            placeholder="Describe the alert..."
            required
          />
        </Grid>
      </Grid>
    </FormModal>
  );
}
