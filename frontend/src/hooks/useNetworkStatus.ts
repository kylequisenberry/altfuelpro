import { useState, useEffect, useCallback } from 'react';
import NetInfo, { NetInfoState } from '@react-native-community/netinfo';
import { Platform } from 'react-native';

export interface NetworkStatus {
  isConnected: boolean;
  isInternetReachable: boolean | null;
  type: string;
  isWifi: boolean;
  isCellular: boolean;
}

export const useNetworkStatus = () => {
  const [networkStatus, setNetworkStatus] = useState<NetworkStatus>({
    isConnected: true,
    isInternetReachable: true,
    type: 'unknown',
    isWifi: false,
    isCellular: false,
  });
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    // Handle web platform differently
    if (Platform.OS === 'web') {
      const handleOnline = () => {
        setNetworkStatus(prev => ({ ...prev, isConnected: true, isInternetReachable: true }));
        setIsOffline(false);
      };
      
      const handleOffline = () => {
        setNetworkStatus(prev => ({ ...prev, isConnected: false, isInternetReachable: false }));
        setIsOffline(true);
      };

      // Check initial status
      setIsOffline(!navigator.onLine);
      setNetworkStatus(prev => ({
        ...prev,
        isConnected: navigator.onLine,
        isInternetReachable: navigator.onLine,
      }));

      window.addEventListener('online', handleOnline);
      window.addEventListener('offline', handleOffline);

      return () => {
        window.removeEventListener('online', handleOnline);
        window.removeEventListener('offline', handleOffline);
      };
    }

    // Mobile platform - use NetInfo
    const unsubscribe = NetInfo.addEventListener((state: NetInfoState) => {
      const newStatus: NetworkStatus = {
        isConnected: state.isConnected ?? false,
        isInternetReachable: state.isInternetReachable,
        type: state.type,
        isWifi: state.type === 'wifi',
        isCellular: state.type === 'cellular',
      };
      
      setNetworkStatus(newStatus);
      setIsOffline(!state.isConnected || state.isInternetReachable === false);
    });

    // Check initial status
    NetInfo.fetch().then((state) => {
      const newStatus: NetworkStatus = {
        isConnected: state.isConnected ?? false,
        isInternetReachable: state.isInternetReachable,
        type: state.type,
        isWifi: state.type === 'wifi',
        isCellular: state.type === 'cellular',
      };
      
      setNetworkStatus(newStatus);
      setIsOffline(!state.isConnected || state.isInternetReachable === false);
    });

    return () => {
      unsubscribe();
    };
  }, []);

  const checkConnection = useCallback(async (): Promise<boolean> => {
    if (Platform.OS === 'web') {
      return navigator.onLine;
    }
    
    try {
      const state = await NetInfo.fetch();
      return state.isConnected === true && state.isInternetReachable !== false;
    } catch {
      return false;
    }
  }, []);

  return {
    networkStatus,
    isOffline,
    checkConnection,
  };
};

export default useNetworkStatus;
