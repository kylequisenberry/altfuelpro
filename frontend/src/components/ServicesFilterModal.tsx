import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  TextInput,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, FUEL_TYPES } from '../constants';
import { FuelTypeChip } from './FuelTypeChip';

// US States and Canadian Provinces for dropdown
const STATES_AND_PROVINCES = [
  // US States
  'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
  // Canadian Provinces
  'AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT'
];

const RADIUS_OPTIONS = [
  { label: '5 miles', value: 5 },
  { label: '10 miles', value: 10 },
  { label: '25 miles', value: 25 },
  { label: '50 miles', value: 50 },
  { label: '100 miles', value: 100 },
  { label: '250 miles', value: 250 },
];

const SERVICE_TYPE_OPTIONS = [
  { id: 'Mobile', label: 'Mobile', icon: 'car-outline', description: 'Technician comes to you' },
  { id: 'In-Shop', label: 'In-Shop', icon: 'business-outline', description: 'Visit service center' },
  { id: 'Both', label: 'Both', icon: 'swap-horizontal-outline', description: 'Mobile & In-Shop' },
];

export interface ServiceFilters {
  city?: string;
  state?: string;
  zipCode?: string;
  radius?: number;
  fuelTypes: string[];
  serviceType?: 'Mobile' | 'In-Shop' | 'Both';
}

interface ServicesFilterModalProps {
  visible: boolean;
  onClose: () => void;
  filters: ServiceFilters;
  onApplyFilters: (filters: ServiceFilters) => void;
}

export const ServicesFilterModal: React.FC<ServicesFilterModalProps> = ({
  visible,
  onClose,
  filters,
  onApplyFilters,
}) => {
  const [localFilters, setLocalFilters] = useState<ServiceFilters>(filters);
  const [showStateDropdown, setShowStateDropdown] = useState(false);
  const [showRadiusDropdown, setShowRadiusDropdown] = useState(false);

  const handleFuelTypeToggle = (fuelType: string) => {
    setLocalFilters(prev => ({
      ...prev,
      fuelTypes: prev.fuelTypes.includes(fuelType)
        ? prev.fuelTypes.filter(t => t !== fuelType)
        : [...prev.fuelTypes, fuelType],
    }));
  };

  const handleServiceTypeSelect = (serviceType: ServiceFilters['serviceType']) => {
    setLocalFilters(prev => ({
      ...prev,
      serviceType: prev.serviceType === serviceType ? undefined : serviceType,
    }));
  };

  const handleClearFilters = () => {
    setLocalFilters({
      city: '',
      state: '',
      zipCode: '',
      radius: undefined,
      fuelTypes: [],
      serviceType: undefined,
    });
  };

  const handleApply = () => {
    onApplyFilters(localFilters);
    onClose();
  };

  const activeFilterCount = [
    localFilters.city,
    localFilters.state,
    localFilters.zipCode,
    localFilters.radius,
    localFilters.fuelTypes.length > 0,
    localFilters.serviceType
  ].filter(Boolean).length;

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={onClose}
    >
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.overlay}
      >
        <View style={styles.container}>
          <SafeAreaView style={styles.safeArea}>
            {/* Header */}
            <View style={styles.header}>
              <View style={styles.headerLeft}>
                <Text style={styles.title}>Filter Services</Text>
                {activeFilterCount > 0 && (
                  <View style={styles.filterBadge}>
                    <Text style={styles.filterBadgeText}>{activeFilterCount}</Text>
                  </View>
                )}
              </View>
              <TouchableOpacity onPress={onClose}>
                <Ionicons name="close" size={24} color={COLORS.text} />
              </TouchableOpacity>
            </View>
            
            <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
              {/* Location Section */}
              <Text style={styles.sectionTitle}>Location</Text>
              
              {/* City */}
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>City</Text>
                <TextInput
                  style={styles.input}
                  value={localFilters.city}
                  onChangeText={(text) => setLocalFilters(prev => ({ ...prev, city: text }))}
                  placeholder="Enter city name"
                  placeholderTextColor={COLORS.textLight}
                />
              </View>

              {/* State */}
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>State</Text>
                <TouchableOpacity 
                  style={styles.dropdown}
                  onPress={() => setShowStateDropdown(!showStateDropdown)}
                >
                  <Text style={localFilters.state ? styles.dropdownText : styles.dropdownPlaceholder}>
                    {localFilters.state || 'Select state'}
                  </Text>
                  <Ionicons name={showStateDropdown ? "chevron-up" : "chevron-down"} size={20} color={COLORS.textSecondary} />
                </TouchableOpacity>
                {showStateDropdown && (
                  <View style={styles.dropdownList}>
                    <ScrollView nestedScrollEnabled style={{ maxHeight: 200 }}>
                      <TouchableOpacity
                        style={styles.dropdownItem}
                        onPress={() => {
                          setLocalFilters(prev => ({ ...prev, state: '' }));
                          setShowStateDropdown(false);
                        }}
                      >
                        <Text style={styles.dropdownItemText}>All States</Text>
                      </TouchableOpacity>
                      {US_STATES.map((state) => (
                        <TouchableOpacity
                          key={state}
                          style={[
                            styles.dropdownItem,
                            localFilters.state === state && styles.dropdownItemActive
                          ]}
                          onPress={() => {
                            setLocalFilters(prev => ({ ...prev, state }));
                            setShowStateDropdown(false);
                          }}
                        >
                          <Text style={[
                            styles.dropdownItemText,
                            localFilters.state === state && styles.dropdownItemTextActive
                          ]}>{state}</Text>
                        </TouchableOpacity>
                      ))}
                    </ScrollView>
                  </View>
                )}
              </View>

              {/* ZIP Code */}
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>ZIP Code</Text>
                <TextInput
                  style={styles.input}
                  value={localFilters.zipCode}
                  onChangeText={(text) => setLocalFilters(prev => ({ ...prev, zipCode: text }))}
                  placeholder="Enter ZIP code"
                  placeholderTextColor={COLORS.textLight}
                  keyboardType="numeric"
                  maxLength={5}
                />
              </View>

              {/* Radius */}
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Search Radius</Text>
                <TouchableOpacity 
                  style={styles.dropdown}
                  onPress={() => setShowRadiusDropdown(!showRadiusDropdown)}
                >
                  <Text style={localFilters.radius ? styles.dropdownText : styles.dropdownPlaceholder}>
                    {localFilters.radius ? `${localFilters.radius} miles` : 'Select radius'}
                  </Text>
                  <Ionicons name={showRadiusDropdown ? "chevron-up" : "chevron-down"} size={20} color={COLORS.textSecondary} />
                </TouchableOpacity>
                {showRadiusDropdown && (
                  <View style={styles.dropdownList}>
                    <TouchableOpacity
                      style={styles.dropdownItem}
                      onPress={() => {
                        setLocalFilters(prev => ({ ...prev, radius: undefined }));
                        setShowRadiusDropdown(false);
                      }}
                    >
                      <Text style={styles.dropdownItemText}>Any distance</Text>
                    </TouchableOpacity>
                    {RADIUS_OPTIONS.map((option) => (
                      <TouchableOpacity
                        key={option.value}
                        style={[
                          styles.dropdownItem,
                          localFilters.radius === option.value && styles.dropdownItemActive
                        ]}
                        onPress={() => {
                          setLocalFilters(prev => ({ ...prev, radius: option.value }));
                          setShowRadiusDropdown(false);
                        }}
                      >
                        <Text style={[
                          styles.dropdownItemText,
                          localFilters.radius === option.value && styles.dropdownItemTextActive
                        ]}>{option.label}</Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                )}
              </View>

              {/* Service Type Section */}
              <Text style={[styles.sectionTitle, { marginTop: 24 }]}>Service Type</Text>
              <View style={styles.serviceTypeGrid}>
                {SERVICE_TYPE_OPTIONS.map((option) => (
                  <TouchableOpacity
                    key={option.id}
                    style={[
                      styles.serviceTypeCard,
                      localFilters.serviceType === option.id && styles.serviceTypeCardActive
                    ]}
                    onPress={() => handleServiceTypeSelect(option.id as ServiceFilters['serviceType'])}
                  >
                    <Ionicons 
                      name={option.icon as any} 
                      size={24} 
                      color={localFilters.serviceType === option.id ? '#FFFFFF' : COLORS.primary} 
                    />
                    <Text style={[
                      styles.serviceTypeLabel,
                      localFilters.serviceType === option.id && styles.serviceTypeLabelActive
                    ]}>{option.label}</Text>
                    <Text style={[
                      styles.serviceTypeDesc,
                      localFilters.serviceType === option.id && styles.serviceTypeDescActive
                    ]}>{option.description}</Text>
                  </TouchableOpacity>
                ))}
              </View>

              {/* Fuel Type Section */}
              <Text style={[styles.sectionTitle, { marginTop: 24 }]}>Fuel Specialization</Text>
              <View style={styles.fuelTypes}>
                {FUEL_TYPES.map((type) => (
                  <FuelTypeChip
                    key={type.id}
                    fuelType={type.id}
                    selected={localFilters.fuelTypes.includes(type.id)}
                    onPress={() => handleFuelTypeToggle(type.id)}
                  />
                ))}
              </View>

              <View style={styles.bottomSpacer} />
            </ScrollView>
            
            {/* Footer */}
            <View style={styles.footer}>
              <TouchableOpacity style={styles.clearButton} onPress={handleClearFilters}>
                <Ionicons name="trash-outline" size={18} color={COLORS.textSecondary} />
                <Text style={styles.clearButtonText}>Clear All</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.applyButton} onPress={handleApply}>
                <Text style={styles.applyButtonText}>Apply Filters</Text>
              </TouchableOpacity>
            </View>
          </SafeAreaView>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  container: {
    backgroundColor: COLORS.surface,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '90%',
  },
  safeArea: {
    maxHeight: '100%',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.divider,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
  },
  filterBadge: {
    backgroundColor: COLORS.primary,
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 6,
  },
  filterBadgeText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  content: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 12,
  },
  inputGroup: {
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 13,
    fontWeight: '500',
    color: COLORS.textSecondary,
    marginBottom: 6,
  },
  input: {
    backgroundColor: COLORS.background,
    borderRadius: 10,
    padding: 14,
    fontSize: 15,
    color: COLORS.text,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  dropdown: {
    backgroundColor: COLORS.background,
    borderRadius: 10,
    padding: 14,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  dropdownText: {
    fontSize: 15,
    color: COLORS.text,
  },
  dropdownPlaceholder: {
    fontSize: 15,
    color: COLORS.textLight,
  },
  dropdownList: {
    backgroundColor: COLORS.surface,
    borderRadius: 10,
    marginTop: 4,
    borderWidth: 1,
    borderColor: COLORS.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  dropdownItem: {
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.divider,
  },
  dropdownItemActive: {
    backgroundColor: COLORS.primary + '15',
  },
  dropdownItemText: {
    fontSize: 14,
    color: COLORS.text,
  },
  dropdownItemTextActive: {
    color: COLORS.primary,
    fontWeight: '600',
  },
  serviceTypeGrid: {
    flexDirection: 'row',
    gap: 10,
  },
  serviceTypeCard: {
    flex: 1,
    backgroundColor: COLORS.background,
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  serviceTypeCardActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  serviceTypeLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.text,
    marginTop: 6,
  },
  serviceTypeLabelActive: {
    color: '#FFFFFF',
  },
  serviceTypeDesc: {
    fontSize: 10,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginTop: 2,
  },
  serviceTypeDescActive: {
    color: 'rgba(255, 255, 255, 0.8)',
  },
  fuelTypes: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  bottomSpacer: {
    height: 20,
  },
  footer: {
    flexDirection: 'row',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: COLORS.divider,
    gap: 12,
  },
  clearButton: {
    flex: 1,
    flexDirection: 'row',
    paddingVertical: 14,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  clearButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  applyButton: {
    flex: 1.5,
    paddingVertical: 14,
    borderRadius: 10,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
  },
  applyButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});
