import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  TextInput,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { getRegulations } from '../src/services/api';
import { Regulation } from '../src/types';
import { FuelTypeChip } from '../src/components/FuelTypeChip';
import { LoadingSpinner } from '../src/components/LoadingSpinner';
import { COLORS } from '../src/constants';

const CATEGORIES = ['All', 'Safety', 'Emissions', 'Installation', 'Incentive'];
const JURISDICTIONS = ['All', 'Federal', 'State'];

export default function RegulationsScreen() {
  const router = useRouter();
  const [regulations, setRegulations] = useState<Regulation[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedJurisdiction, setSelectedJurisdiction] = useState('All');

  const fetchRegulations = useCallback(async () => {
    try {
      const filters: any = {};
      if (selectedCategory !== 'All') filters.category = selectedCategory;
      if (selectedJurisdiction !== 'All') filters.jurisdiction = selectedJurisdiction;
      
      const data = await getRegulations(filters);
      setRegulations(data);
    } catch (error) {
      console.error('Error fetching regulations:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedCategory, selectedJurisdiction]);

  useEffect(() => {
    fetchRegulations();
  }, [fetchRegulations]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchRegulations();
  };

  const filteredRegulations = regulations.filter((reg) =>
    reg.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    reg.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const navigateToRegulation = (id: string) => {
    router.push(`/regulation/${id}`);
  };

  const getCategoryIcon = (category: string): keyof typeof Ionicons.glyphMap => {
    switch (category) {
      case 'Safety': return 'shield-checkmark';
      case 'Emissions': return 'leaf';
      case 'Installation': return 'construct';
      case 'Incentive': return 'cash';
      default: return 'document-text';
    }
  };

  const renderRegulationCard = ({ item }: { item: Regulation }) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => navigateToRegulation(item.id)}
      activeOpacity={0.7}
    >
      <View style={styles.cardHeader}>
        <View style={styles.categoryBadge}>
          <Ionicons name={getCategoryIcon(item.category)} size={14} color={COLORS.primary} />
          <Text style={styles.categoryText}>{item.category}</Text>
        </View>
        <View style={styles.jurisdictionBadge}>
          <Text style={styles.jurisdictionText}>
            {item.jurisdiction}{item.state ? ` - ${item.state}` : ''}
          </Text>
        </View>
      </View>
      
      <Text style={styles.title} numberOfLines={2}>{item.title}</Text>
      
      {item.code_reference && (
        <Text style={styles.codeRef}>{item.code_reference}</Text>
      )}
      
      <Text style={styles.summary} numberOfLines={3}>{item.summary}</Text>
      
      <View style={styles.fuelTypes}>
        {item.fuel_types.slice(0, 4).map((type) => (
          <FuelTypeChip key={type} fuelType={type} size="small" />
        ))}
        {item.fuel_types.length > 4 && (
          <Text style={styles.moreTypes}>+{item.fuel_types.length - 4} more</Text>
        )}
      </View>
    </TouchableOpacity>
  );

  if (loading) {
    return <LoadingSpinner message="Loading regulations..." />;
  }

  return (
    <View style={styles.container}>
      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <Ionicons name="search" size={20} color={COLORS.textSecondary} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search regulations..."
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

      {/* Category Filter */}
      <View style={styles.filterSection}>
        <FlatList
          horizontal
          data={CATEGORIES}
          keyExtractor={(item) => item}
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.filterScroll}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={[
                styles.filterChip,
                selectedCategory === item && styles.filterChipActive,
              ]}
              onPress={() => setSelectedCategory(item)}
            >
              <Text
                style={[
                  styles.filterChipText,
                  selectedCategory === item && styles.filterChipTextActive,
                ]}
              >
                {item}
              </Text>
            </TouchableOpacity>
          )}
        />
      </View>

      {/* Jurisdiction Filter */}
      <View style={styles.jurisdictionFilter}>
        {JURISDICTIONS.map((jur) => (
          <TouchableOpacity
            key={jur}
            style={[
              styles.jurisdictionChip,
              selectedJurisdiction === jur && styles.jurisdictionChipActive,
            ]}
            onPress={() => setSelectedJurisdiction(jur)}
          >
            <Text
              style={[
                styles.jurisdictionChipText,
                selectedJurisdiction === jur && styles.jurisdictionChipTextActive,
              ]}
            >
              {jur}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Regulations List */}
      <FlatList
        data={filteredRegulations}
        keyExtractor={(item) => item.id}
        renderItem={renderRegulationCard}
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
            <Ionicons name="document-text-outline" size={48} color={COLORS.textLight} />
            <Text style={styles.emptyText}>No regulations found</Text>
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
  jurisdictionFilter: {
    flexDirection: 'row',
    padding: 12,
    gap: 8,
    backgroundColor: COLORS.surface,
  },
  jurisdictionChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  jurisdictionChipActive: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary + '10',
  },
  jurisdictionChipText: {
    fontSize: 13,
    color: COLORS.textSecondary,
  },
  jurisdictionChipTextActive: {
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
  categoryBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  categoryText: {
    fontSize: 12,
    fontWeight: '500',
    color: COLORS.primary,
  },
  jurisdictionBadge: {
    backgroundColor: COLORS.background,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  jurisdictionText: {
    fontSize: 11,
    fontWeight: '500',
    color: COLORS.textSecondary,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 4,
  },
  codeRef: {
    fontSize: 12,
    color: COLORS.secondary,
    fontWeight: '500',
    marginBottom: 8,
  },
  summary: {
    fontSize: 13,
    color: COLORS.textSecondary,
    lineHeight: 20,
    marginBottom: 12,
  },
  fuelTypes: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    alignItems: 'center',
  },
  moreTypes: {
    fontSize: 12,
    color: COLORS.textSecondary,
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
