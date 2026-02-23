import { Linking, Platform, Alert, ActionSheetIOS } from 'react-native';

export interface NavigationDestination {
  latitude: number;
  longitude: number;
  name: string;
  address?: string;
}

type MapApp = 'google' | 'apple' | 'waze';

const mapAppNames: Record<MapApp, string> = {
  google: 'Google Maps',
  apple: 'Apple Maps',
  waze: 'Waze',
};

// Generate URL for each map app
const getMapUrl = (app: MapApp, destination: NavigationDestination): string => {
  const { latitude, longitude, name, address } = destination;
  const encodedName = encodeURIComponent(name);
  const encodedAddress = address ? encodeURIComponent(address) : '';

  switch (app) {
    case 'google':
      // Google Maps - works on all platforms
      return `https://www.google.com/maps/dir/?api=1&destination=${latitude},${longitude}&destination_place_id=${encodedName}`;
    
    case 'apple':
      // Apple Maps - iOS only, but web fallback works
      if (Platform.OS === 'ios') {
        return `maps://app?daddr=${latitude},${longitude}&q=${encodedName}`;
      }
      // Fallback to web version for non-iOS
      return `https://maps.apple.com/?daddr=${latitude},${longitude}&q=${encodedName}`;
    
    case 'waze':
      // Waze - works on all platforms
      return `https://waze.com/ul?ll=${latitude},${longitude}&navigate=yes&q=${encodedName}`;
    
    default:
      return `https://www.google.com/maps/dir/?api=1&destination=${latitude},${longitude}`;
  }
};

// Check if a specific map app is available
const canOpenMapApp = async (app: MapApp): Promise<boolean> => {
  try {
    if (app === 'apple' && Platform.OS === 'ios') {
      return await Linking.canOpenURL('maps://');
    }
    if (app === 'waze') {
      return await Linking.canOpenURL('waze://');
    }
    if (app === 'google') {
      // Google Maps app check
      const canOpenApp = await Linking.canOpenURL('comgooglemaps://');
      return canOpenApp || true; // Web fallback always works
    }
    return true; // Web fallbacks always work
  } catch {
    return true; // Assume web fallback works
  }
};

// Open navigation in a specific map app
export const openNavigation = async (
  destination: NavigationDestination,
  preferredApp?: MapApp
): Promise<void> => {
  const url = getMapUrl(preferredApp || 'google', destination);
  
  try {
    const supported = await Linking.canOpenURL(url);
    if (supported) {
      await Linking.openURL(url);
    } else {
      // Fallback to Google Maps web
      const fallbackUrl = getMapUrl('google', destination);
      await Linking.openURL(fallbackUrl);
    }
  } catch (error) {
    console.error('Error opening navigation:', error);
    Alert.alert(
      'Navigation Error',
      'Unable to open maps. Please try again.',
      [{ text: 'OK' }]
    );
  }
};

// Show map app picker (iOS uses ActionSheet, Android/Web uses Alert)
export const showNavigationPicker = async (
  destination: NavigationDestination
): Promise<void> => {
  const availableApps: MapApp[] = ['google', 'waze'];
  
  // Add Apple Maps for iOS
  if (Platform.OS === 'ios') {
    availableApps.unshift('apple');
  }

  if (Platform.OS === 'ios') {
    // iOS ActionSheet
    ActionSheetIOS.showActionSheetWithOptions(
      {
        options: ['Cancel', ...availableApps.map(app => mapAppNames[app])],
        cancelButtonIndex: 0,
        title: 'Open in Maps',
        message: `Get directions to ${destination.name}`,
      },
      (buttonIndex) => {
        if (buttonIndex > 0) {
          const selectedApp = availableApps[buttonIndex - 1];
          openNavigation(destination, selectedApp);
        }
      }
    );
  } else {
    // Android/Web - use Alert with buttons
    Alert.alert(
      'Open in Maps',
      `Get directions to ${destination.name}`,
      [
        { text: 'Cancel', style: 'cancel' },
        ...availableApps.map(app => ({
          text: mapAppNames[app],
          onPress: () => openNavigation(destination, app),
        })),
      ]
    );
  }
};

// Quick navigation - opens default map app directly
export const quickNavigate = async (destination: NavigationDestination): Promise<void> => {
  // Default to Google Maps as it works everywhere
  const defaultApp: MapApp = Platform.OS === 'ios' ? 'apple' : 'google';
  await openNavigation(destination, defaultApp);
};

// Format distance for display
export const formatNavigationDistance = (miles: number, km: number): string => {
  return `${miles} mi (${km} km)`;
};
