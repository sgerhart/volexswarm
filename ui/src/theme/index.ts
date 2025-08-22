import { createTheme, ThemeOptions } from '@mui/material/styles';
import type { PaletteMode } from '@mui/material/styles';

// Custom color palette for trading dashboard
const lightPalette = {
  primary: {
    main: '#1976d2',
    light: '#42a5f5',
    dark: '#1565c0',
    contrastText: '#ffffff',
  },
  secondary: {
    main: '#dc004e',
    light: '#ff5983',
    dark: '#9a0036',
    contrastText: '#ffffff',
  },
  background: {
    default: '#fafafa',
    paper: '#ffffff',
  },
  surface: {
    main: '#ffffff',
    light: '#f5f5f5',
    dark: '#e0e0e0',
  },
  text: {
    primary: '#212121',
    secondary: '#757575',
  },
  success: {
    main: '#4caf50',
    light: '#81c784',
    dark: '#388e3c',
  },
  warning: {
    main: '#ff9800',
    light: '#ffb74d',
    dark: '#f57c00',
  },
  error: {
    main: '#f44336',
    light: '#e57373',
    dark: '#d32f2f',
  },
  info: {
    main: '#2196f3',
    light: '#64b5f6',
    dark: '#1976d2',
  },
  // Trading-specific colors
  profit: {
    main: '#00c853',
    light: '#69f0ae',
    dark: '#00e676',
  },
  loss: {
    main: '#ff1744',
    light: '#ff616f',
    dark: '#d50000',
  },
  neutral: {
    main: '#9e9e9e',
    light: '#cfd8dc',
    dark: '#757575',
  },
};

const darkPalette = {
  primary: {
    main: '#90caf9',
    light: '#e3f2fd',
    dark: '#42a5f5',
    contrastText: '#000000',
  },
  secondary: {
    main: '#f48fb1',
    light: '#fce4ec',
    dark: '#ec407a',
    contrastText: '#000000',
  },
  background: {
    default: '#0a0a0a',
    paper: '#1a1a1a',
  },
  surface: {
    main: '#1a1a1a',
    light: '#2a2a2a',
    dark: '#0a0a0a',
  },
  text: {
    primary: '#ffffff',
    secondary: '#b0b0b0',
  },
  success: {
    main: '#66bb6a',
    light: '#a5d6a7',
    dark: '#4caf50',
  },
  warning: {
    main: '#ffb74d',
    light: '#ffcc80',
    dark: '#ff9800',
  },
  error: {
    main: '#ef5350',
    light: '#e57373',
    dark: '#f44336',
  },
  info: {
    main: '#64b5f6',
    light: '#90caf9',
    dark: '#2196f3',
  },
  // Trading-specific colors for dark theme
  profit: {
    main: '#4caf50',
    light: '#81c784',
    dark: '#388e3c',
  },
  loss: {
    main: '#f44336',
    light: '#e57373',
    dark: '#d32f2f',
  },
  neutral: {
    main: '#9e9e9e',
    light: '#e0e0e0',
    dark: '#616161',
  },
};

// Common theme options
const commonThemeOptions: ThemeOptions = {
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 300,
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 300,
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 400,
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 400,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 400,
      lineHeight: 1.4,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.4,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.43,
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 16px',
          fontWeight: 500,
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          '&:hover': {
            boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundImage: 'none',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid rgba(224, 224, 224, 1)',
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          '& .MuiTableCell-root': {
            fontWeight: 600,
            backgroundColor: 'rgba(0, 0, 0, 0.02)',
          },
        },
      },
    },
  },
};

// Light theme
export const lightTheme = createTheme({
  ...commonThemeOptions,
  palette: {
    mode: 'light',
    ...lightPalette,
  },
});

// Dark theme
export const darkTheme = createTheme({
  ...commonThemeOptions,
  palette: {
    mode: 'dark',
    ...darkPalette,
  },
});

// Theme context and hook
export const getTheme = (mode: PaletteMode) => {
  return mode === 'light' ? lightTheme : darkTheme;
};

// Export theme types
export type { ThemeOptions };
export { PaletteMode };
