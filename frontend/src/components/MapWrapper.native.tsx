import React from 'react';
import MapView, { Marker, Circle, PROVIDER_DEFAULT } from 'react-native-maps';

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

export const MapViewComponent: React.FC<MapWrapperProps> = (props) => {
  return <MapView provider={PROVIDER_DEFAULT} {...props} />;
};

export const MarkerComponent: React.FC<MarkerWrapperProps> = (props) => {
  return <Marker {...props} />;
};

export const CircleComponent: React.FC<CircleWrapperProps> = (props) => {
  return <Circle {...props} />;
};
