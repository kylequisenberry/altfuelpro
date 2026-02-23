import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Linking,
  Alert,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { MapViewComponent, MarkerComponent } from '../../src/components/MapWrapper';
import { getServiceCenter } from '../../src/services/api';
import { ServiceCenter } from '../../src/types';
import { FuelTypeChip } from '../../src/components/FuelTypeChip';
import { RatingStars } from '../../src/components/RatingStars';
import { LoadingSpinner } from '../../src/components/LoadingSpinner';
import { NavigationButton } from '../../src/components/NavigationButton';
import { showNavigationPicker } from '../../src/utils/navigation';
import { COLORS } from '../../src/constants';

export default function ServiceCenterDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [center, setCenter] = useState<ServiceCenter | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchServiceCenter();
  }, [id]);

  const fetchServiceCenter = async () => {
    try {
      const data = await getServiceCenter(id as string);
      setCenter(data);
    } catch (error) {
      console.error('Error fetching service center:', error);
      Alert.alert('Error', 'Failed to load service center details');
    } finally {
      setLoading(false);
    }
  };

  const handleCall = () => {
    if (center?.phone) {
      Linking.openURL(`tel:${center.phone}`);
    }
  };

  const handleEmail = () => {
    if (center?.email) {
      Linking.openURL(`mailto:${center.email}`);
    }
  };

  const handleWebsite = () => {
    if (center?.website) {
      Linking.openURL(center.website);
    }
  };

  const handleDirections = () => {
    if (center) {
      const url = `https://www.google.com/maps/dir/?api=1&destination=${center.latitude},${center.longitude}`;
      Linking.openURL(url);
    }
  };

  const getServiceTypeIcon = (type: string): keyof typeof Ionicons.glyphMap => {
    switch (type) {
      case 'Mobile': return 'car';
      case 'In-Shop': return 'business';
      case 'Both': return 'sync';
      default: return 'construct';
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading service center details..." />;
  }

  if (!center) {
    return (
      <View style={styles.errorContainer}>
        <Ionicons name="alert-circle-outline" size={48} color={COLORS.error} />
        <Text style={styles.errorText}>Service center not found</Text>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Map Section */}
      <View style={styles.mapContainer}>
        <MapViewComponent
          style={styles.map}
          initialRegion={{
            latitude: center.latitude,
            longitude: center.longitude,
            latitudeDelta: 0.01,
            longitudeDelta: 0.01,
          }}
          scrollEnabled={false}
          zoomEnabled={false}
        >
          <MarkerComponent
            coordinate={{
              latitude: center.latitude,
              longitude: center.longitude,
            }}
            pinColor={COLORS.primary}
          />
        </MapViewComponent>
      </View>

      <View style={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.nameRow}>
            <Text style={styles.name}>{center.name}</Text>
            <View style={styles.serviceTypeBadge}>
              <Ionicons name={getServiceTypeIcon(center.service_type)} size={14} color={COLORS.secondary} />
              <Text style={styles.serviceTypeText}>{center.service_type}</Text>
            </View>
          </View>
          
          <Text style={styles.address}>
            {center.address}, {center.city}, {center.state} {center.zip_code}
          </Text>
          
          <View style={styles.ratingRow}>
            <RatingStars rating={center.rating} reviewCount={center.review_count} size={20} />
          </View>
        </View>

        {/* Quick Actions */}
        <View style={styles.quickActions}>
          <TouchableOpacity style={styles.quickActionButton} onPress={handleCall}>
            <View style={[styles.quickActionIcon, { backgroundColor: COLORS.primary + '20' }]}>
              <Ionicons name="call" size={22} color={COLORS.primary} />
            </View>
            <Text style={styles.quickActionText}>Call</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.quickActionButton} onPress={handleDirections}>
            <View style={[styles.quickActionIcon, { backgroundColor: COLORS.secondary + '20' }]}>
              <Ionicons name="navigate" size={22} color={COLORS.secondary} />
            </View>
            <Text style={styles.quickActionText}>Directions</Text>
          </TouchableOpacity>
          
          {center.email && (
            <TouchableOpacity style={styles.quickActionButton} onPress={handleEmail}>
              <View style={[styles.quickActionIcon, { backgroundColor: COLORS.accent + '20' }]}>
                <Ionicons name="mail" size={22} color={COLORS.accent} />
              </View>
              <Text style={styles.quickActionText}>Email</Text>
            </TouchableOpacity>
          )}
          
          {center.website && (
            <TouchableOpacity style={styles.quickActionButton} onPress={handleWebsite}>
              <View style={[styles.quickActionIcon, { backgroundColor: COLORS.success + '20' }]}>
                <Ionicons name="globe" size={22} color={COLORS.success} />
              </View>
              <Text style={styles.quickActionText}>Website</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Contact Info */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Contact Information</Text>
          
          <TouchableOpacity style={styles.contactRow} onPress={handleCall}>
            <Ionicons name="call-outline" size={20} color={COLORS.primary} />
            <Text style={styles.contactText}>{center.phone}</Text>
            <Ionicons name="chevron-forward" size={20} color={COLORS.textLight} />
          </TouchableOpacity>
          
          {center.email && (
            <TouchableOpacity style={styles.contactRow} onPress={handleEmail}>
              <Ionicons name="mail-outline" size={20} color={COLORS.primary} />
              <Text style={styles.contactText}>{center.email}</Text>
              <Ionicons name="chevron-forward" size={20} color={COLORS.textLight} />
            </TouchableOpacity>
          )}
          
          {center.hours && (
            <View style={styles.contactRow}>
              <Ionicons name="time-outline" size={20} color={COLORS.primary} />
              <Text style={styles.contactText}>{center.hours}</Text>
            </View>
          )}
        </View>

        {/* Fuel Specializations */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Fuel Specializations</Text>
          <View style={styles.fuelTypes}>
            {center.fuel_specializations.map((type) => (
              <FuelTypeChip key={type} fuelType={type} selected />
            ))}
          </View>
        </View>

        {/* Services Offered */}
        {center.services_offered.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Services Offered</Text>
            <View style={styles.servicesList}>
              {center.services_offered.map((service, index) => (
                <View key={index} style={styles.serviceItem}>
                  <Ionicons name="checkmark-circle" size={18} color={COLORS.success} />
                  <Text style={styles.serviceText}>{service}</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Certifications */}
        {center.certifications.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Certifications</Text>
            <View style={styles.certifications}>
              {center.certifications.map((cert, index) => (
                <View key={index} style={styles.certBadge}>
                  <Ionicons name="ribbon" size={16} color={COLORS.accent} />
                  <Text style={styles.certText}>{cert}</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Book Appointment Button */}
        <TouchableOpacity style={styles.bookButton} onPress={handleCall}>
          <Ionicons name="calendar" size={22} color="#FFFFFF" />
          <Text style={styles.bookButtonText}>Book Appointment</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  mapContainer: {
    height: 180,
  },
  map: {
    flex: 1,
  },
  content: {
    padding: 16,
  },
  header: {
    marginBottom: 20,
  },
  nameRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  name: {
    fontSize: 22,
    fontWeight: '700',
    color: COLORS.text,
    flex: 1,
    marginRight: 12,
  },
  serviceTypeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.secondary + '15',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    gap: 4,
  },
  serviceTypeText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.secondary,
  },
  address: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginBottom: 12,
  },
  ratingRow: {
    marginTop: 4,
  },
  quickActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  quickActionButton: {
    alignItems: 'center',
  },
  quickActionIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 6,
  },
  quickActionText: {
    fontSize: 12,
    color: COLORS.textSecondary,
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
  contactRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.divider,
    gap: 12,
  },
  contactText: {
    flex: 1,
    fontSize: 15,
    color: COLORS.text,
  },
  fuelTypes: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  servicesList: {
    gap: 10,
  },
  serviceItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  serviceText: {
    fontSize: 14,
    color: COLORS.text,
  },
  certifications: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  certBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.accent + '15',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
    gap: 6,
  },
  certText: {
    fontSize: 13,
    color: COLORS.text,
    fontWeight: '500',
  },
  bookButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    paddingVertical: 16,
    borderRadius: 12,
    gap: 10,
    marginBottom: 20,
  },
  bookButtonText: {
    fontSize: 17,
    fontWeight: '600',
    color: '#FFFFFF',
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
