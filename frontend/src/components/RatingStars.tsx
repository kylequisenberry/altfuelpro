import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../constants';

interface RatingStarsProps {
  rating: number;
  reviewCount?: number;
  size?: number;
}

export const RatingStars: React.FC<RatingStarsProps> = ({ rating, reviewCount, size = 16 }) => {
  const fullStars = Math.floor(rating);
  const hasHalfStar = rating - fullStars >= 0.5;
  const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

  return (
    <View style={styles.container}>
      <View style={styles.stars}>
        {[...Array(fullStars)].map((_, i) => (
          <Ionicons key={`full-${i}`} name="star" size={size} color={COLORS.accent} />
        ))}
        {hasHalfStar && <Ionicons name="star-half" size={size} color={COLORS.accent} />}
        {[...Array(emptyStars)].map((_, i) => (
          <Ionicons key={`empty-${i}`} name="star-outline" size={size} color={COLORS.accent} />
        ))}
      </View>
      <Text style={styles.rating}>{rating.toFixed(1)}</Text>
      {reviewCount !== undefined && (
        <Text style={styles.reviews}>({reviewCount})</Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  stars: {
    flexDirection: 'row',
  },
  rating: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  reviews: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
});
