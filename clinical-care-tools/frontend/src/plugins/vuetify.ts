import 'vuetify/styles'
import { createVuetify, type ThemeDefinition } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi'

// Define custom themes
const lightTheme: ThemeDefinition = {
  dark: false,
  colors: {
    background: '#FFFFFF',
    surface: '#F5F5F5',
    'surface-variant': '#E0E0E0',
    primary: '#1976D2',
    'primary-darken-1': '#1565C0',
    secondary: '#424242',
    'secondary-darken-1': '#212121',
    error: '#D32F2F',
    info: '#0288D1',
    success: '#388E3C',
    warning: '#FFA000',
    'on-background': '#000000',
    'on-surface': '#000000',
    'on-primary': '#FFFFFF',
    'on-secondary': '#FFFFFF',
    'on-error': '#FFFFFF',
    'on-info': '#FFFFFF',
    'on-success': '#FFFFFF',
    'on-warning': '#FFFFFF'
  },
  variables: {
    'border-color': '#E0E0E0',
    'border-opacity': 0.12,
    'high-emphasis-opacity': 0.87,
    'medium-emphasis-opacity': 0.60,
    'disabled-opacity': 0.38,
    'idle-opacity': 0.04,
    'hover-opacity': 0.04,
    'focus-opacity': 0.12,
    'selected-opacity': 0.08,
    'activated-opacity': 0.12,
    'pressed-opacity': 0.12,
    'dragged-opacity': 0.08,
    'theme-overlay-multiplier': 1
  }
}

const darkTheme: ThemeDefinition = {
  dark: true,
  colors: {
    background: '#121212',
    surface: '#1E1E1E',
    'surface-variant': '#2D2D2D',
    primary: '#2196F3',
    'primary-darken-1': '#1976D2',
    secondary: '#00BCD4',
    'secondary-darken-1': '#00ACC1',
    error: '#F44336',
    info: '#03A9F4',
    success: '#4CAF50',
    warning: '#FF9800',
    'on-background': '#FFFFFF',
    'on-surface': '#FFFFFF',
    'on-primary': '#FFFFFF',
    'on-secondary': '#000000',
    'on-error': '#FFFFFF',
    'on-info': '#FFFFFF',
    'on-success': '#FFFFFF',
    'on-warning': '#000000'
  },
  variables: {
    'border-color': '#FFFFFF',
    'border-opacity': 0.12,
    'high-emphasis-opacity': 1,
    'medium-emphasis-opacity': 0.70,
    'disabled-opacity': 0.50,
    'idle-opacity': 0.10,
    'hover-opacity': 0.04,
    'focus-opacity': 0.12,
    'selected-opacity': 0.08,
    'activated-opacity': 0.12,
    'pressed-opacity': 0.16,
    'dragged-opacity': 0.08,
    'theme-overlay-multiplier': 2
  }
}

// Healthcare-specific theme (optional)
const healthcareTheme: ThemeDefinition = {
  dark: false,
  colors: {
    background: '#FAFAFA',
    surface: '#FFFFFF',
    primary: '#00695C', // Teal 800
    'primary-darken-1': '#00574B',
    secondary: '#37474F', // Blue Grey 800
    'secondary-darken-1': '#263238',
    error: '#C62828',
    info: '#0277BD',
    success: '#2E7D32',
    warning: '#E65100',
    accent: '#00838F'
  }
}

// Create Vuetify instance
export default createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: {
      mdi
    }
  },
  theme: {
    defaultTheme: 'light',
    themes: {
      light: lightTheme,
      dark: darkTheme,
      healthcare: healthcareTheme
    },
    variations: {
      colors: ['primary', 'secondary', 'accent'],
      lighten: 5,
      darken: 5
    }
  },
  defaults: {
    VApp: {
      style: 'min-height: 100vh;'
    },
    VBtn: {
      variant: 'flat',
      rounded: 'md'
    },
    VTextField: {
      variant: 'outlined',
      density: 'comfortable',
      color: 'primary'
    },
    VTextarea: {
      variant: 'outlined',
      color: 'primary'
    },
    VSelect: {
      variant: 'outlined',
      density: 'comfortable',
      color: 'primary'
    },
    VAutocomplete: {
      variant: 'outlined',
      density: 'comfortable',
      color: 'primary'
    },
    VCard: {
      rounded: 'lg',
      elevation: 2
    },
    VChip: {
      rounded: 'md'
    },
    VAlert: {
      rounded: 'md'
    },
    VDataTable: {
      fixedHeader: true,
      hover: true
    },
    VDialog: {
      scrim: true,
      persistent: false
    }
  },
  display: {
    mobileBreakpoint: 'sm',
    thresholds: {
      xs: 0,
      sm: 600,
      md: 960,
      lg: 1280,
      xl: 1920,
      xxl: 2560
    }
  }
})