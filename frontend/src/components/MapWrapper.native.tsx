import React from 'react';
import MapView, { Marker, Circle, PROVIDER_GOOGLE } from 'react-native-maps';
import { Platform } from 'react-native';

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
  children?: React.ReactNode;
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

// Native MapView component using react-native-maps
export const MapViewComponent: React.FC<MapWrapperProps> = ({
  style,
  region,
  initialRegion,
  onRegionChangeComplete,
  showsUserLocation = false,
  showsMyLocationButton = false,
  scrollEnabled = true,
  zoomEnabled = true,
  children,
}) => {
  return (
    <MapView
      style={style}
      provider={Platform.OS === 'android' ? PROVIDER_GOOGLE : undefined}
      region={region}
      initialRegion={initialRegion}
      onRegionChangeComplete={onRegionChangeComplete}
      showsUserLocation={showsUserLocation}
      showsMyLocationButton={showsMyLocationButton}
      scrollEnabled={scrollEnabled}
      zoomEnabled={zoomEnabled}
    >
      {children}
    </MapView>
  );
};

export const MarkerComponent: React.FC<MarkerWrapperProps> = ({
  coordinate,
  title,
  description,
  pinColor,
  onCalloutPress,
  children,
}) => {
  return (
    <Marker
      coordinate={coordinate}
      title={title}
      description={description}
      pinColor={pinColor}
      onCalloutPress={onCalloutPress}
    >
      {children}
    </Marker>
  );
};

export const CircleComponent: React.FC<CircleWrapperProps> = ({
  center,
  radius,
  fillColor,
  strokeColor,
  strokeWidth,
}) => {
  return (
    <Circle
      center={center}
      radius={radius}
      fillColor={fillColor}
      strokeColor={strokeColor}
      strokeWidth={strokeWidth}
    />
  );
};
