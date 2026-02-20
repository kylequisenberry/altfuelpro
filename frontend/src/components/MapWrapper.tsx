import React, { useEffect, useRef, useState } from 'react';
import { View, Text, StyleSheet, Platform, TouchableOpacity, Linking } from 'react-native';
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

// Convert latitudeDelta to zoom level for Leaflet
const calculateZoom = (latitudeDelta: number): number => {
  const zoom = Math.round(Math.log2(360 / latitudeDelta));
  return Math.min(Math.max(zoom, 1), 18);
};

// Global map state for web
let webMapInstance: any = null;
let webMapMarkers: MarkerWrapperProps[] = [];

// Web Map initialization
const initWebMap = (
  containerRef: any,
  displayRegion: any,
  scrollEnabled: boolean,
  zoomEnabled: boolean,
  onRegionChangeComplete?: (region: any) => void
) => {
  if (typeof window === 'undefined' || !(window as any).L || !containerRef) return null;
  
  const L = (window as any).L;
  const zoom = calculateZoom(displayRegion.latitudeDelta);
  
  const map = L.map(containerRef, {
    center: [displayRegion.latitude, displayRegion.longitude],
    zoom: zoom,
    scrollWheelZoom: zoomEnabled,
    dragging: scrollEnabled,
    zoomControl: zoomEnabled,
  });

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
  }).addTo(map);

  if (onRegionChangeComplete) {
    map.on('moveend', () => {
      const center = map.getCenter();
      const bounds = map.getBounds();
      onRegionChangeComplete({
        latitude: center.lat,
        longitude: center.lng,
        latitudeDelta: bounds.getNorth() - bounds.getSouth(),
        longitudeDelta: bounds.getEast() - bounds.getWest(),
      });
    });
  }

  return map;
};

// Add marker to web map
const addWebMarker = (L: any, map: any, props: MarkerWrapperProps) => {
  if (!L || !map) return null;
  
  const { coordinate, title, description, pinColor = '#2E7D32', onCalloutPress } = props;
  
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

  const marker = L.marker([coordinate.latitude, coordinate.longitude], { icon }).addTo(map);

  if (title || description) {
    marker.bindPopup(`
      <div style="min-width: 150px;">
        ${title ? `<strong>${title}</strong>` : ''}
        ${description ? `<p style="margin: 4px 0 0 0; font-size: 12px;">${description}</p>` : ''}
      </div>
    `);
  }

  if (onCalloutPress) {
    marker.on('click', () => marker.openPopup());
  }

  return marker;
};

// MapView Component
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
  const mapContainerRef = useRef<any>(null);
  const mapInitialized = useRef(false);
  const [leafletLoaded, setLeafletLoaded] = useState(false);
  
  const displayRegion = region || initialRegion || {
    latitude: 39.8283,
    longitude: -98.5795,
    latitudeDelta: 30,
    longitudeDelta: 30,
  };

  // WEB: Use Leaflet
  useEffect(() => {
    if (Platform.OS !== 'web') return;
    
    const loadLeaflet = () => {
      if (typeof window !== 'undefined' && (window as any).L) {
        setLeafletLoaded(true);
        return;
      }

      const script = document.createElement('script');
      script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
      script.async = true;
      script.onload = () => setLeafletLoaded(true);
      document.head.appendChild(script);
    };

    const timeout = setTimeout(loadLeaflet, 100);
    return () => clearTimeout(timeout);
  }, []);

  useEffect(() => {
    if (!leafletLoaded || !mapContainerRef.current || mapInitialized.current) return;
    if (Platform.OS !== 'web' || typeof window === 'undefined') return;

    try {
      webMapInstance = initWebMap(
        mapContainerRef.current,
        displayRegion,
        scrollEnabled,
        zoomEnabled,
        onRegionChangeComplete
      );
      
      if (webMapInstance) {
        mapInitialized.current = true;
        webMapMarkers.forEach(m => addWebMarker((window as any).L, webMapInstance, m));
      }
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
  }, [leafletLoaded]);

  useEffect(() => {
    if (webMapInstance && region && mapInitialized.current) {
      webMapInstance.setView([region.latitude, region.longitude], calculateZoom(region.latitudeDelta));
    }
  }, [region?.latitude, region?.longitude, region?.latitudeDelta]);

  // WEB: Loading state
  if (Platform.OS === 'web' && !leafletLoaded) {
    return (
      <View style={[styles.fallbackContainer, style]}>
        <View style={styles.fallbackContent}>
          <Ionicons name="map" size={48} color={COLORS.primary} />
          <Text style={styles.fallbackText}>Loading Map...</Text>
        </View>
      </View>
    );
  }

  // WEB: Leaflet map container
  if (Platform.OS === 'web') {
    return (
      <View style={[styles.container, style]}>
        <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />
        {children}
      </View>
    );
  }

  // NATIVE (iOS/Android): Show fallback with option to open in external maps app
  const openInMaps = () => {
    const lat = displayRegion.latitude;
    const lng = displayRegion.longitude;
    const url = Platform.OS === 'ios'
      ? `maps://app?daddr=${lat},${lng}`
      : `geo:${lat},${lng}?q=${lat},${lng}`;
    
    Linking.canOpenURL(url).then(supported => {
      if (supported) {
        Linking.openURL(url);
      } else {
        // Fallback to Google Maps web
        Linking.openURL(`https://www.google.com/maps/@${lat},${lng},10z`);
      }
    });
  };

  return (
    <View style={[styles.fallbackContainer, style]}>
      <View style={styles.fallbackContent}>
        <Ionicons name="map" size={56} color={COLORS.primary} />
        <Text style={styles.fallbackText}>Map View</Text>
        <Text style={styles.fallbackCoords}>
          {displayRegion.latitude.toFixed(4)}, {displayRegion.longitude.toFixed(4)}
        </Text>
        <Text style={styles.fallbackNote}>
          Use the List view to browse stations,{'\n'}or open in your device's Maps app
        </Text>
        <TouchableOpacity style={styles.openMapsButton} onPress={openInMaps}>
          <Ionicons name="navigate" size={18} color="#FFFFFF" />
          <Text style={styles.openMapsText}>Open in Maps App</Text>
        </TouchableOpacity>
      </View>
      {children}
    </View>
  );
};

// Marker Component
export const MarkerComponent: React.FC<MarkerWrapperProps> = (props) => {
  const markerRef = useRef<any>(null);

  // WEB: Add to Leaflet map
  useEffect(() => {
    if (Platform.OS !== 'web') return;
    
    webMapMarkers.push(props);
    
    if (webMapInstance && typeof window !== 'undefined' && (window as any).L) {
      markerRef.current = addWebMarker((window as any).L, webMapInstance, props);
    }

    return () => {
      if (markerRef.current && webMapInstance) {
        webMapInstance.removeLayer(markerRef.current);
      }
      webMapMarkers = webMapMarkers.filter(m => m !== props);
    };
  }, [props.coordinate.latitude, props.coordinate.longitude, props.title, props.description]);

  // On native, markers don't render anything (handled by fallback)
  return null;
};

// Circle Component
export const CircleComponent: React.FC<CircleWrapperProps> = ({
  center,
  radius,
  fillColor = 'rgba(46, 125, 50, 0.2)',
  strokeColor = '#2E7D32',
  strokeWidth = 2,
}) => {
  useEffect(() => {
    if (Platform.OS !== 'web' || !webMapInstance || typeof window === 'undefined') return;
    
    const L = (window as any).L;
    if (!L) return;
    
    const circle = L.circle([center.latitude, center.longitude], {
      radius,
      fillColor,
      color: strokeColor,
      weight: strokeWidth,
    }).addTo(webMapInstance);

    return () => {
      if (webMapInstance) webMapInstance.removeLayer(circle);
    };
  }, [center.latitude, center.longitude, radius]);

  return null;
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    overflow: 'hidden',
  },
  fallbackContainer: {
    backgroundColor: '#E8F5E9',
    justifyContent: 'center',
    alignItems: 'center',
    flex: 1,
  },
  fallbackContent: {
    alignItems: 'center',
    padding: 20,
  },
  fallbackText: {
    fontSize: 20,
    fontWeight: '600',
    color: COLORS.primary,
    marginTop: 12,
  },
  fallbackCoords: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginTop: 4,
  },
  fallbackNote: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginTop: 16,
    textAlign: 'center',
    lineHeight: 20,
  },
  openMapsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary,
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 20,
    gap: 8,
  },
  openMapsText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});
