import { createTheme } from '@mui/material/styles';

// Southern Company brand colors
const SOUTHERN_BLUE = '#0033A0';
const SOUTHERN_BLUE_LIGHT = '#1E5BC6';
const SOUTHERN_BLUE_DARK = '#002575';

export const theme = createTheme({
  palette: {
    primary: {
      main: SOUTHERN_BLUE,
      light: SOUTHERN_BLUE_LIGHT,
      dark: SOUTHERN_BLUE_DARK,
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#6C757D',
      light: '#868E96',
      dark: '#495057',
    },
    success: {
      main: '#28A745',
      light: '#48C764',
      dark: '#1E7E34',
    },
    warning: {
      main: '#FFC107',
      light: '#FFCD39',
      dark: '#D39E00',
    },
    error: {
      main: '#DC3545',
      light: '#E4606D',
      dark: '#BD2130',
    },
    background: {
      default: '#F8F9FA',
      paper: '#FFFFFF',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 500,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 500,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 500,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 500,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 500,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 4,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 4,
        },
      },
    },
  },
});
