import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Linking,
  Alert,
  Dimensions,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import MapView, { Marker, PROVIDER_DEFAULT } from 'react-native-maps';
import { getStation, addFavoriteStation, removeFavoriteStation, getProfile } from '../../src/services/api';
import { FuelStation } from '../../src/types';
import { FuelTypeChip } from '../../src/components/FuelTypeChip';
import { LoadingSpinner } from '../../src/components/LoadingSpinner';
import { COLORS, STATUS_COLORS, FUEL_TYPE_COLORS } from '../../src/constants';

const { width } = Dimensions.get('window');

export default function StationDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [station, setStation] = useState<FuelStation | null>(null);
  const [loading, setLoading] = useState(true);
  const [isFavorite, setIsFavorite] = useState(false);

  useEffect(() => {
    fetchStationAndProfile();
  }, [id]);

  const fetchStationAndProfile = async () => {
    try {
      const [stationData, profileData] = await Promise.all([
        getStation(id as string),
        getProfile(),
      ]);
      setStation(stationData);
      setIsFavorite(profileData.favorite_stations.includes(id as string));
    } catch (error) {
      console.error('Error fetching station:', error);
      Alert.alert('Error', 'Failed to load station details');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleFavorite = async () => {
    try {
      if (isFavorite) {
        await removeFavoriteStation(id as string);
      } else {
        await addFavoriteStation(id as string);
      }
      setIsFavorite(!isFavorite);
    } catch (error) {
      console.error('Error toggling favorite:', error);
    }
  };

  const handleCall = () => {
    if (station?.phone) {
      Linking.openURL(`tel:${station.phone}`);
    }
  };

  const handleDirections = () => {
    if (station) {
      const url = `https://www.google.com/maps/dir/?api=1&destination=${station.latitude},${station.longitude}`;
      Linking.openURL(url);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading station details..." />;
  }

  if (!station) {
    return (
      <View style={styles.errorContainer}>
        <Ionicons name="alert-circle-outline" size={48} color={COLORS.error} />
        <Text style={styles.errorText}>Station not found</Text>
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
        <MapView
          style={styles.map}
          provider={PROVIDER_DEFAULT}
          initialRegion={{
            latitude: station.latitude,
            longitude: station.longitude,
            latitudeDelta: 0.01,
            longitudeDelta: 0.01,
          }}
          scrollEnabled={false}
          zoomEnabled={false}
        >
          <Marker
            coordinate={{
              latitude: station.latitude,
              longitude: station.longitude,
            }}
            pinColor={FUEL_TYPE_COLORS[station.fuel_types[0]] || COLORS.primary}
          />
        </MapView>
        
        {/* Favorite Button */}
        <TouchableOpacity
          style={styles.favoriteButton}
          onPress={handleToggleFavorite}
        >
          <Ionicons
            name={isFavorite ? 'heart' : 'heart-outline'}
            size={24}
            color={isFavorite ? COLORS.error : COLORS.text}
          />
        </TouchableOpacity>
      </View>

      {/* Station Info */}
      <View style={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.titleRow}>
            <Text style={styles.name}>{station.name}</Text>
            <View style={[
              styles.statusBadge,
              { backgroundColor: STATUS_COLORS[station.status] || COLORS.textSecondary }
            ]}>
              <Text style={styles.statusText}>{station.status}</Text>
            </View>
          </View>
          <Text style={styles.address}>
            {station.address}, {station.city}, {station.state} {station.zip_code}
          </Text>
        </View>

        {/* Action Buttons */}
        <View style={styles.actionButtons}>
          <TouchableOpacity style={styles.actionButton} onPress={handleDirections}>
            <Ionicons name="navigate" size={22} color="#FFFFFF" />
            <Text style={styles.actionButtonText}>Directions</Text>
          </TouchableOpacity>
          {station.phone && (
            <TouchableOpacity style={[styles.actionButton, styles.callButton]} onPress={handleCall}>
              <Ionicons name="call" size={22} color="#FFFFFF" />
              <Text style={styles.actionButtonText}>Call</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Fuel Types */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Available Fuels</Text>
          <View style={styles.fuelTypes}>
            {station.fuel_types.map((type) => (
              <View key={type} style={styles.fuelItem}>
                <FuelTypeChip fuelType={type} selected />
                {station.prices && station.prices[type] && (
                  <Text style={styles.fuelPrice}>
                    ${station.prices[type].toFixed(2)}
                    <Text style={styles.priceUnit}>
                      {type === 'Electric' ? '/kWh' : '/gal'}
                    </Text>
                  </Text>
                )}
              </View>
            ))}
          </View>
        </View>

        {/* Hours */}
        {station.hours && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Hours</Text>
            <View style={styles.infoRow}>
              <Ionicons name="time-outline" size={20} color={COLORS.primary} />
              <Text style={styles.infoText}>{station.hours}</Text>
            </View>
          </View>
        )}

        {/* Amenities */}
        {station.amenities.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Amenities</Text>
            <View style={styles.amenitiesGrid}>
              {station.amenities.map((amenity, index) => (
                <View key={index} style={styles.amenityItem}>
                  <Ionicons name="checkmark-circle" size={16} color={COLORS.success} />
                  <Text style={styles.amenityText}>{amenity}</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Payment Methods */}
        {station.card_accepted.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Accepted Payments</Text>
            <View style={styles.paymentMethods}>
              {station.card_accepted.map((card, index) => (
                <View key={index} style={styles.paymentChip}>
                  <Ionicons name="card" size={14} color={COLORS.secondary} />
                  <Text style={styles.paymentText}>{card}</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Last Updated */}
        <View style={styles.lastUpdated}>
          <Ionicons name="refresh" size={14} color={COLORS.textLight} />
          <Text style={styles.lastUpdatedText}>
            Last updated: {new Date(station.last_updated).toLocaleDateString()}
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
  mapContainer: {
    height: 200,
    position: 'relative',
  },
  map: {
    flex: 1,
  },
  favoriteButton: {
    position: 'absolute',
    top: 12,
    right: 12,
    backgroundColor: COLORS.surface,
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  content: {
    padding: 16,
  },
  header: {
    marginBottom: 16,
  },
  titleRow: {
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
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  address: {
    fontSize: 14,
    color: COLORS.textSecondary,
    lineHeight: 20,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 24,
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
  callButton: {
    backgroundColor: COLORS.secondary,
  },
  actionButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
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
  fuelTypes: {
    gap: 12,
  },
  fuelItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  fuelPrice: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.primary,
  },
  priceUnit: {
    fontSize: 12,
    fontWeight: '400',
    color: COLORS.textSecondary,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  infoText: {
    fontSize: 15,
    color: COLORS.text,
  },
  amenitiesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  amenityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    width: '45%',
  },
  amenityText: {
    fontSize: 14,
    color: COLORS.text,
  },
  paymentMethods: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  paymentChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.secondary + '15',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
    gap: 6,
  },
  paymentText: {
    fontSize: 13,
    color: COLORS.secondary,
    fontWeight: '500',
  },
  lastUpdated: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 8,
  },
  lastUpdatedText: {
    fontSize: 12,
    color: COLORS.textLight,
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
