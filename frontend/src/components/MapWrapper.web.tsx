import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Platform } from 'react-native';

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

// Convert latitudeDelta to zoom level
const calculateZoom = (latitudeDelta: number): number => {
  const zoom = Math.round(Math.log2(360 / latitudeDelta));
  return Math.min(Math.max(zoom, 1), 18);
};

// Store markers for the map
let mapMarkers: MarkerWrapperProps[] = [];
let mapInstance: any = null;

// Web MapView component using Leaflet via CDN (loaded in +html.tsx)
export const MapViewComponent: React.FC<MapWrapperProps> = ({
  style,
  region,
  initialRegion,
  onRegionChangeComplete,
  scrollEnabled = true,
  zoomEnabled = true,
  children,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  
  const displayRegion = region || initialRegion || {
    latitude: 39.8283,
    longitude: -98.5795,
    latitudeDelta: 30,
    longitudeDelta: 30,
  };

  useEffect(() => {
    // Wait for Leaflet to be loaded from CDN
    const initMap = () => {
      if (typeof window !== 'undefined' && (window as any).L && mapContainerRef.current && !mapRef.current) {
        const L = (window as any).L;
        
        const zoom = calculateZoom(displayRegion.latitudeDelta);
        
        // Initialize map
        mapRef.current = L.map(mapContainerRef.current, {
          center: [displayRegion.latitude, displayRegion.longitude],
          zoom: zoom,
          scrollWheelZoom: zoomEnabled,
          dragging: scrollEnabled,
          zoomControl: zoomEnabled,
        });
        
        mapInstance = mapRef.current;

        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(mapRef.current);

        // Handle region changes
        if (onRegionChangeComplete) {
          mapRef.current.on('moveend', () => {
            const center = mapRef.current.getCenter();
            const bounds = mapRef.current.getBounds();
            const latDelta = bounds.getNorth() - bounds.getSouth();
            const lngDelta = bounds.getEast() - bounds.getWest();
            
            onRegionChangeComplete({
              latitude: center.lat,
              longitude: center.lng,
              latitudeDelta: latDelta,
              longitudeDelta: lngDelta,
            });
          });
        }

        // Add any pending markers
        mapMarkers.forEach(marker => {
          addMarkerToMap(L, mapRef.current, marker);
        });
      }
    };

    // Check if Leaflet is already loaded
    if ((window as any).L) {
      initMap();
    } else {
      // Wait for Leaflet to load
      const checkLeaflet = setInterval(() => {
        if ((window as any).L) {
          clearInterval(checkLeaflet);
          initMap();
        }
      }, 100);
      
      // Cleanup interval after 10 seconds
      setTimeout(() => clearInterval(checkLeaflet), 10000);
    }

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
        mapInstance = null;
      }
    };
  }, []);

  // Update map view when region changes
  useEffect(() => {
    if (mapRef.current && region) {
      const zoom = calculateZoom(region.latitudeDelta);
      mapRef.current.setView([region.latitude, region.longitude], zoom);
    }
  }, [region]);

  return (
    <View style={[styles.container, style]}>
      <div 
        ref={mapContainerRef} 
        style={{ width: '100%', height: '100%' }}
      />
    </View>
  );
};

// Helper to add marker to map
const addMarkerToMap = (L: any, map: any, props: MarkerWrapperProps) => {
  const { coordinate, title, description, pinColor = '#2E7D32', onCalloutPress } = props;
  
  // Create custom icon
  const iconHtml = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 36" width="24" height="36">
      <path fill="${pinColor}" stroke="#fff" stroke-width="1" d="M12 0C5.4 0 0 5.4 0 12c0 7.2 12 24 12 24s12-16.8 12-24c0-6.6-5.4-12-12-12z"/>
      <circle fill="#fff" cx="12" cy="12" r="5"/>
    </svg>
  `;
  
  const icon = L.divIcon({
    html: iconHtml,
    className: 'custom-marker',
    iconSize: [24, 36],
    iconAnchor: [12, 36],
    popupAnchor: [0, -36],
  });

  const marker = L.marker([coordinate.latitude, coordinate.longitude], { icon })
    .addTo(map);

  if (title || description) {
    const popupContent = `
      <div style="cursor: pointer;">
        ${title ? `<strong>${title}</strong>` : ''}
        ${description ? `<p style="margin: 4px 0 0 0; font-size: 12px;">${description}</p>` : ''}
      </div>
    `;
    marker.bindPopup(popupContent);
  }

  if (onCalloutPress) {
    marker.on('click', onCalloutPress);
  }
};

// Leaflet Marker component
export const MarkerComponent: React.FC<MarkerWrapperProps> = (props) => {
  useEffect(() => {
    mapMarkers.push(props);
    
    // If map is already initialized, add marker directly
    if (mapInstance && (window as any).L) {
      addMarkerToMap((window as any).L, mapInstance, props);
    }

    return () => {
      mapMarkers = mapMarkers.filter(m => m !== props);
    };
  }, [props.coordinate.latitude, props.coordinate.longitude]);

  return null;
};

// Leaflet Circle component
export const CircleComponent: React.FC<CircleWrapperProps> = ({
  center,
  radius,
  fillColor = 'rgba(46, 125, 50, 0.2)',
  strokeColor = '#2E7D32',
  strokeWidth = 2,
}) => {
  useEffect(() => {
    if (mapInstance && (window as any).L) {
      const L = (window as any).L;
      L.circle([center.latitude, center.longitude], {
        radius,
        fillColor,
        color: strokeColor,
        weight: strokeWidth,
      }).addTo(mapInstance);
    }
  }, [center, radius]);

  return null;
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    overflow: 'hidden',
  },
});
