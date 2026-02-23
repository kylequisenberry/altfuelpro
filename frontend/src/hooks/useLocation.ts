import { useState, useEffect, useCallback } from 'react';
import * as Location from 'expo-location';
import { Platform } from 'react-native';

export interface UserLocation {
  latitude: number;
  longitude: number;
}

export interface LocationState {
  location: UserLocation | null;
  loading: boolean;
  error: string | null;
  permissionStatus: Location.PermissionStatus | null;
}

export const useLocation = () => {
  const [state, setState] = useState<LocationState>({
    location: null,
    loading: false,
    error: null,
    permissionStatus: null,
  });

  const requestLocation = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      // Request permission
      const { status } = await Location.requestForegroundPermissionsAsync();
      setState(prev => ({ ...prev, permissionStatus: status }));

      if (status !== 'granted') {
        setState(prev => ({
          ...prev,
          loading: false,
          error: 'Location permission denied. Please enable location access in your settings.',
        }));
        return null;
      }

      // Get current position
      const position = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });

      const userLocation: UserLocation = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
      };

      setState(prev => ({
        ...prev,
        location: userLocation,
        loading: false,
        error: null,
      }));

      return userLocation;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to get location';
      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      return null;
    }
  }, []);

  // Check if we're on web and use browser geolocation as fallback
  const requestLocationWeb = useCallback(async (): Promise<UserLocation | null> => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    return new Promise((resolve) => {
      if (!navigator.geolocation) {
        setState(prev => ({
          ...prev,
          loading: false,
          error: 'Geolocation is not supported by your browser',
        }));
        resolve(null);
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const userLocation: UserLocation = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          };
          setState(prev => ({
            ...prev,
            location: userLocation,
            loading: false,
            error: null,
          }));
          resolve(userLocation);
        },
        (error) => {
          let errorMessage = 'Failed to get location';
          switch (error.code) {
            case error.PERMISSION_DENIED:
              errorMessage = 'Location permission denied. Please enable location access.';
              break;
            case error.POSITION_UNAVAILABLE:
              errorMessage = 'Location information unavailable.';
              break;
            case error.TIMEOUT:
              errorMessage = 'Location request timed out.';
              break;
          }
          setState(prev => ({
            ...prev,
            loading: false,
            error: errorMessage,
          }));
          resolve(null);
        },
        {
          enableHighAccuracy: false,
          timeout: 10000,
          maximumAge: 300000, // 5 minutes cache
        }
      );
    });
  }, []);

  const getLocation = useCallback(async () => {
    if (Platform.OS === 'web') {
      return requestLocationWeb();
    }
    return requestLocation();
  }, [requestLocation, requestLocationWeb]);

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  return {
    ...state,
    getLocation,
    clearError,
  };
};

// Utility function to format distance
export const formatDistance = (miles: number, km: number): string => {
  return `${miles} mi / ${km} km`;
};

export const formatDistanceShort = (miles: number): string => {
  if (miles < 1) {
    return `${Math.round(miles * 5280)} ft`;
  }
  return `${miles} mi`;
};
