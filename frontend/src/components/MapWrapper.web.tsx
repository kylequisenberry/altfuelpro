import React, { useEffect, useRef } from 'react';
import { View, StyleSheet } from 'react-native';
import { MapContainer, TileLayer, Marker, Circle, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icons in Leaflet with webpack/bundlers
const DefaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

L.Marker.prototype.options.icon = DefaultIcon;

// Custom colored marker icons
const createColoredIcon = (color: string) => {
  const svgIcon = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 36" width="24" height="36">
      <path fill="${color}" stroke="#fff" stroke-width="1" d="M12 0C5.4 0 0 5.4 0 12c0 7.2 12 24 12 24s12-16.8 12-24c0-6.6-5.4-12-12-12z"/>
      <circle fill="#fff" cx="12" cy="12" r="5"/>
    </svg>
  `;
  return L.divIcon({
    html: svgIcon,
    className: 'custom-marker',
    iconSize: [24, 36],
    iconAnchor: [12, 36],
    popupAnchor: [0, -36],
  });
};

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

// Component to handle map region changes
const MapController: React.FC<{
  region?: MapWrapperProps['region'];
  onRegionChangeComplete?: MapWrapperProps['onRegionChangeComplete'];
}> = ({ region, onRegionChangeComplete }) => {
  const map = useMap();

  useEffect(() => {
    if (region) {
      map.setView([region.latitude, region.longitude], calculateZoom(region.latitudeDelta));
    }
  }, [region, map]);

  useEffect(() => {
    if (onRegionChangeComplete) {
      const handleMoveEnd = () => {
        const center = map.getCenter();
        const bounds = map.getBounds();
        const latDelta = bounds.getNorth() - bounds.getSouth();
        const lngDelta = bounds.getEast() - bounds.getWest();
        
        onRegionChangeComplete({
          latitude: center.lat,
          longitude: center.lng,
          latitudeDelta: latDelta,
          longitudeDelta: lngDelta,
        });
      };

      map.on('moveend', handleMoveEnd);
      return () => {
        map.off('moveend', handleMoveEnd);
      };
    }
  }, [map, onRegionChangeComplete]);

  return null;
};

// Convert latitudeDelta to zoom level
const calculateZoom = (latitudeDelta: number): number => {
  // Approximate conversion from latitudeDelta to Leaflet zoom level
  const zoom = Math.round(Math.log2(360 / latitudeDelta));
  return Math.min(Math.max(zoom, 1), 18);
};

// Web MapView component using Leaflet
export const MapViewComponent: React.FC<MapWrapperProps> = ({
  style,
  region,
  initialRegion,
  onRegionChangeComplete,
  scrollEnabled = true,
  zoomEnabled = true,
  children,
}) => {
  const displayRegion = region || initialRegion || {
    latitude: 39.8283,
    longitude: -98.5795,
    latitudeDelta: 30,
    longitudeDelta: 30,
  };

  const zoom = calculateZoom(displayRegion.latitudeDelta);

  return (
    <View style={[styles.container, style]}>
      <MapContainer
        center={[displayRegion.latitude, displayRegion.longitude]}
        zoom={zoom}
        style={{ width: '100%', height: '100%' }}
        scrollWheelZoom={zoomEnabled}
        dragging={scrollEnabled}
        zoomControl={zoomEnabled}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapController region={region} onRegionChangeComplete={onRegionChangeComplete} />
        {children}
      </MapContainer>
    </View>
  );
};

// Leaflet Marker component
export const MarkerComponent: React.FC<MarkerWrapperProps> = ({
  coordinate,
  title,
  description,
  pinColor = '#2E7D32',
  onCalloutPress,
  children,
}) => {
  const icon = createColoredIcon(pinColor);

  return (
    <Marker 
      position={[coordinate.latitude, coordinate.longitude]} 
      icon={icon}
      eventHandlers={{
        click: () => {
          if (onCalloutPress) {
            onCalloutPress();
          }
        },
      }}
    >
      {(title || description) && (
        <Popup>
          <div onClick={onCalloutPress} style={{ cursor: onCalloutPress ? 'pointer' : 'default' }}>
            {title && <strong>{title}</strong>}
            {description && <p style={{ margin: '4px 0 0 0', fontSize: '12px' }}>{description}</p>}
          </div>
        </Popup>
      )}
      {children}
    </Marker>
  );
};

// Leaflet Circle component
export const CircleComponent: React.FC<CircleWrapperProps> = ({
  center,
  radius,
  fillColor = 'rgba(46, 125, 50, 0.2)',
  strokeColor = '#2E7D32',
  strokeWidth = 2,
}) => {
  return (
    <Circle
      center={[center.latitude, center.longitude]}
      radius={radius}
      pathOptions={{
        fillColor,
        color: strokeColor,
        weight: strokeWidth,
      }}
    />
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    overflow: 'hidden',
  },
});
