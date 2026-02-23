import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  Linking,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { getServiceCenters, getNearbyServiceCenters, ServiceCenterWithDistance } from '../src/services/api';
import { ServiceCenter } from '../src/types';
import { FuelTypeChip } from '../src/components/FuelTypeChip';
import { RatingStars } from '../src/components/RatingStars';
import { LoadingSpinner } from '../src/components/LoadingSpinner';
import { ServicesFilterModal, ServiceFilters } from '../src/components/ServicesFilterModal';
import { useLocation } from '../src/hooks/useLocation';
import { COLORS } from '../src/constants';

// Type for service center with optional distance
type ServiceCenterDisplay = ServiceCenter & {
  distance_miles?: number;
  distance_km?: number;
};

export default function ServicesScreen() {
  const router = useRouter();
  const [serviceCenters, setServiceCenters] = useState<ServiceCenterDisplay[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filterModalVisible, setFilterModalVisible] = useState(false);
  const [nearbyMode, setNearbyMode] = useState(false);
  const [locationLoading, setLocationLoading] = useState(false);
  const [filters, setFilters] = useState<ServiceFilters>({
    city: '',
    state: '',
    zipCode: '',
    radius: undefined,
    fuelTypes: [],
    serviceType: undefined,
  });

  const { getLocation, error: locationError, clearError } = useLocation();

  const fetchServiceCenters = useCallback(async () => {
    try {
      const apiFilters: any = {};
      
      if (filters.serviceType) {
        apiFilters.service_type = filters.serviceType;
      }
      if (filters.state) {
        apiFilters.state = filters.state;
      }
      if (filters.city) {
        apiFilters.city = filters.city;
      }
      if (filters.fuelTypes.length === 1) {
        apiFilters.fuel_type = filters.fuelTypes[0];
      }
      
      const data = await getServiceCenters(Object.keys(apiFilters).length > 0 ? apiFilters : undefined);
      setServiceCenters(data);
    } catch (error) {
      console.error('Error fetching service centers:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchServiceCenters();
  }, [fetchServiceCenters]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchServiceCenters();
  };

  const handleApplyFilters = (newFilters: ServiceFilters) => {
    setFilters(newFilters);
  };

  // Client-side filtering for multiple fuel types
  const filteredCenters = serviceCenters.filter((center) => {
    if (filters.fuelTypes.length > 1) {
      return center.fuel_specializations.some((type) => filters.fuelTypes.includes(type));
    }
    return true;
  });

  const navigateToServiceCenter = (id: string) => {
    router.push(`/service/${id}`);
  };

  const handleCall = (phone: string) => {
    Linking.openURL(`tel:${phone}`);
  };

  const getServiceTypeIcon = (type: string): keyof typeof Ionicons.glyphMap => {
    switch (type) {
      case 'Mobile': return 'car';
      case 'In-Shop': return 'business';
      case 'Both': return 'swap-horizontal';
      default: return 'construct';
    }
  };

  const activeFilterCount = [
    filters.city,
    filters.state,
    filters.zipCode,
    filters.radius,
    filters.fuelTypes.length > 0,
    filters.serviceType
  ].filter(Boolean).length;

  const renderServiceCard = ({ item }: { item: ServiceCenter }) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => navigateToServiceCenter(item.id)}
      activeOpacity={0.7}
    >
      <View style={styles.cardHeader}>
        <View style={styles.nameRow}>
          <Ionicons name="construct" size={20} color={COLORS.primary} />
          <Text style={styles.name} numberOfLines={1}>{item.name}</Text>
        </View>
        <View style={styles.serviceTypeBadge}>
          <Ionicons name={getServiceTypeIcon(item.service_type)} size={12} color={COLORS.secondary} />
          <Text style={styles.serviceTypeText}>{item.service_type}</Text>
        </View>
      </View>

      <Text style={styles.address} numberOfLines={1}>
        {item.address}, {item.city}, {item.state}
      </Text>

      <RatingStars rating={item.rating} reviewCount={item.review_count} />

      <View style={styles.fuelTypes}>
        {item.fuel_specializations.map((type) => (
          <FuelTypeChip key={type} fuelType={type} size="small" />
        ))}
      </View>

      {item.certifications.length > 0 && (
        <View style={styles.certifications}>
          <Ionicons name="ribbon" size={14} color={COLORS.accent} />
          <Text style={styles.certText} numberOfLines={1}>
            {item.certifications.slice(0, 2).join(' • ')}
          </Text>
        </View>
      )}

      <View style={styles.cardFooter}>
        {item.hours && (
          <View style={styles.hoursRow}>
            <Ionicons name="time-outline" size={14} color={COLORS.textSecondary} />
            <Text style={styles.hoursText} numberOfLines={1}>{item.hours}</Text>
          </View>
        )}
        <TouchableOpacity
          style={styles.callButton}
          onPress={() => handleCall(item.phone)}
        >
          <Ionicons name="call" size={16} color={COLORS.primary} />
          <Text style={styles.callText}>Call</Text>
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );

  if (loading) {
    return <LoadingSpinner message="Loading service centers..." />;
  }

  return (
    <View style={styles.container}>
      {/* Header Controls */}
      <View style={styles.headerControls}>
        <Text style={styles.resultCount}>
          {filteredCenters.length} service center{filteredCenters.length !== 1 ? 's' : ''}
        </Text>
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
            {filters.serviceType && `${filters.serviceType} `}
            {filters.state && `• ${filters.state} `}
            {filters.city && `• ${filters.city} `}
            {filters.zipCode && `• ZIP: ${filters.zipCode} `}
            {filters.radius && `• within ${filters.radius} mi `}
            {filters.fuelTypes.length > 0 && `• ${filters.fuelTypes.join(', ')}`}
          </Text>
          <TouchableOpacity onPress={() => setFilters({
            city: '',
            state: '',
            zipCode: '',
            radius: undefined,
            fuelTypes: [],
            serviceType: undefined,
          })}>
            <Ionicons name="close-circle" size={18} color={COLORS.textSecondary} />
          </TouchableOpacity>
        </View>
      )}

      {/* Service Centers List */}
      <FlatList
        data={filteredCenters}
        keyExtractor={(item) => item.id}
        renderItem={renderServiceCard}
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
            <Ionicons name="construct-outline" size={48} color={COLORS.textLight} />
            <Text style={styles.emptyText}>No service centers found</Text>
            <Text style={styles.emptySubtext}>Try adjusting your filters</Text>
          </View>
        }
      />

      {/* Filter Modal */}
      <ServicesFilterModal
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
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.divider,
  },
  resultCount: {
    fontSize: 14,
    color: COLORS.textSecondary,
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
  listContent: {
    padding: 12,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 8,
  },
  name: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    flex: 1,
  },
  serviceTypeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.secondary + '15',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    gap: 4,
  },
  serviceTypeText: {
    fontSize: 11,
    fontWeight: '500',
    color: COLORS.secondary,
  },
  address: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginBottom: 8,
  },
  fuelTypes: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 10,
    marginBottom: 8,
  },
  certifications: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 12,
  },
  certText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    flex: 1,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: COLORS.divider,
    paddingTop: 12,
  },
  hoursRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    flex: 1,
  },
  hoursText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    flex: 1,
  },
  callButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary + '15',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    gap: 4,
  },
  callText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.primary,
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
