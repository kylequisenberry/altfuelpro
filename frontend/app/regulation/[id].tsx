import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { getRegulation } from '../../src/services/api';
import { Regulation } from '../../src/types';
import { FuelTypeChip } from '../../src/components/FuelTypeChip';
import { LoadingSpinner } from '../../src/components/LoadingSpinner';
import { COLORS } from '../../src/constants';

export default function RegulationDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [regulation, setRegulation] = useState<Regulation | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRegulation();
  }, [id]);

  const fetchRegulation = async () => {
    try {
      const data = await getRegulation(id as string);
      setRegulation(data);
    } catch (error) {
      console.error('Error fetching regulation:', error);
      Alert.alert('Error', 'Failed to load regulation details');
    } finally {
      setLoading(false);
    }
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

  const getCategoryColor = (category: string): string => {
    switch (category) {
      case 'Safety': return '#D32F2F';
      case 'Emissions': return '#4CAF50';
      case 'Installation': return '#FF9800';
      case 'Incentive': return '#2196F3';
      default: return COLORS.primary;
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading regulation details..." />;
  }

  if (!regulation) {
    return (
      <View style={styles.errorContainer}>
        <Ionicons name="alert-circle-outline" size={48} color={COLORS.error} />
        <Text style={styles.errorText}>Regulation not found</Text>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const categoryColor = getCategoryColor(regulation.category);

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Header Section */}
      <View style={[styles.headerSection, { backgroundColor: categoryColor + '15' }]}>
        <View style={[styles.categoryBadge, { backgroundColor: categoryColor }]}>
          <Ionicons name={getCategoryIcon(regulation.category)} size={20} color="#FFFFFF" />
          <Text style={styles.categoryText}>{regulation.category}</Text>
        </View>
        
        <Text style={styles.title}>{regulation.title}</Text>
        
        <View style={styles.metaRow}>
          <View style={styles.metaItem}>
            <Ionicons name="business" size={14} color={COLORS.textSecondary} />
            <Text style={styles.metaText}>
              {regulation.jurisdiction}{regulation.state ? ` - ${regulation.state}` : ''}
            </Text>
          </View>
          {regulation.effective_date && (
            <View style={styles.metaItem}>
              <Ionicons name="calendar" size={14} color={COLORS.textSecondary} />
              <Text style={styles.metaText}>
                Effective: {regulation.effective_date}
              </Text>
            </View>
          )}
        </View>
      </View>

      <View style={styles.content}>
        {/* Code Reference */}
        {regulation.code_reference && (
          <View style={styles.codeRefCard}>
            <View style={styles.codeRefHeader}>
              <Ionicons name="document-text" size={20} color={COLORS.secondary} />
              <Text style={styles.codeRefLabel}>Code Reference</Text>
            </View>
            <Text style={styles.codeRefValue}>{regulation.code_reference}</Text>
          </View>
        )}

        {/* Description */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Description</Text>
          <Text style={styles.description}>{regulation.description}</Text>
        </View>

        {/* Summary */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Summary</Text>
          <View style={styles.summaryCard}>
            <Ionicons name="information-circle" size={20} color={COLORS.primary} />
            <Text style={styles.summaryText}>{regulation.summary}</Text>
          </View>
        </View>

        {/* Applicable Fuel Types */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Applicable Fuel Types</Text>
          <View style={styles.fuelTypes}>
            {regulation.fuel_types.map((type) => (
              <FuelTypeChip key={type} fuelType={type} selected />
            ))}
          </View>
        </View>

        {/* Key Points */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Key Points</Text>
          <View style={styles.keyPointsCard}>
            <View style={styles.keyPoint}>
              <Ionicons name="checkmark-circle" size={18} color={COLORS.success} />
              <Text style={styles.keyPointText}>Compliance is mandatory for covered entities</Text>
            </View>
            <View style={styles.keyPoint}>
              <Ionicons name="checkmark-circle" size={18} color={COLORS.success} />
              <Text style={styles.keyPointText}>Regular inspections may be required</Text>
            </View>
            <View style={styles.keyPoint}>
              <Ionicons name="checkmark-circle" size={18} color={COLORS.success} />
              <Text style={styles.keyPointText}>Documentation must be maintained</Text>
            </View>
            <View style={styles.keyPoint}>
              <Ionicons name="warning" size={18} color={COLORS.warning} />
              <Text style={styles.keyPointText}>Non-compliance may result in penalties</Text>
            </View>
          </View>
        </View>

        {/* Actions */}
        <View style={styles.actionsSection}>
          <TouchableOpacity style={styles.actionButton}>
            <Ionicons name="download" size={20} color="#FFFFFF" />
            <Text style={styles.actionButtonText}>Download PDF</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.actionButton, styles.secondaryButton]}>
            <Ionicons name="share-social" size={20} color={COLORS.primary} />
            <Text style={[styles.actionButtonText, styles.secondaryButtonText]}>Share</Text>
          </TouchableOpacity>
        </View>

        {/* Disclaimer */}
        <View style={styles.disclaimer}>
          <Ionicons name="information-circle-outline" size={16} color={COLORS.textLight} />
          <Text style={styles.disclaimerText}>
            This information is provided for reference purposes. Always consult the official 
            regulatory documents and legal professionals for compliance guidance.
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  headerSection: {
    padding: 20,
    paddingTop: 24,
  },
  categoryBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    gap: 6,
    marginBottom: 12,
  },
  categoryText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.text,
    lineHeight: 30,
    marginBottom: 12,
  },
  metaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 16,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  metaText: {
    fontSize: 13,
    color: COLORS.textSecondary,
  },
  content: {
    padding: 16,
  },
  codeRefCard: {
    backgroundColor: COLORS.secondary + '10',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.secondary,
  },
  codeRefHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  codeRefLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.secondary,
  },
  codeRefValue: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.text,
  },
  section: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 12,
  },
  description: {
    fontSize: 15,
    color: COLORS.textSecondary,
    lineHeight: 24,
  },
  summaryCard: {
    flexDirection: 'row',
    backgroundColor: COLORS.primary + '10',
    borderRadius: 8,
    padding: 12,
    gap: 12,
  },
  summaryText: {
    flex: 1,
    fontSize: 14,
    color: COLORS.text,
    lineHeight: 22,
  },
  fuelTypes: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  keyPointsCard: {
    gap: 12,
  },
  keyPoint: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  keyPointText: {
    flex: 1,
    fontSize: 14,
    color: COLORS.text,
    lineHeight: 20,
  },
  actionsSection: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    paddingVertical: 14,
    borderRadius: 10,
    gap: 8,
  },
  secondaryButton: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.primary,
  },
  actionButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  secondaryButtonText: {
    color: COLORS.primary,
  },
  disclaimer: {
    flexDirection: 'row',
    backgroundColor: COLORS.background,
    borderRadius: 8,
    padding: 12,
    gap: 10,
    marginBottom: 20,
  },
  disclaimerText: {
    flex: 1,
    fontSize: 12,
    color: COLORS.textLight,
    lineHeight: 18,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
    padding: 20,
  },
  errorText: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
    marginTop: 16,
  },
  backButton: {
    marginTop: 16,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: COLORS.primary,
    borderRadius: 8,
  },
  backButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});
