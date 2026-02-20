import React, { useEffect, useRef, useState } from 'react';
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

// Global map state for web
let webMapInstance: any = null;
let webMapMarkers: any[] = [];

// Web MapView component using Leaflet loaded from CDN
export const MapViewComponent: React.FC<MapWrapperProps> = ({
  style,
  region,
  initialRegion,
  onRegionChangeComplete,
  scrollEnabled = true,
  zoomEnabled = true,
  children,
}) => {
  const mapContainerRef = useRef<any>(null);
  const mapInitialized = useRef(false);
  const [leafletLoaded, setLeafletLoaded] = useState(false);
  
  const displayRegion = region || initialRegion || {
    latitude: 39.8283,
    longitude: -98.5795,
    latitudeDelta: 30,
    longitudeDelta: 30,
  };

  // Load Leaflet JS from CDN if not already loaded
  useEffect(() => {
    if (Platform.OS !== 'web') return;
    
    const loadLeaflet = () => {
      // Check if Leaflet is already loaded
      if (typeof window !== 'undefined' && (window as any).L) {
        setLeafletLoaded(true);
        return;
      }

      // Load Leaflet script
      const script = document.createElement('script');
      script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
      script.async = true;
      script.onload = () => {
        setLeafletLoaded(true);
      };
      document.head.appendChild(script);
    };

    // Use setTimeout to ensure we're on the client
    const timeout = setTimeout(loadLeaflet, 100);
    return () => clearTimeout(timeout);
  }, []);

  // Initialize map when Leaflet is loaded
  useEffect(() => {
    if (!leafletLoaded || !mapContainerRef.current || mapInitialized.current) return;
    if (Platform.OS !== 'web') return;
    if (typeof window === 'undefined') return;

    const L = (window as any).L;
    if (!L) return;

    try {
      const zoom = calculateZoom(displayRegion.latitudeDelta);
      
      // Initialize map
      webMapInstance = L.map(mapContainerRef.current, {
        center: [displayRegion.latitude, displayRegion.longitude],
        zoom: zoom,
        scrollWheelZoom: zoomEnabled,
        dragging: scrollEnabled,
        zoomControl: zoomEnabled,
      });

      // Add OpenStreetMap tiles
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
      }).addTo(webMapInstance);

      // Handle region changes
      if (onRegionChangeComplete) {
        webMapInstance.on('moveend', () => {
          const center = webMapInstance.getCenter();
          const bounds = webMapInstance.getBounds();
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

      mapInitialized.current = true;

      // Add any pending markers
      webMapMarkers.forEach(marker => {
        addMarkerToMap(L, webMapInstance, marker);
      });
    } catch (e) {
      console.error('Error initializing map:', e);
    }

    return () => {
      if (webMapInstance) {
        webMapInstance.remove();
        webMapInstance = null;
        mapInitialized.current = false;
      }
    };
  }, [leafletLoaded, displayRegion.latitude, displayRegion.longitude]);

  // Update map view when region changes
  useEffect(() => {
    if (webMapInstance && region && mapInitialized.current) {
      const zoom = calculateZoom(region.latitudeDelta);
      webMapInstance.setView([region.latitude, region.longitude], zoom);
    }
  }, [region?.latitude, region?.longitude, region?.latitudeDelta]);

  // Fallback for SSR or if Leaflet hasn't loaded
  if (Platform.OS !== 'web' || !leafletLoaded) {
    return (
      <View style={[styles.webMapContainer, style]}>
        <View style={styles.webMapContent}>
          <Ionicons name="map" size={48} color={COLORS.primary} />
          <Text style={styles.webMapText}>Loading Map...</Text>
          {displayRegion && (
            <Text style={styles.webMapCoords}>
              {displayRegion.latitude.toFixed(4)}, {displayRegion.longitude.toFixed(4)}
            </Text>
          )}
        </View>
      </View>
    );
  }

  return (
    <View style={[styles.container, style]}>
      <div 
        ref={mapContainerRef} 
        style={{ width: '100%', height: '100%' }}
      />
      {children}
    </View>
  );
};

// Helper to add marker to map
const addMarkerToMap = (L: any, map: any, props: MarkerWrapperProps) => {
  if (!L || !map) return;
  
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
    className: 'leaflet-custom-marker',
    iconSize: [24, 36],
    iconAnchor: [12, 36],
    popupAnchor: [0, -36],
  });

  const marker = L.marker([coordinate.latitude, coordinate.longitude], { icon })
    .addTo(map);

  if (title || description) {
    const popupContent = `
      <div style="cursor: pointer; min-width: 150px;">
        ${title ? `<strong style="font-size: 14px;">${title}</strong>` : ''}
        ${description ? `<p style="margin: 4px 0 0 0; font-size: 12px; color: #666;">${description}</p>` : ''}
      </div>
    `;
    marker.bindPopup(popupContent);
  }

  if (onCalloutPress) {
    marker.on('click', () => {
      marker.openPopup();
    });
    marker.on('popupopen', () => {
      const popup = marker.getPopup();
      if (popup) {
        const container = popup.getElement();
        if (container) {
          container.addEventListener('click', onCalloutPress);
        }
      }
    });
  }

  return marker;
};

// Leaflet Marker component
export const MarkerComponent: React.FC<MarkerWrapperProps> = (props) => {
  const markerRef = useRef<any>(null);

  useEffect(() => {
    if (Platform.OS !== 'web') return;
    
    // Store marker data
    webMapMarkers.push(props);
    
    // If map is already initialized, add marker directly
    if (webMapInstance && typeof window !== 'undefined' && (window as any).L) {
      markerRef.current = addMarkerToMap((window as any).L, webMapInstance, props);
    }

    return () => {
      // Remove marker from map
      if (markerRef.current && webMapInstance) {
        webMapInstance.removeLayer(markerRef.current);
      }
      // Remove from pending markers
      webMapMarkers = webMapMarkers.filter(m => m !== props);
    };
  }, [props.coordinate.latitude, props.coordinate.longitude, props.title, props.description]);

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
    if (Platform.OS !== 'web') return;
    if (!webMapInstance || typeof window === 'undefined') return;
    
    const L = (window as any).L;
    if (!L) return;
    
    const circle = L.circle([center.latitude, center.longitude], {
      radius,
      fillColor,
      color: strokeColor,
      weight: strokeWidth,
    }).addTo(webMapInstance);

    return () => {
      if (webMapInstance) {
        webMapInstance.removeLayer(circle);
      }
    };
  }, [center.latitude, center.longitude, radius]);

  return null;
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    overflow: 'hidden',
  },
  webMapContainer: {
    backgroundColor: '#E8F5E9',
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
    flex: 1,
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
});
