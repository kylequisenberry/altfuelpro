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
import { MapViewComponent, MarkerComponent, CircleComponent } from '../../src/components/MapWrapper';
import { getInspector } from '../../src/services/api';
import { Inspector } from '../../src/types';
import { FuelTypeChip } from '../../src/components/FuelTypeChip';
import { RatingStars } from '../../src/components/RatingStars';
import { LoadingSpinner } from '../../src/components/LoadingSpinner';
import { COLORS } from '../../src/constants';

export default function InspectorDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [inspector, setInspector] = useState<Inspector | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInspector();
  }, [id]);

  const fetchInspector = async () => {
    try {
      const data = await getInspector(id as string);
      setInspector(data);
    } catch (error) {
      console.error('Error fetching inspector:', error);
      Alert.alert('Error', 'Failed to load inspector details');
    } finally {
      setLoading(false);
    }
  };

  const handleCall = () => {
    if (inspector?.phone) {
      Linking.openURL(`tel:${inspector.phone}`);
    }
  };

  const handleEmail = () => {
    if (inspector?.email) {
      Linking.openURL(`mailto:${inspector.email}`);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading inspector details..." />;
  }

  if (!inspector) {
    return (
      <View style={styles.errorContainer}>
        <Ionicons name="alert-circle-outline" size={48} color={COLORS.error} />
        <Text style={styles.errorText}>Inspector not found</Text>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Profile Header */}
      <View style={styles.profileHeader}>
        <View style={styles.avatarContainer}>
          <Ionicons name="person" size={48} color={COLORS.primary} />
        </View>
        
        <Text style={styles.name}>{inspector.name}</Text>
        
        {inspector.company && (
          <Text style={styles.company}>{inspector.company}</Text>
        )}
        
        <View style={styles.locationRow}>
          <Ionicons name="location" size={16} color={COLORS.textSecondary} />
          <Text style={styles.location}>{inspector.city}, {inspector.state}</Text>
        </View>
        
        <View style={styles.ratingRow}>
          <RatingStars rating={inspector.rating} reviewCount={inspector.review_count} size={22} />
        </View>
        
        <View style={styles.experienceBadge}>
          <Text style={styles.experienceNumber}>{inspector.years_experience}</Text>
          <Text style={styles.experienceLabel}>Years Experience</Text>
        </View>
      </View>

      <View style={styles.content}>
        {/* Quick Actions */}
        <View style={styles.quickActions}>
          <TouchableOpacity style={[styles.actionButton, styles.primaryAction]} onPress={handleCall}>
            <Ionicons name="call" size={22} color="#FFFFFF" />
            <Text style={styles.primaryActionText}>Call Now</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={[styles.actionButton, styles.secondaryAction]} onPress={handleEmail}>
            <Ionicons name="mail" size={22} color={COLORS.primary} />
            <Text style={styles.secondaryActionText}>Send Email</Text>
          </TouchableOpacity>
        </View>

        {/* Contact Info */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Contact Information</Text>
          
          <TouchableOpacity style={styles.contactRow} onPress={handleCall}>
            <View style={styles.contactIcon}>
              <Ionicons name="call" size={18} color={COLORS.primary} />
            </View>
            <View style={styles.contactInfo}>
              <Text style={styles.contactLabel}>Phone</Text>
              <Text style={styles.contactValue}>{inspector.phone}</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color={COLORS.textLight} />
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.contactRow} onPress={handleEmail}>
            <View style={styles.contactIcon}>
              <Ionicons name="mail" size={18} color={COLORS.primary} />
            </View>
            <View style={styles.contactInfo}>
              <Text style={styles.contactLabel}>Email</Text>
              <Text style={styles.contactValue}>{inspector.email}</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color={COLORS.textLight} />
          </TouchableOpacity>
          
          {inspector.license_number && (
            <View style={styles.contactRow}>
              <View style={styles.contactIcon}>
                <Ionicons name="card" size={18} color={COLORS.primary} />
              </View>
              <View style={styles.contactInfo}>
                <Text style={styles.contactLabel}>License Number</Text>
                <Text style={styles.contactValue}>{inspector.license_number}</Text>
              </View>
            </View>
          )}
        </View>

        {/* Bio */}
        {inspector.bio && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>About</Text>
            <Text style={styles.bioText}>{inspector.bio}</Text>
          </View>
        )}

        {/* Fuel Specializations */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Fuel Specializations</Text>
          <View style={styles.fuelTypes}>
            {inspector.fuel_specializations.map((type) => (
              <FuelTypeChip key={type} fuelType={type} selected />
            ))}
          </View>
        </View>

        {/* Certifications */}
        {inspector.certifications.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Certifications & Credentials</Text>
            <View style={styles.certifications}>
              {inspector.certifications.map((cert, index) => (
                <View key={index} style={styles.certItem}>
                  <Ionicons name="ribbon" size={18} color={COLORS.accent} />
                  <Text style={styles.certText}>{cert}</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Service Area */}
        {inspector.service_area.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Service Area</Text>
            
            {/* Map */}
            <View style={styles.mapContainer}>
              <MapView
                style={styles.map}
                provider={PROVIDER_DEFAULT}
                initialRegion={{
                  latitude: inspector.latitude,
                  longitude: inspector.longitude,
                  latitudeDelta: 2,
                  longitudeDelta: 2,
                }}
                scrollEnabled={false}
                zoomEnabled={false}
              >
                <Marker
                  coordinate={{
                    latitude: inspector.latitude,
                    longitude: inspector.longitude,
                  }}
                  pinColor={COLORS.primary}
                />
                <Circle
                  center={{
                    latitude: inspector.latitude,
                    longitude: inspector.longitude,
                  }}
                  radius={100000}
                  fillColor={COLORS.primary + '20'}
                  strokeColor={COLORS.primary}
                  strokeWidth={2}
                />
              </MapView>
            </View>
            
            <View style={styles.serviceAreaList}>
              <Ionicons name="map" size={16} color={COLORS.primary} />
              <Text style={styles.serviceAreaText}>
                {inspector.service_area.join(' • ')}
              </Text>
            </View>
          </View>
        )}

        {/* Request Inspection Button */}
        <TouchableOpacity style={styles.requestButton} onPress={handleCall}>
          <Ionicons name="clipboard" size={22} color="#FFFFFF" />
          <Text style={styles.requestButtonText}>Request Inspection</Text>
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
  profileHeader: {
    backgroundColor: COLORS.surface,
    alignItems: 'center',
    paddingVertical: 24,
    paddingHorizontal: 16,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  avatarContainer: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: COLORS.primary + '20',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  name: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: 4,
  },
  company: {
    fontSize: 16,
    color: COLORS.textSecondary,
    marginBottom: 8,
  },
  locationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 12,
  },
  location: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  ratingRow: {
    marginBottom: 16,
  },
  experienceBadge: {
    backgroundColor: COLORS.accent + '15',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 6,
  },
  experienceNumber: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.accent,
  },
  experienceLabel: {
    fontSize: 13,
    color: COLORS.accent,
    fontWeight: '500',
  },
  content: {
    padding: 16,
  },
  quickActions: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 12,
    gap: 8,
  },
  primaryAction: {
    backgroundColor: COLORS.primary,
  },
  secondaryAction: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.primary,
  },
  primaryActionText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  secondaryActionText: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.primary,
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
  },
  contactIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: COLORS.primary + '15',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  contactInfo: {
    flex: 1,
  },
  contactLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginBottom: 2,
  },
  contactValue: {
    fontSize: 15,
    color: COLORS.text,
    fontWeight: '500',
  },
  bioText: {
    fontSize: 14,
    color: COLORS.text,
    lineHeight: 22,
  },
  fuelTypes: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  certifications: {
    gap: 10,
  },
  certItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  certText: {
    fontSize: 14,
    color: COLORS.text,
    flex: 1,
  },
  mapContainer: {
    height: 150,
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 12,
  },
  map: {
    flex: 1,
  },
  serviceAreaList: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
  },
  serviceAreaText: {
    flex: 1,
    fontSize: 14,
    color: COLORS.text,
    lineHeight: 22,
  },
  requestButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    paddingVertical: 16,
    borderRadius: 12,
    gap: 10,
    marginBottom: 20,
  },
  requestButtonText: {
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
