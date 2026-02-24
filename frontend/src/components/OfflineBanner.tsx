import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Animated } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../constants';

interface OfflineBannerProps {
  isOffline: boolean;
  lastSyncTime?: Date | null;
  onSyncPress?: () => void;
  isSyncing?: boolean;
}

export const OfflineBanner: React.FC<OfflineBannerProps> = ({
  isOffline,
  lastSyncTime,
  onSyncPress,
  isSyncing = false,
}) => {
  if (!isOffline) return null;

  const formatLastSync = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <Ionicons name="cloud-offline" size={18} color="#FFFFFF" />
        <View style={styles.textContainer}>
          <Text style={styles.title}>You're offline</Text>
          {lastSyncTime && (
            <Text style={styles.subtitle}>
              Last synced: {formatLastSync(lastSyncTime)}
            </Text>
          )}
        </View>
      </View>
      {onSyncPress && !isSyncing && (
        <TouchableOpacity style={styles.syncButton} onPress={onSyncPress}>
          <Ionicons name="refresh" size={16} color="#FFFFFF" />
        </TouchableOpacity>
      )}
      {isSyncing && (
        <Ionicons name="sync" size={16} color="#FFFFFF" style={styles.syncingIcon} />
      )}
    </View>
  );
};

// Compact version for inline use
export const OfflineIndicator: React.FC<{ isOffline: boolean }> = ({ isOffline }) => {
  if (!isOffline) return null;

  return (
    <View style={styles.indicator}>
      <Ionicons name="cloud-offline" size={14} color="#F59E0B" />
      <Text style={styles.indicatorText}>Offline</Text>
    </View>
  );
};

// Badge for showing cached data status
interface CachedDataBadgeProps {
  itemCount: number;
  isOffline: boolean;
}

export const CachedDataBadge: React.FC<CachedDataBadgeProps> = ({ itemCount, isOffline }) => {
  if (!isOffline || itemCount === 0) return null;

  return (
    <View style={styles.cachedBadge}>
      <Ionicons name="download" size={12} color={COLORS.primary} />
      <Text style={styles.cachedBadgeText}>{itemCount} cached</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#EF4444',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  textContainer: {
    flex: 1,
  },
  title: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  subtitle: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 2,
  },
  syncButton: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: 'rgba(255,255,255,0.2)',
  },
  syncingIcon: {
    opacity: 0.7,
  },
  indicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  indicatorText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#92400E',
  },
  cachedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: `${COLORS.primary}15`,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  cachedBadgeText: {
    fontSize: 11,
    fontWeight: '500',
    color: COLORS.primary,
  },
});
