export const COLORS = {
  primary: '#2E7D32',
  primaryLight: '#4CAF50',
  primaryDark: '#1B5E20',
  secondary: '#1976D2',
  secondaryLight: '#42A5F5',
  accent: '#FF9800',
  background: '#F5F5F5',
  surface: '#FFFFFF',
  error: '#D32F2F',
  warning: '#FFA000',
  success: '#388E3C',
  text: '#212121',
  textSecondary: '#757575',
  textLight: '#BDBDBD',
  border: '#E0E0E0',
  divider: '#EEEEEE',
};

export const FUEL_TYPE_COLORS: Record<string, string> = {
  CNG: '#4CAF50',
  LNG: '#2196F3',
  Hydrogen: '#9C27B0',
  Electric: '#FF9800',
  Diesel: '#795548',
  Gasoline: '#F44336',
  Biodiesel: '#8BC34A',
  E85: '#FF5722',
  LPG: '#00BCD4',
};

export const FUEL_TYPE_ICONS: Record<string, string> = {
  CNG: 'gas-cylinder',
  LNG: 'snowflake',
  Hydrogen: 'atom',
  Electric: 'flash',
  Diesel: 'water',
  Gasoline: 'water',
  Biodiesel: 'leaf',
  E85: 'water',
  LPG: 'flame',
};

export const STATUS_COLORS: Record<string, string> = {
  Operational: '#4CAF50',
  'Under Maintenance': '#FFA000',
  'Temporarily Unavailable': '#FFA000',
  Closed: '#D32F2F',
  Planned: '#2196F3',
  Unknown: '#757575',
};

export const FUEL_TYPES = [
  { id: 'Electric', name: 'Electric (EV)', icon: 'flash' },
  { id: 'CNG', name: 'Compressed Natural Gas', icon: 'gas-cylinder' },
  { id: 'LNG', name: 'Liquefied Natural Gas', icon: 'snowflake' },
  { id: 'Hydrogen', name: 'Hydrogen', icon: 'atom' },
  { id: 'Biodiesel', name: 'Biodiesel', icon: 'leaf' },
  { id: 'E85', name: 'Ethanol (E85)', icon: 'water' },
  { id: 'LPG', name: 'Propane (LPG)', icon: 'flame' },
];
