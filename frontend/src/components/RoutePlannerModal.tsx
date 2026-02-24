import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Modal,
  Alert,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { planRoute, RoutePlan, RoutePlanRequest } from '../services/api';
import { showNavigationPicker } from '../utils/navigation';
import { COLORS } from '../constants';

// Popular city coordinates for quick selection
const POPULAR_CITIES = [
  { name: 'Los Angeles, CA', lat: 34.0522, lng: -118.2437 },
  { name: 'Phoenix, AZ', lat: 33.4484, lng: -112.0740 },
  { name: 'Dallas, TX', lat: 32.7767, lng: -96.7970 },
  { name: 'Houston, TX', lat: 29.7604, lng: -95.3698 },
  { name: 'Denver, CO', lat: 39.7392, lng: -104.9903 },
  { name: 'Chicago, IL', lat: 41.8781, lng: -87.6298 },
  { name: 'Atlanta, GA', lat: 33.7490, lng: -84.3880 },
  { name: 'Miami, FL', lat: 25.7617, lng: -80.1918 },
  { name: 'Seattle, WA', lat: 47.6062, lng: -122.3321 },
  { name: 'San Francisco, CA', lat: 37.7749, lng: -122.4194 },
  { name: 'Las Vegas, NV', lat: 36.1699, lng: -115.1398 },
  { name: 'Salt Lake City, UT', lat: 40.7608, lng: -111.8910 },
];

const FUEL_TYPES = ['CNG', 'LNG', 'Hydrogen', 'Electric'];

interface RoutePlannerModalProps {
  visible: boolean;
  onClose: () => void;
}

export const RoutePlannerModal: React.FC<RoutePlannerModalProps> = ({
  visible,
  onClose,
}) => {
  const [step, setStep] = useState<'input' | 'results'>('input');
  const [loading, setLoading] = useState(false);
  const [routePlan, setRoutePlan] = useState<RoutePlan | null>(null);
  
  // Form state
  const [origin, setOrigin] = useState({ name: '', lat: 0, lng: 0 });
  const [destination, setDestination] = useState({ name: '', lat: 0, lng: 0 });
  const [fuelType, setFuelType] = useState('CNG');
  const [tankCapacity, setTankCapacity] = useState('60');
  const [mpg, setMpg] = useState('6');
  const [reserve, setReserve] = useState('15');
  
  // City picker
  const [showOriginPicker, setShowOriginPicker] = useState(false);
  const [showDestPicker, setShowDestPicker] = useState(false);

  const handlePlanRoute = useCallback(async () => {
    if (!origin.lat || !destination.lat) {
      Alert.alert('Missing Location', 'Please select both origin and destination.');
      return;
    }

    setLoading(true);
    try {
      const request: RoutePlanRequest = {
        origin_lat: origin.lat,
        origin_lng: origin.lng,
        origin_name: origin.name,
        destination_lat: destination.lat,
        destination_lng: destination.lng,
        destination_name: destination.name,
        fuel_type: fuelType,
        tank_capacity_dge: parseFloat(tankCapacity) || 60,
        mpg_dge: parseFloat(mpg) || 6,
        reserve_percentage: parseFloat(reserve) || 15,
      };

      const plan = await planRoute(request);
      setRoutePlan(plan);
      setStep('results');
    } catch (error) {
      console.error('Error planning route:', error);
      Alert.alert('Error', 'Failed to plan route. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [origin, destination, fuelType, tankCapacity, mpg, reserve]);

  const handleNavigateToStop = (stop: any) => {
    showNavigationPicker({
      latitude: stop.latitude,
      longitude: stop.longitude,
      name: stop.station_name,
      address: `${stop.address}, ${stop.city}, ${stop.state}`,
    });
  };

  const handleReset = () => {
    setStep('input');
    setRoutePlan(null);
  };

  const handleClose = () => {
    handleReset();
    onClose();
  };

  const selectCity = (city: typeof POPULAR_CITIES[0], type: 'origin' | 'destination') => {
    if (type === 'origin') {
      setOrigin({ name: city.name, lat: city.lat, lng: city.lng });
      setShowOriginPicker(false);
    } else {
      setDestination({ name: city.name, lat: city.lat, lng: city.lng });
      setShowDestPicker(false);
    }
  };

  const renderCityPicker = (type: 'origin' | 'destination') => (
    <View style={styles.cityPickerOverlay}>
      <View style={styles.cityPickerContainer}>
        <View style={styles.cityPickerHeader}>
          <Text style={styles.cityPickerTitle}>Select {type === 'origin' ? 'Origin' : 'Destination'}</Text>
          <TouchableOpacity onPress={() => type === 'origin' ? setShowOriginPicker(false) : setShowDestPicker(false)}>
            <Ionicons name="close" size={24} color={COLORS.text} />
          </TouchableOpacity>
        </View>
        <ScrollView style={styles.cityList}>
          {POPULAR_CITIES.map((city, index) => (
            <TouchableOpacity
              key={index}
              style={styles.cityItem}
              onPress={() => selectCity(city, type)}
            >
              <Ionicons name="location" size={20} color={COLORS.primary} />
              <Text style={styles.cityName}>{city.name}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>
    </View>
  );

  const renderInputForm = () => (
    <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
      {/* Origin */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>
          <Ionicons name="navigate-circle" size={18} color={COLORS.primary} /> Origin
        </Text>
        <TouchableOpacity
          style={styles.locationInput}
          onPress={() => setShowOriginPicker(true)}
        >
          <Ionicons name="location" size={20} color={origin.name ? COLORS.primary : COLORS.textSecondary} />
          <Text style={[styles.locationText, !origin.name && styles.placeholderText]}>
            {origin.name || 'Select starting city'}
          </Text>
          <Ionicons name="chevron-down" size={20} color={COLORS.textSecondary} />
        </TouchableOpacity>
      </View>

      {/* Destination */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>
          <Ionicons name="flag" size={18} color={COLORS.secondary} /> Destination
        </Text>
        <TouchableOpacity
          style={styles.locationInput}
          onPress={() => setShowDestPicker(true)}
        >
          <Ionicons name="location" size={20} color={destination.name ? COLORS.secondary : COLORS.textSecondary} />
          <Text style={[styles.locationText, !destination.name && styles.placeholderText]}>
            {destination.name || 'Select destination city'}
          </Text>
          <Ionicons name="chevron-down" size={20} color={COLORS.textSecondary} />
        </TouchableOpacity>
      </View>

      {/* Fuel Type */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>
          <Ionicons name="flash" size={18} color={COLORS.primary} /> Fuel Type
        </Text>
        <View style={styles.fuelTypeContainer}>
          {FUEL_TYPES.map((type) => (
            <TouchableOpacity
              key={type}
              style={[styles.fuelTypeButton, fuelType === type && styles.fuelTypeButtonActive]}
              onPress={() => setFuelType(type)}
            >
              <Text style={[styles.fuelTypeText, fuelType === type && styles.fuelTypeTextActive]}>
                {type}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Vehicle Settings */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>
          <Ionicons name="car" size={18} color={COLORS.primary} /> Vehicle Settings
        </Text>
        <View style={styles.vehicleSettings}>
          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>Tank Capacity (DGE)</Text>
            <TextInput
              style={styles.settingInput}
              value={tankCapacity}
              onChangeText={setTankCapacity}
              keyboardType="numeric"
              placeholder="60"
            />
          </View>
          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>MPG (DGE)</Text>
            <TextInput
              style={styles.settingInput}
              value={mpg}
              onChangeText={setMpg}
              keyboardType="numeric"
              placeholder="6"
            />
          </View>
          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>Reserve %</Text>
            <TextInput
              style={styles.settingInput}
              value={reserve}
              onChangeText={setReserve}
              keyboardType="numeric"
              placeholder="15"
            />
          </View>
        </View>
      </View>

      {/* Calculate Button */}
      <TouchableOpacity
        style={[styles.calculateButton, loading && styles.calculateButtonDisabled]}
        onPress={handlePlanRoute}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color="#FFFFFF" />
        ) : (
          <>
            <Ionicons name="map" size={20} color="#FFFFFF" />
            <Text style={styles.calculateButtonText}>Plan Route</Text>
          </>
        )}
      </TouchableOpacity>

      {/* City Pickers */}
      {showOriginPicker && renderCityPicker('origin')}
      {showDestPicker && renderCityPicker('destination')}
    </ScrollView>
  );

  const renderResults = () => {
    if (!routePlan) return null;

    return (
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Route Summary */}
        <View style={styles.summaryCard}>
          <View style={styles.summaryHeader}>
            <Text style={styles.summaryTitle}>Route Summary</Text>
            <TouchableOpacity onPress={handleReset} style={styles.editButton}>
              <Ionicons name="pencil" size={16} color={COLORS.primary} />
              <Text style={styles.editButtonText}>Edit</Text>
            </TouchableOpacity>
          </View>
          
          <View style={styles.routeEndpoints}>
            <View style={styles.endpoint}>
              <Ionicons name="navigate-circle" size={24} color={COLORS.primary} />
              <Text style={styles.endpointText}>{routePlan.origin.name}</Text>
            </View>
            <Ionicons name="arrow-down" size={20} color={COLORS.textSecondary} />
            <View style={styles.endpoint}>
              <Ionicons name="flag" size={24} color={COLORS.secondary} />
              <Text style={styles.endpointText}>{routePlan.destination.name}</Text>
            </View>
          </View>

          <View style={styles.statsGrid}>
            <View style={styles.statItem}>
              <Ionicons name="speedometer" size={24} color={COLORS.primary} />
              <Text style={styles.statValue}>{routePlan.total_distance_miles} mi</Text>
              <Text style={styles.statLabel}>{routePlan.total_distance_km} km</Text>
            </View>
            <View style={styles.statItem}>
              <Ionicons name="time" size={24} color={COLORS.primary} />
              <Text style={styles.statValue}>{routePlan.estimated_total_time_hours.toFixed(1)} hrs</Text>
              <Text style={styles.statLabel}>Est. Time</Text>
            </View>
            <View style={styles.statItem}>
              <Ionicons name="water" size={24} color={COLORS.primary} />
              <Text style={styles.statValue}>{routePlan.total_fuel_needed_dge} DGE</Text>
              <Text style={styles.statLabel}>Fuel Needed</Text>
            </View>
            <View style={styles.statItem}>
              <Ionicons name="cash" size={24} color={COLORS.primary} />
              <Text style={styles.statValue}>${routePlan.estimated_fuel_cost}</Text>
              <Text style={styles.statLabel}>Est. Cost</Text>
            </View>
          </View>
        </View>

        {/* Warnings */}
        {routePlan.warnings.length > 0 && (
          <View style={styles.warningsCard}>
            {routePlan.warnings.map((warning, index) => (
              <View key={index} style={styles.warningItem}>
                <Ionicons name="alert-circle" size={18} color="#F59E0B" />
                <Text style={styles.warningText}>{warning}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Fuel Stops */}
        <View style={styles.stopsSection}>
          <Text style={styles.sectionTitle}>
            <Ionicons name="gas-station" size={18} color={COLORS.primary} /> 
            {routePlan.fuel_stops.length > 0 ? ` Fuel Stops (${routePlan.fuel_stops.length})` : ' No Fuel Stops Needed'}
          </Text>
          
          {routePlan.fuel_stops.length === 0 ? (
            <View style={styles.noStopsCard}>
              <Ionicons name="checkmark-circle" size={48} color={COLORS.primary} />
              <Text style={styles.noStopsText}>Your trip is within vehicle range!</Text>
              <Text style={styles.noStopsSubtext}>No refueling stops required.</Text>
            </View>
          ) : (
            routePlan.fuel_stops.map((stop, index) => (
              <View key={index} style={styles.stopCard}>
                <View style={styles.stopHeader}>
                  <View style={styles.stopNumber}>
                    <Text style={styles.stopNumberText}>{index + 1}</Text>
                  </View>
                  <View style={styles.stopInfo}>
                    <Text style={styles.stopName}>{stop.station_name}</Text>
                    <Text style={styles.stopAddress}>{stop.city}, {stop.state}</Text>
                  </View>
                  <TouchableOpacity
                    style={styles.navigateButton}
                    onPress={() => handleNavigateToStop(stop)}
                  >
                    <Ionicons name="navigate" size={20} color="#FFFFFF" />
                  </TouchableOpacity>
                </View>
                <View style={styles.stopDetails}>
                  <View style={styles.stopDetail}>
                    <Text style={styles.stopDetailLabel}>Distance</Text>
                    <Text style={styles.stopDetailValue}>{stop.distance_from_start} mi from start</Text>
                  </View>
                  <View style={styles.stopDetail}>
                    <Text style={styles.stopDetailLabel}>Fuel Needed</Text>
                    <Text style={styles.stopDetailValue}>{stop.estimated_fuel_needed} DGE</Text>
                  </View>
                  {stop.access_hours && (
                    <View style={styles.stopDetail}>
                      <Text style={styles.stopDetailLabel}>Hours</Text>
                      <Text style={styles.stopDetailValue} numberOfLines={1}>{stop.access_hours}</Text>
                    </View>
                  )}
                </View>
              </View>
            ))
          )}
        </View>

        {/* Route Segments */}
        <View style={styles.segmentsSection}>
          <Text style={styles.sectionTitle}>
            <Ionicons name="git-branch" size={18} color={COLORS.primary} /> Route Segments
          </Text>
          {routePlan.segments.map((segment, index) => (
            <View key={index} style={styles.segmentItem}>
              <View style={styles.segmentDot} />
              <View style={styles.segmentContent}>
                <Text style={styles.segmentText}>
                  {segment.from_location} → {segment.to_location}
                </Text>
                <Text style={styles.segmentDetails}>
                  {segment.distance_miles} mi • {segment.estimated_time_hours.toFixed(1)} hrs
                </Text>
              </View>
            </View>
          ))}
        </View>
      </ScrollView>
    );
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={handleClose}
    >
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={handleClose} style={styles.closeButton}>
            <Ionicons name="close" size={24} color={COLORS.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Route Planner</Text>
          <View style={{ width: 40 }} />
        </View>

        {step === 'input' ? renderInputForm() : renderResults()}
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.divider,
  },
  closeButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 12,
  },
  locationInput: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.divider,
    gap: 12,
  },
  locationText: {
    flex: 1,
    fontSize: 16,
    color: COLORS.text,
  },
  placeholderText: {
    color: COLORS.textSecondary,
  },
  fuelTypeContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  fuelTypeButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.divider,
  },
  fuelTypeButtonActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  fuelTypeText: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.text,
  },
  fuelTypeTextActive: {
    color: '#FFFFFF',
  },
  vehicleSettings: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 16,
    gap: 12,
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  settingLabel: {
    fontSize: 14,
    color: COLORS.text,
  },
  settingInput: {
    backgroundColor: COLORS.background,
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
    width: 80,
    textAlign: 'center',
    fontSize: 14,
    color: COLORS.text,
    borderWidth: 1,
    borderColor: COLORS.divider,
  },
  calculateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    padding: 16,
    gap: 8,
    marginTop: 8,
    marginBottom: 32,
  },
  calculateButtonDisabled: {
    opacity: 0.7,
  },
  calculateButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  cityPickerOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    padding: 20,
  },
  cityPickerContainer: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    maxHeight: '80%',
  },
  cityPickerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.divider,
  },
  cityPickerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
  },
  cityList: {
    maxHeight: 400,
  },
  cityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    gap: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.divider,
  },
  cityName: {
    fontSize: 16,
    color: COLORS.text,
  },
  // Results styles
  summaryCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  summaryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  summaryTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
  },
  editButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  editButtonText: {
    fontSize: 14,
    color: COLORS.primary,
  },
  routeEndpoints: {
    alignItems: 'center',
    marginBottom: 20,
    gap: 8,
  },
  endpoint: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  endpointText: {
    fontSize: 16,
    fontWeight: '500',
    color: COLORS.text,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  statItem: {
    flex: 1,
    minWidth: '45%',
    alignItems: 'center',
    padding: 12,
    backgroundColor: COLORS.background,
    borderRadius: 12,
  },
  statValue: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.text,
    marginTop: 8,
  },
  statLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  warningsCard: {
    backgroundColor: '#FEF3C7',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    gap: 8,
  },
  warningItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
  },
  warningText: {
    flex: 1,
    fontSize: 14,
    color: '#92400E',
  },
  stopsSection: {
    marginBottom: 24,
  },
  noStopsCard: {
    alignItems: 'center',
    padding: 32,
    backgroundColor: COLORS.surface,
    borderRadius: 16,
  },
  noStopsText: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
    marginTop: 16,
  },
  noStopsSubtext: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginTop: 4,
  },
  stopCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  stopHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  stopNumber: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stopNumberText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  stopInfo: {
    flex: 1,
  },
  stopName: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  stopAddress: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  navigateButton: {
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    padding: 10,
  },
  stopDetails: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 16,
  },
  stopDetail: {
    minWidth: '40%',
  },
  stopDetailLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  stopDetailValue: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.text,
    marginTop: 2,
  },
  segmentsSection: {
    marginBottom: 32,
  },
  segmentItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    marginBottom: 16,
  },
  segmentDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: COLORS.primary,
    marginTop: 4,
  },
  segmentContent: {
    flex: 1,
  },
  segmentText: {
    fontSize: 14,
    color: COLORS.text,
  },
  segmentDetails: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
});
