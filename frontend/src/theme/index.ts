import { createTheme } from '@mui/material/styles';

// Power & Utility Color Palette
// Focused on high contrast, clarity, and "engineered" reliability.
const PRIMARY_BLUE = '#002D9C'; // Deep Reliability Blue - Stable & Trustworthy
const PRIMARY_DARK = '#001D66';
const PRIMARY_LIGHT = '#4589FF'; // Active/Highlight Blue

const SECONDARY_TEAL = '#005D5D'; // Energy Teal - Sustainable & Flow
const SECONDARY_DARK = '#004144';
const SECONDARY_LIGHT = '#08BDBA';

const BACKGROUND_DEFAULT = '#F4F4F4'; // Industrial Grey - Low Eye Strain
const PAPER_WHITE = '#FFFFFF';
const BORDER_COLOR = '#E0E0E0'; // Crisp borders

// Status Colors - Standard SCADA/HMI conventions
const STATUS_SUCCESS = '#198038'; // "Good" Green
const STATUS_WARNING = '#F1C21B'; // Warning Yellow
const STATUS_CRITICAL = '#DA1E28'; // Alarm Red
const STATUS_INFO = '#0043CE';    // Information Blue

// Chart Colors - High distinction for data visualization
export const CHART_COLORS = [
  '#002D9C', // Primary Blue
  '#005D5D', // Teal
  '#DA1E28', // Red (Critical)
  '#F1C21B', // Yellow (Warning)
  '#8A3FFC', // Purple (Auxiliary)
  '#6929C4', // Violet
];

export const theme = createTheme({
  palette: {
    primary: {
      main: PRIMARY_BLUE,
      light: PRIMARY_LIGHT,
      dark: PRIMARY_DARK,
      contrastText: '#ffffff',
    },
    secondary: {
      main: SECONDARY_TEAL,
      light: SECONDARY_LIGHT,
      dark: SECONDARY_DARK,
      contrastText: '#ffffff',
    },
    background: {
      default: BACKGROUND_DEFAULT,
      paper: PAPER_WHITE,
    },
    text: {
      primary: '#161616', // High contrast for legibility
      secondary: '#525252',
    },
    success: {
      main: STATUS_SUCCESS,
    },
    warning: {
      main: STATUS_WARNING,
      light: '#FDD13A',
    },
    error: {
      main: STATUS_CRITICAL,
    },
    info: {
      main: STATUS_INFO,
    },
    divider: BORDER_COLOR,
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: { fontWeight: 600, letterSpacing: '-0.01em', color: '#161616' },
    h2: { fontWeight: 600, letterSpacing: '-0.01em', color: '#161616' },
    h3: { fontWeight: 600, letterSpacing: '0em', color: '#161616' },
    h4: { fontWeight: 600, letterSpacing: '0em', color: '#161616' },
    h5: { fontWeight: 600, color: '#161616' },
    h6: { fontWeight: 600, color: '#161616' },
    subtitle1: { fontWeight: 500, color: '#525252' },
    subtitle2: { fontWeight: 500, color: '#525252' },
    button: { fontWeight: 600, textTransform: 'none', letterSpacing: '0.01em' },
    body1: { fontSize: '0.875rem', lineHeight: 1.5 }, // Slightly smaller for density
    body2: { fontSize: '0.75rem', lineHeight: 1.5 },
  },
  shape: {
    borderRadius: 4, // "Engineered" look - sharper corners
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: BACKGROUND_DEFAULT,
          scrollbarWidth: 'thin',
          '&::-webkit-scrollbar': {
            width: '8px',
            height: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: '#e0e0e0',
          },
          '&::-webkit-scrollbar-thumb': {
            background: '#8d8d8d',
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-thumb:hover': {
            background: '#6e6e6e',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.05)', // Subtle, functional shadow
          border: `1px solid ${BORDER_COLOR}`, // Explicit boundary
          backgroundColor: PAPER_WHITE,
          transition: 'none', // Remove "floaty" transitions for stability
          '&:hover': {
            borderColor: PRIMARY_BLUE, // Active state indication
            transform: 'none',
            boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.05)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
        rounded: {
          borderRadius: 4,
        },
        elevation1: {
          boxShadow: '0px 1px 3px rgba(0, 0, 0, 0.1)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          padding: '6px 16px', // Compact padding
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
            backgroundColor: PRIMARY_DARK, // Clear hover state
          },
        },
        containedPrimary: {
          background: PRIMARY_BLUE, // Solid fill, no gradients
          '&:hover': {
            background: PRIMARY_DARK,
          },
        },
        outlined: {
          borderWidth: '1px',
          borderColor: BORDER_COLOR,
          '&:hover': {
            borderWidth: '1px',
            borderColor: PRIMARY_BLUE,
            backgroundColor: 'rgba(0, 45, 156, 0.04)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 4, // Consistent squared look
          fontWeight: 600,
          height: '24px', // Compact chips
        },
        label: {
          paddingLeft: 8,
          paddingRight: 8,
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          padding: '8px 16px', // High density data tables
          borderBottom: `1px solid ${BORDER_COLOR}`,
        },
        head: {
          fontWeight: 600,
          backgroundColor: '#F2F4F8',
          color: '#161616',
          borderBottom: `2px solid ${BORDER_COLOR}`, // Distinct header separation
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 4,
        },
        standardSuccess: {
          backgroundColor: '#DEFBE6',
          color: '#0E6027',
        },
        standardWarning: {
          backgroundColor: '#FCF2BD',
          color: '#161616',
        },
        standardError: {
          backgroundColor: '#FFF1F1',
          color: '#DA1E28',
        },
        standardInfo: {
          backgroundColor: '#EDF5FF',
          color: '#0043CE',
        },
      },
    },
  },
});

