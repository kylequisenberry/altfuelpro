import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { FUEL_TYPE_COLORS } from '../constants';

interface FuelTypeChipProps {
  fuelType: string;
  selected?: boolean;
  onPress?: () => void;
  size?: 'small' | 'medium';
}

const FUEL_ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
  CNG: 'flame',
  LNG: 'snow',
  Hydrogen: 'water',
  Electric: 'flash',
  Diesel: 'water-outline',
  Gasoline: 'water-outline',
  Biodiesel: 'leaf',
};

export const FuelTypeChip: React.FC<FuelTypeChipProps> = ({
  fuelType,
  selected = false,
  onPress,
  size = 'medium',
}) => {
  const color = FUEL_TYPE_COLORS[fuelType] || '#757575';
  const iconName = FUEL_ICONS[fuelType] || 'help-circle';
  const isSmall = size === 'small';

  const Container = onPress ? TouchableOpacity : View;

  return (
    <Container
      onPress={onPress}
      style={[
        styles.chip,
        isSmall && styles.chipSmall,
        selected && { backgroundColor: color },
        !selected && { borderColor: color, borderWidth: 1 },
      ]}
    >
      <Ionicons
        name={iconName}
        size={isSmall ? 12 : 16}
        color={selected ? '#FFFFFF' : color}
      />
      <Text
        style={[
          styles.text,
          isSmall && styles.textSmall,
          { color: selected ? '#FFFFFF' : color },
        ]}
      >
        {fuelType}
      </Text>
    </Container>
  );
};

const styles = StyleSheet.create({
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#FFFFFF',
    gap: 4,
  },
  chipSmall: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  text: {
    fontSize: 14,
    fontWeight: '500',
  },
  textSmall: {
    fontSize: 11,
  },
});
