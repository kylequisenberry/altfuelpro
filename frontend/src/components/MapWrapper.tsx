import React from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../constants';

// Platform-specific map components
let MapView: any = null;
let Marker: any = null;
let Circle: any = null;
let PROVIDER_DEFAULT: any = null;

// Only import react-native-maps on native platforms
if (Platform.OS !== 'web') {
  try {
    const Maps = require('react-native-maps');
    MapView = Maps.default;
    Marker = Maps.Marker;
    Circle = Maps.Circle;
    PROVIDER_DEFAULT = Maps.PROVIDER_DEFAULT;
  } catch (e) {
    console.log('react-native-maps not available');
  }
}

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
const WebMapFallback: React.FC<MapWrapperProps> = ({ style, children, initialRegion, region }) => {
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
        <Text style={styles.webMapNote}>Open in Expo Go for full map</Text>
      </View>
      {children}
    </View>
  );
};

const WebMarkerFallback: React.FC<MarkerWrapperProps> = () => null;
const WebCircleFallback: React.FC<CircleWrapperProps> = () => null;

// Export platform-specific components
export const MapViewComponent: React.FC<MapWrapperProps> = (props) => {
  if (Platform.OS === 'web' || !MapView) {
    return <WebMapFallback {...props} />;
  }
  return <MapView provider={PROVIDER_DEFAULT} {...props} />;
};

export const MarkerComponent: React.FC<MarkerWrapperProps> = (props) => {
  if (Platform.OS === 'web' || !Marker) {
    return <WebMarkerFallback {...props} />;
  }
  return <Marker {...props} />;
};

export const CircleComponent: React.FC<CircleWrapperProps> = (props) => {
  if (Platform.OS === 'web' || !Circle) {
    return <WebCircleFallback {...props} />;
  }
  return <Circle {...props} />;
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
