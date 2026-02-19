import React from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../constants';

interface MapWrapperProps {
  style?: any;
  region?: {
    latitude: number;
    longitude: number;
    latitudeDelta: number;
    longitudeDelta: number;
  };
  initialRegion?: {
    latitude: number;
    longitude: number;
    latitudeDelta: number;
    longitudeDelta: number;
  };
  onRegionChangeComplete?: (region: any) => void;
  showsUserLocation?: boolean;
  showsMyLocationButton?: boolean;
  scrollEnabled?: boolean;
  zoomEnabled?: boolean;
  children?: React.ReactNode;
}

interface MarkerWrapperProps {
  coordinate: {
    latitude: number;
    longitude: number;
  };
  title?: string;
  description?: string;
  pinColor?: string;
  onCalloutPress?: () => void;
}

interface CircleWrapperProps {
  center: {
    latitude: number;
    longitude: number;
  };
  radius: number;
  fillColor?: string;
  strokeColor?: string;
  strokeWidth?: number;
}

// Web fallback component
const WebMapFallback: React.FC<MapWrapperProps> = ({ style, initialRegion, region }) => {
  const displayRegion = region || initialRegion;
  return (
    <View style={[styles.webMapContainer, style]}>
      <View style={styles.webMapContent}>
        <Ionicons name="map" size={48} color={COLORS.primary} />
        <Text style={styles.webMapText}>Map View</Text>
        {displayRegion && (
          <Text style={styles.webMapCoords}>
            {displayRegion.latitude.toFixed(4)}, {displayRegion.longitude.toFixed(4)}
          </Text>
        )}
        <Text style={styles.webMapNote}>Open in Expo Go for full map experience</Text>
      </View>
    </View>
  );
};

// Export platform-specific components
export const MapViewComponent: React.FC<MapWrapperProps> = (props) => {
  // Always show web fallback on web platform
  if (Platform.OS === 'web') {
    return <WebMapFallback {...props} />;
  }
  
  // On native, dynamically require react-native-maps
  try {
    const MapView = require('react-native-maps').default;
    const PROVIDER_DEFAULT = require('react-native-maps').PROVIDER_DEFAULT;
    return <MapView provider={PROVIDER_DEFAULT} {...props} />;
  } catch (e) {
    return <WebMapFallback {...props} />;
  }
};

export const MarkerComponent: React.FC<MarkerWrapperProps> = (props) => {
  if (Platform.OS === 'web') {
    return null;
  }
  
  try {
    const { Marker } = require('react-native-maps');
    return <Marker {...props} />;
  } catch (e) {
    return null;
  }
};

export const CircleComponent: React.FC<CircleWrapperProps> = (props) => {
  if (Platform.OS === 'web') {
    return null;
  }
  
  try {
    const { Circle } = require('react-native-maps');
    return <Circle {...props} />;
  } catch (e) {
    return null;
  }
};

const styles = StyleSheet.create({
  webMapContainer: {
    backgroundColor: '#E8F5E9',
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  webMapContent: {
    alignItems: 'center',
  },
  webMapText: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.primary,
    marginTop: 8,
  },
  webMapCoords: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 4,
  },
  webMapNote: {
    fontSize: 11,
    color: COLORS.textLight,
    marginTop: 8,
    fontStyle: 'italic',
  },
});
