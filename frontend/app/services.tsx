import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  TextInput,
  Linking,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { getServiceCenters } from '../src/services/api';
import { ServiceCenter } from '../src/types';
import { FuelTypeChip } from '../src/components/FuelTypeChip';
import { RatingStars } from '../src/components/RatingStars';
import { LoadingSpinner } from '../src/components/LoadingSpinner';
import { COLORS } from '../src/constants';

const SERVICE_TYPES = ['All', 'In-Shop', 'Mobile', 'Both'];

export default function ServicesScreen() {
  const router = useRouter();
  const [serviceCenters, setServiceCenters] = useState<ServiceCenter[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedServiceType, setSelectedServiceType] = useState('All');

  const fetchServiceCenters = useCallback(async () => {
    try {
      const filters: any = {};
      if (selectedServiceType !== 'All') filters.service_type = selectedServiceType;
      
      const data = await getServiceCenters(filters);
      setServiceCenters(data);
    } catch (error) {
      console.error('Error fetching service centers:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedServiceType]);

  useEffect(() => {
    fetchServiceCenters();
  }, [fetchServiceCenters]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchServiceCenters();
  };

  const filteredCenters = serviceCenters.filter((center) =>
    center.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    center.city.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
      case 'Both': return 'sync';
      default: return 'construct';
    }
  };

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
      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <Ionicons name="search" size={20} color={COLORS.textSecondary} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search service centers..."
          placeholderTextColor={COLORS.textSecondary}
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => setSearchQuery('')}>
            <Ionicons name="close-circle" size={20} color={COLORS.textSecondary} />
          </TouchableOpacity>
        )}
      </View>

      {/* Service Type Filter */}
      <View style={styles.filterSection}>
        <FlatList
          horizontal
          data={SERVICE_TYPES}
          keyExtractor={(item) => item}
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.filterScroll}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={[
                styles.filterChip,
                selectedServiceType === item && styles.filterChipActive,
              ]}
              onPress={() => setSelectedServiceType(item)}
            >
              <Ionicons
                name={getServiceTypeIcon(item === 'All' ? 'construct' : item)}
                size={14}
                color={selectedServiceType === item ? '#FFFFFF' : COLORS.textSecondary}
              />
              <Text
                style={[
                  styles.filterChipText,
                  selectedServiceType === item && styles.filterChipTextActive,
                ]}
              >
                {item}
              </Text>
            </TouchableOpacity>
          )}
        />
      </View>

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
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    margin: 12,
    paddingHorizontal: 12,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  searchInput: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 8,
    fontSize: 16,
    color: COLORS.text,
  },
  filterSection: {
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.divider,
  },
  filterScroll: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    gap: 8,
  },
  filterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: COLORS.background,
    marginRight: 8,
    gap: 6,
  },
  filterChipActive: {
    backgroundColor: COLORS.primary,
  },
  filterChipText: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.textSecondary,
  },
  filterChipTextActive: {
    color: '#FFFFFF',
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
});
