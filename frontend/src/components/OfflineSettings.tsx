import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import {
  getCacheStats,
  clearCache,
  cacheStations,
  cacheServiceCenters,
  setLastSyncTime,
  getLastSyncTime,
} from '../services/offlineCache';
import { getStations, getServiceCenters } from '../services/api';
import { useNetworkStatus } from '../hooks/useNetworkStatus';
import { COLORS } from '../constants';

interface CacheStats {
  stationsCount: number;
  serviceCentersCount: number;
  lastSync: Date | null;
  cacheSize: string;
}

export const OfflineSettings: React.FC = () => {
  const { isOffline, checkConnection } = useNetworkStatus();
  const [stats, setStats] = useState<CacheStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);

  const loadStats = useCallback(async () => {
    setLoading(true);
    try {
      const cacheStats = await getCacheStats();
      setStats(cacheStats);
    } catch (error) {
      console.error('Error loading cache stats:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  const handleSyncData = async () => {
    const isConnected = await checkConnection();
    if (!isConnected) {
      Alert.alert('No Connection', 'Please connect to the internet to sync data.');
      return;
    }

    setSyncing(true);
    try {
      // Fetch and cache stations
      const stations = await getStations();
      await cacheStations(stations);

      // Fetch and cache service centers
      const centers = await getServiceCenters();
      await cacheServiceCenters(centers);

      // Update last sync time
      await setLastSyncTime();

      // Reload stats
      await loadStats();

      Alert.alert('Success', 'Offline data synced successfully!');
    } catch (error) {
      console.error('Error syncing data:', error);
      Alert.alert('Error', 'Failed to sync data. Please try again.');
    } finally {
      setSyncing(false);
    }
  };

  const handleClearCache = () => {
    Alert.alert(
      'Clear Offline Data',
      'This will remove all cached data. You will need to sync again to use offline mode.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            try {
              await clearCache();
              await loadStats();
              Alert.alert('Success', 'Offline data cleared.');
            } catch (error) {
              console.error('Error clearing cache:', error);
            }
          },
        },
      ]
    );
  };

  const formatLastSync = (date: Date) => {
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Ionicons name="cloud-download" size={24} color={COLORS.primary} />
        <Text style={styles.title}>Offline Mode</Text>
      </View>

      <Text style={styles.description}>
        Download stations and service centers for offline access in areas with poor connectivity.
      </Text>

      {/* Status Badge */}
      <View style={[styles.statusBadge, isOffline ? styles.statusOffline : styles.statusOnline]}>
        <Ionicons
          name={isOffline ? 'cloud-offline' : 'cloud-done'}
          size={16}
          color={isOffline ? '#EF4444' : '#10B981'}
        />
        <Text style={[styles.statusText, isOffline ? styles.statusTextOffline : styles.statusTextOnline]}>
          {isOffline ? 'Currently Offline' : 'Online'}
        </Text>
      </View>

      {/* Cache Statistics */}
      {loading ? (
        <ActivityIndicator style={styles.loader} color={COLORS.primary} />
      ) : stats ? (
        <View style={styles.statsContainer}>
          <View style={styles.statRow}>
            <View style={styles.statItem}>
              <Ionicons name="gas-station" size={20} color={COLORS.primary} />
              <Text style={styles.statValue}>{stats.stationsCount}</Text>
              <Text style={styles.statLabel}>Stations</Text>
            </View>
            <View style={styles.statItem}>
              <Ionicons name="construct" size={20} color={COLORS.primary} />
              <Text style={styles.statValue}>{stats.serviceCentersCount}</Text>
              <Text style={styles.statLabel}>Service Centers</Text>
            </View>
            <View style={styles.statItem}>
              <Ionicons name="folder" size={20} color={COLORS.primary} />
              <Text style={styles.statValue}>{stats.cacheSize}</Text>
              <Text style={styles.statLabel}>Storage</Text>
            </View>
          </View>

          {stats.lastSync && (
            <View style={styles.lastSyncRow}>
              <Ionicons name="time-outline" size={16} color={COLORS.textSecondary} />
              <Text style={styles.lastSyncText}>
                Last synced: {formatLastSync(stats.lastSync)}
              </Text>
            </View>
          )}
        </View>
      ) : null}

      {/* Action Buttons */}
      <View style={styles.actions}>
        <TouchableOpacity
          style={[styles.syncButton, syncing && styles.buttonDisabled]}
          onPress={handleSyncData}
          disabled={syncing || isOffline}
        >
          {syncing ? (
            <ActivityIndicator color="#FFFFFF" size="small" />
          ) : (
            <>
              <Ionicons name="sync" size={18} color="#FFFFFF" />
              <Text style={styles.syncButtonText}>
                {stats?.stationsCount ? 'Refresh Data' : 'Download for Offline'}
              </Text>
            </>
          )}
        </TouchableOpacity>

        {(stats?.stationsCount ?? 0) > 0 && (
          <TouchableOpacity style={styles.clearButton} onPress={handleClearCache}>
            <Ionicons name="trash-outline" size={18} color={COLORS.error} />
            <Text style={styles.clearButtonText}>Clear Offline Data</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Info Note */}
      <View style={styles.infoNote}>
        <Ionicons name="information-circle" size={16} color={COLORS.textSecondary} />
        <Text style={styles.infoText}>
          Cached data expires after 24 hours. Sync regularly for the latest information.
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 8,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
  },
  description: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginBottom: 16,
    lineHeight: 20,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    marginBottom: 16,
  },
  statusOnline: {
    backgroundColor: '#D1FAE5',
  },
  statusOffline: {
    backgroundColor: '#FEE2E2',
  },
  statusText: {
    fontSize: 13,
    fontWeight: '500',
  },
  statusTextOnline: {
    color: '#065F46',
  },
  statusTextOffline: {
    color: '#991B1B',
  },
  loader: {
    marginVertical: 20,
  },
  statsContainer: {
    backgroundColor: COLORS.background,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  statRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
    gap: 4,
  },
  statValue: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
    marginTop: 4,
  },
  statLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  lastSyncRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: COLORS.divider,
  },
  lastSyncText: {
    fontSize: 13,
    color: COLORS.textSecondary,
  },
  actions: {
    gap: 12,
  },
  syncButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    padding: 14,
    gap: 8,
  },
  buttonDisabled: {
    opacity: 0.7,
  },
  syncButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  clearButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'transparent',
    borderRadius: 12,
    padding: 12,
    gap: 8,
    borderWidth: 1,
    borderColor: COLORS.error,
  },
  clearButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.error,
  },
  infoNote: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: COLORS.divider,
  },
  infoText: {
    flex: 1,
    fontSize: 12,
    color: COLORS.textSecondary,
    lineHeight: 18,
  },
});
