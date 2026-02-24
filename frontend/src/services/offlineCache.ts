import AsyncStorage from '@react-native-async-storage/async-storage';
import { FuelStation, ServiceCenter } from '../types';

// Cache keys
const CACHE_KEYS = {
  STATIONS: '@fuelpoint_stations',
  SERVICE_CENTERS: '@fuelpoint_service_centers',
  NEARBY_STATIONS: '@fuelpoint_nearby_stations',
  NEARBY_SERVICE_CENTERS: '@fuelpoint_nearby_service_centers',
  LAST_SYNC: '@fuelpoint_last_sync',
  USER_LOCATION: '@fuelpoint_user_location',
};

// Cache expiration time (24 hours)
const CACHE_EXPIRATION_MS = 24 * 60 * 60 * 1000;

interface CachedData<T> {
  data: T;
  timestamp: number;
  location?: { latitude: number; longitude: number };
}

// Generic cache functions
export const setCache = async <T>(key: string, data: T, location?: { latitude: number; longitude: number }): Promise<void> => {
  try {
    const cachedData: CachedData<T> = {
      data,
      timestamp: Date.now(),
      location,
    };
    await AsyncStorage.setItem(key, JSON.stringify(cachedData));
  } catch (error) {
    console.error(`Error setting cache for ${key}:`, error);
  }
};

export const getCache = async <T>(key: string): Promise<CachedData<T> | null> => {
  try {
    const cached = await AsyncStorage.getItem(key);
    if (!cached) return null;
    return JSON.parse(cached) as CachedData<T>;
  } catch (error) {
    console.error(`Error getting cache for ${key}:`, error);
    return null;
  }
};

export const isCacheValid = (timestamp: number): boolean => {
  return Date.now() - timestamp < CACHE_EXPIRATION_MS;
};

export const clearCache = async (key?: string): Promise<void> => {
  try {
    if (key) {
      await AsyncStorage.removeItem(key);
    } else {
      // Clear all FuelPoint caches
      const keys = Object.values(CACHE_KEYS);
      await AsyncStorage.multiRemove(keys);
    }
  } catch (error) {
    console.error('Error clearing cache:', error);
  }
};

// Station-specific cache functions
export const cacheStations = async (stations: FuelStation[]): Promise<void> => {
  await setCache(CACHE_KEYS.STATIONS, stations);
};

export const getCachedStations = async (): Promise<FuelStation[] | null> => {
  const cached = await getCache<FuelStation[]>(CACHE_KEYS.STATIONS);
  if (cached && isCacheValid(cached.timestamp)) {
    return cached.data;
  }
  return null;
};

export const cacheNearbyStations = async (
  stations: FuelStation[],
  location: { latitude: number; longitude: number }
): Promise<void> => {
  await setCache(CACHE_KEYS.NEARBY_STATIONS, stations, location);
};

export const getCachedNearbyStations = async (): Promise<{
  stations: FuelStation[];
  location: { latitude: number; longitude: number };
} | null> => {
  const cached = await getCache<FuelStation[]>(CACHE_KEYS.NEARBY_STATIONS);
  if (cached && isCacheValid(cached.timestamp) && cached.location) {
    return {
      stations: cached.data,
      location: cached.location,
    };
  }
  return null;
};

// Service center-specific cache functions
export const cacheServiceCenters = async (centers: ServiceCenter[]): Promise<void> => {
  await setCache(CACHE_KEYS.SERVICE_CENTERS, centers);
};

export const getCachedServiceCenters = async (): Promise<ServiceCenter[] | null> => {
  const cached = await getCache<ServiceCenter[]>(CACHE_KEYS.SERVICE_CENTERS);
  if (cached && isCacheValid(cached.timestamp)) {
    return cached.data;
  }
  return null;
};

export const cacheNearbyServiceCenters = async (
  centers: ServiceCenter[],
  location: { latitude: number; longitude: number }
): Promise<void> => {
  await setCache(CACHE_KEYS.NEARBY_SERVICE_CENTERS, centers, location);
};

export const getCachedNearbyServiceCenters = async (): Promise<{
  centers: ServiceCenter[];
  location: { latitude: number; longitude: number };
} | null> => {
  const cached = await getCache<ServiceCenter[]>(CACHE_KEYS.NEARBY_SERVICE_CENTERS);
  if (cached && isCacheValid(cached.timestamp) && cached.location) {
    return {
      centers: cached.data,
      location: cached.location,
    };
  }
  return null;
};

// Last sync time
export const setLastSyncTime = async (): Promise<void> => {
  await AsyncStorage.setItem(CACHE_KEYS.LAST_SYNC, Date.now().toString());
};

export const getLastSyncTime = async (): Promise<Date | null> => {
  try {
    const timestamp = await AsyncStorage.getItem(CACHE_KEYS.LAST_SYNC);
    if (timestamp) {
      return new Date(parseInt(timestamp, 10));
    }
    return null;
  } catch (error) {
    console.error('Error getting last sync time:', error);
    return null;
  }
};

// User location for offline reference
export const cacheUserLocation = async (location: { latitude: number; longitude: number }): Promise<void> => {
  await AsyncStorage.setItem(CACHE_KEYS.USER_LOCATION, JSON.stringify(location));
};

export const getCachedUserLocation = async (): Promise<{ latitude: number; longitude: number } | null> => {
  try {
    const location = await AsyncStorage.getItem(CACHE_KEYS.USER_LOCATION);
    if (location) {
      return JSON.parse(location);
    }
    return null;
  } catch (error) {
    console.error('Error getting cached user location:', error);
    return null;
  }
};

// Get cache statistics
export const getCacheStats = async (): Promise<{
  stationsCount: number;
  serviceCentersCount: number;
  lastSync: Date | null;
  cacheSize: string;
}> => {
  const stations = await getCachedStations();
  const centers = await getCachedServiceCenters();
  const lastSync = await getLastSyncTime();
  
  // Estimate cache size
  let totalSize = 0;
  const keys = Object.values(CACHE_KEYS);
  for (const key of keys) {
    const data = await AsyncStorage.getItem(key);
    if (data) {
      totalSize += data.length;
    }
  }
  
  const cacheSizeKB = (totalSize / 1024).toFixed(1);
  
  return {
    stationsCount: stations?.length || 0,
    serviceCentersCount: centers?.length || 0,
    lastSync,
    cacheSize: `${cacheSizeKB} KB`,
  };
};

export { CACHE_KEYS };
