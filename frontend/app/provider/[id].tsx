import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Linking,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { getProvider } from '../../src/services/api';
import { FuelSystemProvider } from '../../src/types';
import { FuelTypeChip } from '../../src/components/FuelTypeChip';
import { LoadingSpinner } from '../../src/components/LoadingSpinner';
import { COLORS } from '../../src/constants';

export default function ProviderDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [provider, setProvider] = useState<FuelSystemProvider | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProvider();
  }, [id]);

  const fetchProvider = async () => {
    try {
      if (id) {
        const data = await getProvider(id);
        setProvider(data);
      }
    } catch (error) {
      console.error('Error fetching provider:', error);
    } finally {
      setLoading(false);
    }
  };

  const openWebsite = (url: string) => {
    Linking.openURL(url);
  };

  const handleCall = (phone: string) => {
    Linking.openURL(`tel:${phone}`);
  };

  const handleEmail = (email: string) => {
    Linking.openURL(`mailto:${email}`);
  };

  if (loading) {
    return <LoadingSpinner message="Loading provider details..." />;
  }

  if (!provider) {
    return (
      <View style={styles.errorContainer}>
        <Ionicons name="alert-circle-outline" size={48} color={COLORS.error} />
        <Text style={styles.errorText}>Provider not found</Text>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Header Section */}
      <View style={styles.header}>
        <View style={styles.iconContainer}>
          <Ionicons name="business" size={40} color={COLORS.primary} />
        </View>
        <Text style={styles.name}>{provider.name}</Text>
        {provider.formerly_known_as && (
          <Text style={styles.formerName}>
            Formerly: {provider.formerly_known_as}
          </Text>
        )}
        {provider.headquarters && (
          <View style={styles.locationRow}>
            <Ionicons name="location" size={16} color={COLORS.textSecondary} />
            <Text style={styles.location}>{provider.headquarters}</Text>
          </View>
        )}
      </View>

      {/* Description */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>About</Text>
        <Text style={styles.description}>{provider.description}</Text>
      </View>

      {/* Fuel Types */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Fuel Specializations</Text>
        <View style={styles.fuelTypes}>
          {provider.fuel_types.map((type) => (
            <FuelTypeChip key={type} fuelType={type} size="medium" />
          ))}
        </View>
      </View>

      {/* Products */}
      {provider.products.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Products & Solutions</Text>
          <View style={styles.productsList}>
            {provider.products.map((product, index) => (
              <View key={index} style={styles.productItem}>
                <Ionicons name="cube" size={18} color={COLORS.primary} />
                <Text style={styles.productText}>{product}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Quick Links */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Quick Links</Text>
        <View style={styles.linksContainer}>
          <TouchableOpacity
            style={styles.linkCard}
            onPress={() => openWebsite(provider.website)}
          >
            <View style={styles.linkIconContainer}>
              <Ionicons name="globe" size={24} color={COLORS.secondary} />
            </View>
            <Text style={styles.linkTitle}>Website</Text>
            <Text style={styles.linkSubtitle}>Visit official site</Text>
          </TouchableOpacity>

          {provider.support_url && (
            <TouchableOpacity
              style={styles.linkCard}
              onPress={() => openWebsite(provider.support_url!)}
            >
              <View style={[styles.linkIconContainer, { backgroundColor: COLORS.accent + '20' }]}>
                <Ionicons name="help-circle" size={24} color={COLORS.accent} />
              </View>
              <Text style={styles.linkTitle}>Support</Text>
              <Text style={styles.linkSubtitle}>Get help</Text>
            </TouchableOpacity>
          )}

          {provider.documentation_url && (
            <TouchableOpacity
              style={styles.linkCard}
              onPress={() => openWebsite(provider.documentation_url!)}
            >
              <View style={[styles.linkIconContainer, { backgroundColor: COLORS.primaryLight + '20' }]}>
                <Ionicons name="document-text" size={24} color={COLORS.primaryLight} />
              </View>
              <Text style={styles.linkTitle}>Docs</Text>
              <Text style={styles.linkSubtitle}>Documentation</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Contact Information */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Contact Information</Text>
        <View style={styles.contactContainer}>
          {provider.phone && (
            <TouchableOpacity
              style={styles.contactButton}
              onPress={() => handleCall(provider.phone!)}
            >
              <View style={styles.contactIconContainer}>
                <Ionicons name="call" size={20} color={COLORS.primary} />
              </View>
              <View style={styles.contactInfo}>
                <Text style={styles.contactLabel}>Phone</Text>
                <Text style={styles.contactValue}>{provider.phone}</Text>
              </View>
              <Ionicons name="chevron-forward" size={20} color={COLORS.textSecondary} />
            </TouchableOpacity>
          )}

          {provider.email && (
            <TouchableOpacity
              style={styles.contactButton}
              onPress={() => handleEmail(provider.email!)}
            >
              <View style={styles.contactIconContainer}>
                <Ionicons name="mail" size={20} color={COLORS.primary} />
              </View>
              <View style={styles.contactInfo}>
                <Text style={styles.contactLabel}>Email</Text>
                <Text style={styles.contactValue}>{provider.email}</Text>
              </View>
              <Ionicons name="chevron-forward" size={20} color={COLORS.textSecondary} />
            </TouchableOpacity>
          )}

          <TouchableOpacity
            style={styles.contactButton}
            onPress={() => openWebsite(provider.website)}
          >
            <View style={styles.contactIconContainer}>
              <Ionicons name="globe" size={20} color={COLORS.primary} />
            </View>
            <View style={styles.contactInfo}>
              <Text style={styles.contactLabel}>Website</Text>
              <Text style={styles.contactValue} numberOfLines={1}>
                {provider.website.replace('https://', '').replace('http://', '')}
              </Text>
            </View>
            <Ionicons name="open-outline" size={20} color={COLORS.textSecondary} />
          </TouchableOpacity>
        </View>
      </View>

      {/* Action Button */}
      <TouchableOpacity
        style={styles.primaryButton}
        onPress={() => openWebsite(provider.website)}
      >
        <Ionicons name="open-outline" size={20} color="#FFFFFF" />
        <Text style={styles.primaryButtonText}>Visit Website</Text>
      </TouchableOpacity>

      <View style={styles.bottomPadding} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: COLORS.background,
  },
  errorText: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
    marginTop: 16,
  },
  backButton: {
    marginTop: 20,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: COLORS.primary,
    borderRadius: 8,
  },
  backButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  header: {
    backgroundColor: COLORS.surface,
    padding: 20,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: COLORS.divider,
  },
  iconContainer: {
    width: 80,
    height: 80,
    borderRadius: 20,
    backgroundColor: COLORS.primary + '15',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  name: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.text,
    textAlign: 'center',
  },
  formerName: {
    fontSize: 14,
    color: COLORS.accent,
    fontStyle: 'italic',
    marginTop: 4,
  },
  locationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    gap: 4,
  },
  location: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  section: {
    backgroundColor: COLORS.surface,
    padding: 16,
    marginTop: 8,
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
    lineHeight: 22,
  },
  fuelTypes: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  productsList: {
    gap: 10,
  },
  productItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: COLORS.background,
    padding: 12,
    borderRadius: 8,
  },
  productText: {
    fontSize: 14,
    color: COLORS.text,
    flex: 1,
  },
  linksContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  linkCard: {
    flex: 1,
    minWidth: 100,
    backgroundColor: COLORS.background,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  linkIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: COLORS.secondary + '20',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  linkTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  linkSubtitle: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  contactContainer: {
    gap: 12,
  },
  contactButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.background,
    padding: 14,
    borderRadius: 10,
    gap: 12,
  },
  contactIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.primary + '15',
    justifyContent: 'center',
    alignItems: 'center',
  },
  contactInfo: {
    flex: 1,
  },
  contactLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  contactValue: {
    fontSize: 15,
    fontWeight: '500',
    color: COLORS.text,
  },
  primaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    marginHorizontal: 16,
    marginTop: 16,
    paddingVertical: 16,
    borderRadius: 12,
    gap: 8,
  },
  primaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  bottomPadding: {
    height: 32,
  },
});
