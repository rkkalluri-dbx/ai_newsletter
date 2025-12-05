import { useState, useEffect } from 'react';
import {
  Grid,
  TextField,
  FormControlLabel,
  Switch,
} from '@mui/material';
import FormModal from '../common/FormModal';
import { useCreateVendor, useUpdateVendor } from '../../hooks/useQueries';

interface VendorFormData {
  vendor_name: string;
  contact_name: string;
  contact_email: string;
  contact_phone: string;
  is_active: boolean;
}

interface VendorFormModalProps {
  open: boolean;
  onClose: () => void;
  vendor?: {
    vendor_id?: string;
    vendor_name?: string;
    contact_name?: string;
    contact_email?: string;
    contact_phone?: string;
    is_active?: boolean;
  };
  onSuccess?: () => void;
}

const initialFormData: VendorFormData = {
  vendor_name: '',
  contact_name: '',
  contact_email: '',
  contact_phone: '',
  is_active: true,
};

export default function VendorFormModal({
  open,
  onClose,
  vendor,
  onSuccess,
}: VendorFormModalProps) {
  const [formData, setFormData] = useState<VendorFormData>(initialFormData);
  const [errors, setErrors] = useState<Partial<Record<keyof VendorFormData, string>>>({});

  const createVendor = useCreateVendor();
  const updateVendor = useUpdateVendor();

  const isEditing = !!vendor?.vendor_id;

  useEffect(() => {
    if (vendor) {
      setFormData({
        vendor_name: vendor.vendor_name || '',
        contact_name: vendor.contact_name || '',
        contact_email: vendor.contact_email || '',
        contact_phone: vendor.contact_phone || '',
        is_active: vendor.is_active ?? true,
      });
    } else {
      setFormData(initialFormData);
    }
    setErrors({});
  }, [vendor, open]);

  const handleChange = (field: keyof VendorFormData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = field === 'is_active' ? e.target.checked : e.target.value;
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof VendorFormData, string>> = {};

    if (!formData.vendor_name.trim()) {
      newErrors.vendor_name = 'Vendor name is required';
    }
    if (formData.contact_email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.contact_email)) {
      newErrors.contact_email = 'Invalid email format';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) return;

    try {
      if (isEditing && vendor?.vendor_id) {
        await updateVendor.mutateAsync({
          id: vendor.vendor_id,
          data: formData as unknown as Record<string, unknown>,
        });
      } else {
        await createVendor.mutateAsync(formData as unknown as Record<string, unknown>);
      }
      onSuccess?.();
      onClose();
    } catch (error) {
      console.error('Failed to save vendor:', error);
    }
  };

  const isSubmitting = createVendor.isPending || updateVendor.isPending;

  return (
    <FormModal
      open={open}
      onClose={onClose}
      title={isEditing ? 'Edit Vendor' : 'New Vendor'}
      onSubmit={handleSubmit}
      submitLabel={isEditing ? 'Update' : 'Create'}
      isSubmitting={isSubmitting}
    >
      <Grid container spacing={2} sx={{ mt: 0.5 }}>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Vendor Name"
            value={formData.vendor_name}
            onChange={handleChange('vendor_name')}
            error={!!errors.vendor_name}
            helperText={errors.vendor_name}
            required
          />
        </Grid>

        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Contact Name"
            value={formData.contact_name}
            onChange={handleChange('contact_name')}
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            type="email"
            label="Contact Email"
            value={formData.contact_email}
            onChange={handleChange('contact_email')}
            error={!!errors.contact_email}
            helperText={errors.contact_email}
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Contact Phone"
            value={formData.contact_phone}
            onChange={handleChange('contact_phone')}
          />
        </Grid>

        <Grid item xs={12}>
          <FormControlLabel
            control={
              <Switch
                checked={formData.is_active}
                onChange={handleChange('is_active')}
              />
            }
            label="Active Vendor"
          />
        </Grid>
      </Grid>
    </FormModal>
  );
}
