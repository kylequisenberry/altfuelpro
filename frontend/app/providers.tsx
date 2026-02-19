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
  ScrollView,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { getProviders } from '../src/services/api';
import { FuelSystemProvider } from '../src/types';
import { FuelTypeChip } from '../src/components/FuelTypeChip';
import { LoadingSpinner } from '../src/components/LoadingSpinner';
import { COLORS } from '../src/constants';

const FUEL_FILTERS = ['All', 'CNG', 'LNG', 'Hydrogen', 'Electric', 'Biodiesel', 'LPG'];

export default function ProvidersScreen() {
  const router = useRouter();
  const [providers, setProviders] = useState<FuelSystemProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFuelType, setSelectedFuelType] = useState('All');

  const fetchProviders = useCallback(async () => {
    try {
      const filters: any = {};
      if (selectedFuelType !== 'All') filters.fuel_type = selectedFuelType;
      if (searchQuery.trim()) filters.search = searchQuery.trim();
      
      const data = await getProviders(filters);
      setProviders(data);
    } catch (error) {
      console.error('Error fetching providers:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedFuelType, searchQuery]);

  useEffect(() => {
    fetchProviders();
  }, [fetchProviders]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchProviders();
  };

  const openWebsite = (url: string) => {
    Linking.openURL(url);
  };

  const handleCall = (phone: string) => {
    Linking.openURL(`tel:${phone}`);
  };

  const navigateToProvider = (id: string) => {
    router.push(`/provider/${id}`);
  };

  const renderProviderCard = ({ item }: { item: FuelSystemProvider }) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => navigateToProvider(item.id)}
      activeOpacity={0.7}
    >
      <View style={styles.cardHeader}>
        <View style={styles.iconContainer}>
          <Ionicons name="business" size={28} color={COLORS.primary} />
        </View>
        <View style={styles.headerInfo}>
          <Text style={styles.name}>{item.name}</Text>
          {item.formerly_known_as && (
            <Text style={styles.formerName}>
              Formerly: {item.formerly_known_as}
            </Text>
          )}
          {item.headquarters && (
            <Text style={styles.location}>
              <Ionicons name="location" size={12} color={COLORS.textSecondary} />
              {' '}{item.headquarters}
            </Text>
          )}
        </View>
      </View>

      <Text style={styles.description} numberOfLines={3}>
        {item.description}
      </Text>

      <View style={styles.fuelTypes}>
        {item.fuel_types.map((type) => (
          <FuelTypeChip key={type} fuelType={type} size="small" />
        ))}
      </View>

      {item.products.length > 0 && (
        <View style={styles.productsContainer}>
          <Ionicons name="cube-outline" size={14} color={COLORS.textSecondary} />
          <Text style={styles.productsText} numberOfLines={2}>
            {item.products.slice(0, 3).join(' • ')}
          </Text>
        </View>
      )}

      <View style={styles.cardFooter}>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => openWebsite(item.website)}
        >
          <Ionicons name="globe-outline" size={16} color={COLORS.primary} />
          <Text style={styles.actionText}>Website</Text>
        </TouchableOpacity>
        
        {item.support_url && (
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => openWebsite(item.support_url!)}
          >
            <Ionicons name="help-circle-outline" size={16} color={COLORS.primary} />
            <Text style={styles.actionText}>Support</Text>
          </TouchableOpacity>
        )}
        
        {item.phone && (
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => handleCall(item.phone!)}
          >
            <Ionicons name="call-outline" size={16} color={COLORS.primary} />
            <Text style={styles.actionText}>Call</Text>
          </TouchableOpacity>
        )}
        
        <TouchableOpacity
          style={[styles.actionButton, styles.viewButton]}
          onPress={() => navigateToProvider(item.id)}
        >
          <Text style={styles.viewButtonText}>Details</Text>
          <Ionicons name="chevron-forward" size={16} color="#FFFFFF" />
        </TouchableOpacity>
      </View>
    </TouchableOpacity>
  );

  if (loading) {
    return <LoadingSpinner message="Loading providers..." />;
  }

  return (
    <View style={styles.container}>
      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <Ionicons name="search" size={20} color={COLORS.textSecondary} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search providers..."
          placeholderTextColor={COLORS.textSecondary}
          value={searchQuery}
          onChangeText={setSearchQuery}
          onSubmitEditing={fetchProviders}
          returnKeyType="search"
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => setSearchQuery('')}>
            <Ionicons name="close-circle" size={20} color={COLORS.textSecondary} />
          </TouchableOpacity>
        )}
      </View>

      {/* Fuel Type Filter */}
      <View style={styles.filterSection}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.filterScroll}
        >
          {FUEL_FILTERS.map((item) => (
            <TouchableOpacity
              key={item}
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
          ))}
        </ScrollView>
      </View>

      {/* Provider Count */}
      <View style={styles.countContainer}>
        <Text style={styles.countText}>
          {providers.length} provider{providers.length !== 1 ? 's' : ''} found
        </Text>
      </View>

      {/* Providers List */}
      <FlatList
        data={providers}
        keyExtractor={(item) => item.id}
        renderItem={renderProviderCard}
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
            <Ionicons name="business-outline" size={48} color={COLORS.textLight} />
            <Text style={styles.emptyText}>No providers found</Text>
            <Text style={styles.emptySubtext}>Try adjusting your filters</Text>
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
  countContainer: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: COLORS.surface,
  },
  countText: {
    fontSize: 13,
    color: COLORS.textSecondary,
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
  iconContainer: {
    width: 52,
    height: 52,
    borderRadius: 12,
    backgroundColor: COLORS.primary + '15',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerInfo: {
    flex: 1,
    marginLeft: 12,
  },
  name: {
    fontSize: 17,
    fontWeight: '600',
    color: COLORS.text,
  },
  formerName: {
    fontSize: 12,
    color: COLORS.accent,
    fontStyle: 'italic',
    marginTop: 2,
  },
  location: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 4,
  },
  description: {
    fontSize: 14,
    color: COLORS.textSecondary,
    lineHeight: 20,
    marginBottom: 12,
  },
  fuelTypes: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: 10,
  },
  productsContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 6,
    marginBottom: 12,
    backgroundColor: COLORS.background,
    padding: 10,
    borderRadius: 8,
  },
  productsText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    flex: 1,
    lineHeight: 18,
  },
  cardFooter: {
    flexDirection: 'row',
    flexWrap: 'wrap',
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
    minWidth: 80,
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
  emptySubtext: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginTop: 4,
  },
});
