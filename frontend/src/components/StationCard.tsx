import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { FuelStation } from '../types';
import { COLORS, STATUS_COLORS } from '../constants';
import { FuelTypeChip } from './FuelTypeChip';

interface StationCardProps {
  station: FuelStation;
  onPress: () => void;
  distance?: string;
}

export const StationCard: React.FC<StationCardProps> = ({ station, onPress, distance }) => {
  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Ionicons name="location" size={20} color={COLORS.primary} />
          <Text style={styles.name} numberOfLines={1}>{station.name}</Text>
        </View>
        <View style={[
          styles.statusBadge,
          { backgroundColor: STATUS_COLORS[station.status] || COLORS.textSecondary }
        ]}>
          <Text style={styles.statusText}>{station.status}</Text>
        </View>
      </View>
      
      <Text style={styles.address} numberOfLines={1}>
        {station.address}, {station.city}, {station.state}
      </Text>
      
      <View style={styles.fuelTypes}>
        {station.fuel_types.map((type) => (
          <FuelTypeChip key={type} fuelType={type} size="small" />
        ))}
      </View>
      
      <View style={styles.footer}>
        {station.hours && (
          <View style={styles.infoItem}>
            <Ionicons name="time-outline" size={14} color={COLORS.textSecondary} />
            <Text style={styles.infoText}>{station.hours}</Text>
          </View>
        )}
        {distance && (
          <View style={styles.infoItem}>
            <Ionicons name="navigate-outline" size={14} color={COLORS.primary} />
            <Text style={[styles.infoText, { color: COLORS.primary }]}>{distance}</Text>
          </View>
        )}
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 8,
  },
  name: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    flex: 1,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  statusText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  address: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginBottom: 12,
  },
  fuelTypes: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 12,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  infoItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  infoText: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
});
