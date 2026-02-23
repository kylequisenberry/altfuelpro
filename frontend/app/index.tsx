import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  RefreshControl,
  Dimensions,
  Platform,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { MapViewComponent, MarkerComponent } from '../src/components/MapWrapper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { getStations } from '../src/services/api';
import { FuelStation } from '../src/types';
import { StationCard } from '../src/components/StationCard';
import { StationsFilterModal, StationFilters } from '../src/components/StationsFilterModal';
import { LoadingSpinner } from '../src/components/LoadingSpinner';
import { useLocation } from '../src/hooks/useLocation';
import { COLORS, FUEL_TYPE_COLORS } from '../src/constants';

const { width } = Dimensions.get('window');

// Type for station with optional distance
type FuelStationDisplay = FuelStation & {
  distance_miles?: number;
  distance_km?: number;
};

// Haversine distance calculation (client-side)
const calculateDistance = (lat1: number, lon1: number, lat2: number, lon2: number): { miles: number; km: number } => {
  const R = 3959; // Earth's radius in miles
  const lat1Rad = (lat1 * Math.PI) / 180;
  const lat2Rad = (lat2 * Math.PI) / 180;
  const deltaLat = ((lat2 - lat1) * Math.PI) / 180;
  const deltaLon = ((lon2 - lon1) * Math.PI) / 180;
  
  const a = Math.sin(deltaLat / 2) ** 2 + Math.cos(lat1Rad) * Math.cos(lat2Rad) * Math.sin(deltaLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  
  const miles = R * c;
  return { miles: Math.round(miles * 10) / 10, km: Math.round(miles * 1.60934 * 10) / 10 };
};

export default function StationsScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const [stations, setStations] = useState<FuelStationDisplay[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [viewMode, setViewMode] = useState<'map' | 'list'>('map');
  const [filterModalVisible, setFilterModalVisible] = useState(false);
  const [nearbyMode, setNearbyMode] = useState(false);
  const [locationLoading, setLocationLoading] = useState(false);
  const [userLocation, setUserLocation] = useState<{ latitude: number; longitude: number } | null>(null);
  const [filters, setFilters] = useState<StationFilters>({
    city: '',
    state: '',
    zipCode: '',
    radius: undefined,
    fuelTypes: [],
  });
  const [mapRegion, setMapRegion] = useState({
    latitude: 37.0902,
    longitude: -95.7129,
    latitudeDelta: 40,
    longitudeDelta: 40,
  });

  const { getLocation, clearError } = useLocation();

  const findNearbyStations = useCallback(async () => {
    setLocationLoading(true);
    clearError();
    
    try {
      const location = await getLocation();
      if (!location) {
        Alert.alert(
          'Location Required',
          'Please enable location access to find nearby stations.',
          [{ text: 'OK' }]
        );
        setLocationLoading(false);
        return;
      }

      setUserLocation(location);

      // Fetch stations using the AFDC API with location parameters
      const apiFilters: any = {
        latitude: location.latitude,
        longitude: location.longitude,
        radius: 25, // 25 miles radius
      };
      
      if (filters.fuelTypes.length === 1) {
        apiFilters.fuel_type = filters.fuelTypes[0];
      }

      const data = await getStations(apiFilters);
      
      // Calculate distances for each station
      const stationsWithDistance = data.map((station) => {
        const dist = calculateDistance(
          location.latitude,
          location.longitude,
          station.latitude,
          station.longitude
        );
        return {
          ...station,
          distance_miles: dist.miles,
          distance_km: dist.km,
        };
      });

      // Sort by distance
      stationsWithDistance.sort((a, b) => (a.distance_miles || 0) - (b.distance_miles || 0));

      setStations(stationsWithDistance);
      setNearbyMode(true);
      
      // Center map on user location
      setMapRegion({
        latitude: location.latitude,
        longitude: location.longitude,
        latitudeDelta: 0.5,
        longitudeDelta: 0.5,
      });
    } catch (error) {
      console.error('Error finding nearby stations:', error);
      Alert.alert('Error', 'Failed to find nearby stations. Please try again.');
    } finally {
      setLocationLoading(false);
      setLoading(false);
    }
  }, [getLocation, clearError, filters.fuelTypes]);

  const handleShowAll = () => {
    setNearbyMode(false);
    setUserLocation(null);
    setLoading(true);
    fetchStations();
  };

  const fetchStations = useCallback(async () => {
    try {
      const apiFilters: any = {};
      
      if (filters.fuelTypes.length === 1) {
        apiFilters.fuel_type = filters.fuelTypes[0];
      }
      if (filters.state) {
        apiFilters.state = filters.state;
      }
      if (filters.city) {
        apiFilters.city = filters.city;
      }
      if (filters.zipCode) {
        apiFilters.zip_code = filters.zipCode;
      }
      if (filters.radius) {
        apiFilters.radius = filters.radius;
      }
      
      const data = await getStations(Object.keys(apiFilters).length > 0 ? apiFilters : undefined);
      setStations(data);
      
      // Center map on first station if available
      if (data.length > 0 && mapRegion.latitudeDelta > 30) {
        setMapRegion({
          latitude: data[0].latitude,
          longitude: data[0].longitude,
          latitudeDelta: 10,
          longitudeDelta: 10,
        });
      }
    } catch (error) {
      console.error('Error fetching stations:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchStations();
  }, [fetchStations]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchStations();
  };

  const handleApplyFilters = (newFilters: StationFilters) => {
    setFilters(newFilters);
    setNearbyMode(false);
    setUserLocation(null);
  };

  // Filter stations client-side for multiple fuel types
  const filteredStations = stations.filter((station) => {
    if (filters.fuelTypes.length > 1) {
      return station.fuel_types.some((type) => filters.fuelTypes.includes(type));
    }
    return true;
  });

  const navigateToStation = (id: string) => {
    router.push(`/station/${id}`);
  };

  const getMarkerColor = (fuelTypes: string[]) => {
    if (fuelTypes.length === 0) return COLORS.primary;
    return FUEL_TYPE_COLORS[fuelTypes[0]] || COLORS.primary;
  };

  const activeFilterCount = [
    filters.city,
    filters.state,
    filters.zipCode,
    filters.radius,
    filters.fuelTypes.length > 0
  ].filter(Boolean).length;

  if (loading) {
    return <LoadingSpinner message="Finding fuel stations..." />;
  }

  return (
    <View style={styles.container}>
      {/* Header Controls */}
      <View style={styles.headerControls}>
        {/* View Mode Toggle */}
        <View style={styles.viewToggle}>
          <TouchableOpacity
            style={[styles.toggleButton, viewMode === 'map' && styles.toggleButtonActive]}
            onPress={() => setViewMode('map')}
          >
            <Ionicons
              name="map"
              size={18}
              color={viewMode === 'map' ? '#FFFFFF' : COLORS.textSecondary}
            />
            <Text
              style={[styles.toggleText, viewMode === 'map' && styles.toggleTextActive]}
            >
              Map
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.toggleButton, viewMode === 'list' && styles.toggleButtonActive]}
            onPress={() => setViewMode('list')}
          >
            <Ionicons
              name="list"
              size={18}
              color={viewMode === 'list' ? '#FFFFFF' : COLORS.textSecondary}
            />
            <Text
              style={[styles.toggleText, viewMode === 'list' && styles.toggleTextActive]}
            >
              List
            </Text>
          </TouchableOpacity>
        </View>

        {/* Filter Button */}
        <TouchableOpacity
          style={styles.filterButton}
          onPress={() => setFilterModalVisible(true)}
        >
          <Ionicons name="options" size={18} color={COLORS.primary} />
          <Text style={styles.filterButtonText}>Filter</Text>
          {activeFilterCount > 0 && (
            <View style={styles.filterBadge}>
              <Text style={styles.filterBadgeText}>{activeFilterCount}</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      {/* Active Filters Display */}
      {activeFilterCount > 0 && (
        <View style={styles.activeFiltersBar}>
          <Text style={styles.activeFiltersText}>
            {filters.state && `${filters.state} `}
            {filters.city && `${filters.city} `}
            {filters.zipCode && `ZIP: ${filters.zipCode} `}
            {filters.radius && `within ${filters.radius} mi `}
            {filters.fuelTypes.length > 0 && `• ${filters.fuelTypes.join(', ')}`}
          </Text>
          <TouchableOpacity onPress={() => setFilters({
            city: '',
            state: '',
            zipCode: '',
            radius: undefined,
            fuelTypes: [],
          })}>
            <Ionicons name="close-circle" size={18} color={COLORS.textSecondary} />
          </TouchableOpacity>
        </View>
      )}

      {/* Map View */}
      {viewMode === 'map' && (
        <View style={styles.mapContainer}>
          <MapViewComponent
            style={styles.map}
            region={mapRegion}
            onRegionChangeComplete={setMapRegion}
            showsUserLocation
            showsMyLocationButton
            markers={filteredStations.map((station) => ({
              id: station.id,
              latitude: station.latitude,
              longitude: station.longitude,
              title: station.name,
              description: `${station.fuel_types.join(', ')} - ${station.status}`,
              pinColor: getMarkerColor(station.fuel_types),
            }))}
          >
            {/* Markers for web (children approach) */}
            {Platform.OS === 'web' && filteredStations.map((station) => (
              <MarkerComponent
                key={station.id}
                coordinate={{
                  latitude: station.latitude,
                  longitude: station.longitude,
                }}
                title={station.name}
                description={`${station.fuel_types.join(', ')} - ${station.status}`}
                pinColor={getMarkerColor(station.fuel_types)}
                onCalloutPress={() => navigateToStation(station.id)}
              />
            ))}
          </MapViewComponent>
          
          {/* Station Count Badge */}
          <View style={styles.countBadge}>
            <Text style={styles.countText}>
              {filteredStations.length} station{filteredStations.length !== 1 ? 's' : ''}
            </Text>
          </View>
        </View>
      )}

      {/* List View */}
      {viewMode === 'list' && (
        <FlatList
          data={filteredStations}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <StationCard
              station={item}
              onPress={() => navigateToStation(item.id)}
            />
          )}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor={COLORS.primary}
            />
          }
          ListHeaderComponent={
            <View style={styles.listHeader}>
              <Text style={styles.listHeaderText}>
                {filteredStations.length} station{filteredStations.length !== 1 ? 's' : ''} found
              </Text>
            </View>
          }
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <Ionicons name="location-outline" size={48} color={COLORS.textLight} />
              <Text style={styles.emptyText}>No stations found</Text>
              <Text style={styles.emptySubtext}>Try adjusting your filters</Text>
            </View>
          }
        />
      )}

      {/* Filter Modal */}
      <StationsFilterModal
        visible={filterModalVisible}
        onClose={() => setFilterModalVisible(false)}
        filters={filters}
        onApplyFilters={handleApplyFilters}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  headerControls: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.divider,
  },
  viewToggle: {
    flexDirection: 'row',
    backgroundColor: COLORS.background,
    borderRadius: 8,
    padding: 3,
  },
  toggleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 6,
    gap: 4,
  },
  toggleButtonActive: {
    backgroundColor: COLORS.primary,
  },
  toggleText: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.textSecondary,
  },
  toggleTextActive: {
    color: '#FFFFFF',
  },
  filterButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 8,
    backgroundColor: COLORS.background,
    borderWidth: 1,
    borderColor: COLORS.border,
    gap: 6,
  },
  filterButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.primary,
  },
  filterBadge: {
    backgroundColor: COLORS.primary,
    borderRadius: 10,
    minWidth: 18,
    height: 18,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 2,
  },
  filterBadgeText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '600',
  },
  activeFiltersBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.primary + '10',
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  activeFiltersText: {
    flex: 1,
    fontSize: 12,
    color: COLORS.primary,
    fontWeight: '500',
  },
  mapContainer: {
    flex: 1,
  },
  map: {
    flex: 1,
  },
  countBadge: {
    position: 'absolute',
    top: 12,
    left: 12,
    backgroundColor: COLORS.surface,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  countText: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.text,
  },
  listContent: {
    padding: 12,
  },
  listHeader: {
    marginBottom: 8,
  },
  listHeaderText: {
    fontSize: 13,
    color: COLORS.textSecondary,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginTop: 4,
  },
});
