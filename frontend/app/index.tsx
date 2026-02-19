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
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import MapView, { Marker, PROVIDER_DEFAULT } from 'react-native-maps';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { getStations } from '../src/services/api';
import { FuelStation } from '../src/types';
import { StationCard } from '../src/components/StationCard';
import { FilterModal } from '../src/components/FilterModal';
import { LoadingSpinner } from '../src/components/LoadingSpinner';
import { COLORS, FUEL_TYPE_COLORS } from '../src/constants';

const { width, height } = Dimensions.get('window');

export default function StationsScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const [stations, setStations] = useState<FuelStation[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [viewMode, setViewMode] = useState<'map' | 'list'>('map');
  const [filterModalVisible, setFilterModalVisible] = useState(false);
  const [selectedFuelTypes, setSelectedFuelTypes] = useState<string[]>([]);
  const [mapRegion, setMapRegion] = useState({
    latitude: 37.0902,
    longitude: -95.7129,
    latitudeDelta: 40,
    longitudeDelta: 40,
  });

  const fetchStations = useCallback(async () => {
    try {
      const filters = selectedFuelTypes.length === 1
        ? { fuel_type: selectedFuelTypes[0] }
        : undefined;
      const data = await getStations(filters);
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
  }, [selectedFuelTypes]);

  useEffect(() => {
    fetchStations();
  }, [fetchStations]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchStations();
  };

  const handleFuelTypeToggle = (fuelType: string) => {
    setSelectedFuelTypes((prev) =>
      prev.includes(fuelType)
        ? prev.filter((t) => t !== fuelType)
        : [...prev, fuelType]
    );
  };

  const handleClearFilters = () => {
    setSelectedFuelTypes([]);
  };

  const filteredStations = selectedFuelTypes.length > 0
    ? stations.filter((s) =>
        s.fuel_types.some((type) => selectedFuelTypes.includes(type))
      )
    : stations;

  const navigateToStation = (stationId: string) => {
    router.push(`/station/${stationId}`);
  };

  const getMarkerColor = (fuelTypes: string[]) => {
    if (fuelTypes.length === 0) return COLORS.textSecondary;
    return FUEL_TYPE_COLORS[fuelTypes[0]] || COLORS.primary;
  };

  if (loading) {
    return <LoadingSpinner message="Loading stations..." />;
  }

  return (
    <View style={styles.container}>
      {/* View Toggle & Filter Bar */}
      <View style={styles.controlBar}>
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
            <Text style={[styles.toggleText, viewMode === 'map' && styles.toggleTextActive]}>
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
            <Text style={[styles.toggleText, viewMode === 'list' && styles.toggleTextActive]}>
              List
            </Text>
          </TouchableOpacity>
        </View>
        
        <TouchableOpacity
          style={[
            styles.filterButton,
            selectedFuelTypes.length > 0 && styles.filterButtonActive,
          ]}
          onPress={() => setFilterModalVisible(true)}
        >
          <Ionicons
            name="filter"
            size={18}
            color={selectedFuelTypes.length > 0 ? '#FFFFFF' : COLORS.primary}
          />
          <Text
            style={[
              styles.filterText,
              selectedFuelTypes.length > 0 && styles.filterTextActive,
            ]}
          >
            Filter{selectedFuelTypes.length > 0 ? ` (${selectedFuelTypes.length})` : ''}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Map View */}
      {viewMode === 'map' && (
        <View style={styles.mapContainer}>
          <MapView
            style={styles.map}
            provider={PROVIDER_DEFAULT}
            region={mapRegion}
            onRegionChangeComplete={setMapRegion}
            showsUserLocation
            showsMyLocationButton
          >
            {filteredStations.map((station) => (
              <Marker
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
          </MapView>
          
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
      <FilterModal
        visible={filterModalVisible}
        onClose={() => setFilterModalVisible(false)}
        selectedFuelTypes={selectedFuelTypes}
        onFuelTypeToggle={handleFuelTypeToggle}
        onClearFilters={handleClearFilters}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  controlBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  viewToggle: {
    flexDirection: 'row',
    backgroundColor: COLORS.background,
    borderRadius: 8,
    padding: 4,
  },
  toggleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
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
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.primary,
    gap: 4,
  },
  filterButtonActive: {
    backgroundColor: COLORS.primary,
  },
  filterText: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.primary,
  },
  filterTextActive: {
    color: '#FFFFFF',
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
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 3,
  },
  countText: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.text,
  },
  listContent: {
    paddingVertical: 8,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
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
