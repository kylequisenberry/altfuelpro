import React from 'react';
import { TouchableOpacity, Text, StyleSheet, View, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { showNavigationPicker, quickNavigate, NavigationDestination } from '../utils/navigation';
import { COLORS } from '../constants';

interface NavigationButtonProps {
  destination: NavigationDestination;
  variant?: 'primary' | 'secondary' | 'icon-only';
  size?: 'small' | 'medium' | 'large';
  showPicker?: boolean; // If true, shows app picker. If false, opens default map app
  distance?: { miles: number; km: number };
}

export const NavigationButton: React.FC<NavigationButtonProps> = ({
  destination,
  variant = 'primary',
  size = 'medium',
  showPicker = false,
  distance,
}) => {
  const handlePress = async () => {
    if (showPicker) {
      await showNavigationPicker(destination);
    } else {
      await quickNavigate(destination);
    }
  };

  const getIconSize = () => {
    switch (size) {
      case 'small': return 16;
      case 'large': return 24;
      default: return 20;
    }
  };

  const getFontSize = () => {
    switch (size) {
      case 'small': return 12;
      case 'large': return 16;
      default: return 14;
    }
  };

  if (variant === 'icon-only') {
    return (
      <TouchableOpacity
        style={[styles.iconButton, styles[`iconButton_${size}`]]}
        onPress={handlePress}
        activeOpacity={0.7}
        data-testid="navigation-icon-btn"
      >
        <Ionicons name="navigate" size={getIconSize()} color={COLORS.primary} />
      </TouchableOpacity>
    );
  }

  return (
    <TouchableOpacity
      style={[
        styles.button,
        styles[`button_${variant}`],
        styles[`button_${size}`],
      ]}
      onPress={handlePress}
      activeOpacity={0.7}
      data-testid="navigation-btn"
    >
      <Ionicons 
        name="navigate" 
        size={getIconSize()} 
        color={variant === 'primary' ? '#FFFFFF' : COLORS.primary} 
      />
      <View style={styles.textContainer}>
        <Text style={[
          styles.buttonText,
          styles[`buttonText_${variant}`],
          { fontSize: getFontSize() }
        ]}>
          Get Directions
        </Text>
        {distance && (
          <Text style={[
            styles.distanceText,
            styles[`distanceText_${variant}`],
            { fontSize: getFontSize() - 2 }
          ]}>
            {distance.miles} mi ({distance.km} km)
          </Text>
        )}
      </View>
      <Ionicons 
        name="chevron-forward" 
        size={getIconSize()} 
        color={variant === 'primary' ? '#FFFFFF' : COLORS.primary} 
      />
    </TouchableOpacity>
  );
};

// Compact navigation button for list items
export const NavigationIconButton: React.FC<{
  destination: NavigationDestination;
  size?: number;
  color?: string;
}> = ({ destination, size = 20, color = COLORS.primary }) => {
  const handlePress = async () => {
    await quickNavigate(destination);
  };

  return (
    <TouchableOpacity
      style={styles.compactButton}
      onPress={handlePress}
      activeOpacity={0.7}
      hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
      data-testid="navigation-compact-btn"
    >
      <Ionicons name="navigate" size={size} color={color} />
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 12,
    gap: 8,
  },
  button_primary: {
    backgroundColor: COLORS.primary,
  },
  button_secondary: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: COLORS.primary,
  },
  button_small: {
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  button_medium: {
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  button_large: {
    paddingVertical: 16,
    paddingHorizontal: 20,
  },
  textContainer: {
    flex: 1,
  },
  buttonText: {
    fontWeight: '600',
  },
  buttonText_primary: {
    color: '#FFFFFF',
  },
  buttonText_secondary: {
    color: COLORS.primary,
  },
  distanceText: {
    marginTop: 2,
  },
  distanceText_primary: {
    color: 'rgba(255,255,255,0.8)',
  },
  distanceText_secondary: {
    color: COLORS.textSecondary,
  },
  iconButton: {
    borderRadius: 8,
    backgroundColor: `${COLORS.primary}15`,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconButton_small: {
    padding: 6,
  },
  iconButton_medium: {
    padding: 10,
  },
  iconButton_large: {
    padding: 14,
  },
  compactButton: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: `${COLORS.primary}10`,
  },
});
