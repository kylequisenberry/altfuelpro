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
import { getInspectors } from '../src/services/api';
import { Inspector } from '../src/types';
import { FuelTypeChip } from '../src/components/FuelTypeChip';
import { RatingStars } from '../src/components/RatingStars';
import { LoadingSpinner } from '../src/components/LoadingSpinner';
import { COLORS } from '../src/constants';

const FUEL_FILTERS = ['All', 'CNG', 'LNG', 'Hydrogen', 'Electric', 'Biodiesel'];

export default function InspectorsScreen() {
  const router = useRouter();
  const [inspectors, setInspectors] = useState<Inspector[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFuelType, setSelectedFuelType] = useState('All');

  const fetchInspectors = useCallback(async () => {
    try {
      const filters: any = {};
      if (selectedFuelType !== 'All') filters.fuel_type = selectedFuelType;
      
      const data = await getInspectors(filters);
      setInspectors(data);
    } catch (error) {
      console.error('Error fetching inspectors:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedFuelType]);

  useEffect(() => {
    fetchInspectors();
  }, [fetchInspectors]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchInspectors();
  };

  const filteredInspectors = inspectors.filter((inspector) =>
    inspector.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    inspector.city.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (inspector.company && inspector.company.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const navigateToInspector = (id: string) => {
    router.push(`/inspector/${id}`);
  };

  const handleCall = (phone: string) => {
    Linking.openURL(`tel:${phone}`);
  };

  const handleEmail = (email: string) => {
    Linking.openURL(`mailto:${email}`);
  };

  const renderInspectorCard = ({ item }: { item: Inspector }) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => navigateToInspector(item.id)}
      activeOpacity={0.7}
    >
      <View style={styles.cardHeader}>
        <View style={styles.avatarContainer}>
          <Ionicons name="person" size={24} color={COLORS.primary} />
        </View>
        <View style={styles.headerInfo}>
          <Text style={styles.name}>{item.name}</Text>
          {item.company && (
            <Text style={styles.company}>{item.company}</Text>
          )}
          <Text style={styles.location}>
            <Ionicons name="location" size={12} color={COLORS.textSecondary} />
            {' '}{item.city}, {item.state}
          </Text>
        </View>
        <View style={styles.experienceBadge}>
          <Text style={styles.experienceNumber}>{item.years_experience}</Text>
          <Text style={styles.experienceLabel}>years</Text>
        </View>
      </View>

      <RatingStars rating={item.rating} reviewCount={item.review_count} />

      <View style={styles.fuelTypes}>
        {item.fuel_specializations.map((type) => (
          <FuelTypeChip key={type} fuelType={type} size="small" />
        ))}
      </View>

      {item.certifications.length > 0 && (
        <View style={styles.certifications}>
          <Ionicons name="ribbon" size={14} color={COLORS.accent} />
          <Text style={styles.certText} numberOfLines={2}>
            {item.certifications.slice(0, 3).join(' • ')}
          </Text>
        </View>
      )}

      {item.service_area.length > 0 && (
        <View style={styles.serviceArea}>
          <Ionicons name="map-outline" size={14} color={COLORS.textSecondary} />
          <Text style={styles.serviceAreaText} numberOfLines={1}>
            Serves: {item.service_area.join(', ')}
          </Text>
        </View>
      )}

      <View style={styles.cardFooter}>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => handleCall(item.phone)}
        >
          <Ionicons name="call" size={16} color={COLORS.primary} />
          <Text style={styles.actionText}>Call</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => handleEmail(item.email)}
        >
          <Ionicons name="mail" size={16} color={COLORS.primary} />
          <Text style={styles.actionText}>Email</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.actionButton, styles.viewButton]}
          onPress={() => navigateToInspector(item.id)}
        >
          <Text style={styles.viewButtonText}>View Profile</Text>
          <Ionicons name="chevron-forward" size={16} color="#FFFFFF" />
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );

  if (loading) {
    return <LoadingSpinner message="Loading inspectors..." />;
  }

  return (
    <View style={styles.container}>
      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <Ionicons name="search" size={20} color={COLORS.textSecondary} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search inspectors..."
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

      {/* Fuel Type Filter */}
      <View style={styles.filterSection}>
        <FlatList
          horizontal
          data={FUEL_FILTERS}
          keyExtractor={(item) => item}
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.filterScroll}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={[
                styles.filterChip,
                selectedFuelType === item && styles.filterChipActive,
              ]}
              onPress={() => setSelectedFuelType(item)}
            >
              <Text
                style={[
                  styles.filterChipText,
                  selectedFuelType === item && styles.filterChipTextActive,
                ]}
              >
                {item}
              </Text>
            </TouchableOpacity>
          )}
        />
      </View>

      {/* Inspectors List */}
      <FlatList
        data={filteredInspectors}
        keyExtractor={(item) => item.id}
        renderItem={renderInspectorCard}
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
            <Ionicons name="shield-checkmark-outline" size={48} color={COLORS.textLight} />
            <Text style={styles.emptyText}>No inspectors found</Text>
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
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: COLORS.background,
    marginRight: 8,
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
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  avatarContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: COLORS.primary + '20',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerInfo: {
    flex: 1,
    marginLeft: 12,
  },
  name: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  company: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  location: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 4,
  },
  experienceBadge: {
    backgroundColor: COLORS.accent + '20',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    alignItems: 'center',
  },
  experienceNumber: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.accent,
  },
  experienceLabel: {
    fontSize: 10,
    color: COLORS.accent,
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
    alignItems: 'flex-start',
    gap: 6,
    marginBottom: 8,
  },
  certText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    flex: 1,
    lineHeight: 18,
  },
  serviceArea: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 12,
  },
  serviceAreaText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    flex: 1,
  },
  cardFooter: {
    flexDirection: 'row',
    gap: 8,
    borderTopWidth: 1,
    borderTopColor: COLORS.divider,
    paddingTop: 12,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary + '15',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    gap: 4,
  },
  actionText: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.primary,
  },
  viewButton: {
    flex: 1,
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
  },
  viewButtonText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#FFFFFF',
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
