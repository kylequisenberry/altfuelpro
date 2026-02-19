import axios from 'axios';
import { FuelStation, Regulation, ServiceCenter, Inspector, UserProfile, FuelType } from '../types';

// API_BASE uses environment variable or falls back to relative path (same origin)
// This works for both development and production deployments
const API_BASE = process.env.EXPO_PUBLIC_BACKEND_URL ?? '';

const api = axios.create({
  baseURL: `${API_BASE}/api`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Fuel Stations
export const getStations = async (filters?: {
  fuel_type?: string;
  state?: string;
  city?: string;
  status?: string;
}): Promise<FuelStation[]> => {
  const params = new URLSearchParams();
  if (filters?.fuel_type) params.append('fuel_type', filters.fuel_type);
  if (filters?.state) params.append('state', filters.state);
  if (filters?.city) params.append('city', filters.city);
  if (filters?.status) params.append('status', filters.status);
  
  const response = await api.get(`/stations?${params.toString()}`);
  return response.data;
};

export const getStation = async (id: string): Promise<FuelStation> => {
  const response = await api.get(`/stations/${id}`);
  return response.data;
};

// Regulations
export const getRegulations = async (filters?: {
  fuel_type?: string;
  category?: string;
  jurisdiction?: string;
  state?: string;
}): Promise<Regulation[]> => {
  const params = new URLSearchParams();
  if (filters?.fuel_type) params.append('fuel_type', filters.fuel_type);
  if (filters?.category) params.append('category', filters.category);
  if (filters?.jurisdiction) params.append('jurisdiction', filters.jurisdiction);
  if (filters?.state) params.append('state', filters.state);
  
  const response = await api.get(`/regulations?${params.toString()}`);
  return response.data;
};

export const getRegulation = async (id: string): Promise<Regulation> => {
  const response = await api.get(`/regulations/${id}`);
  return response.data;
};

// Service Centers
export const getServiceCenters = async (filters?: {
  fuel_type?: string;
  service_type?: string;
  state?: string;
  city?: string;
}): Promise<ServiceCenter[]> => {
  const params = new URLSearchParams();
  if (filters?.fuel_type) params.append('fuel_type', filters.fuel_type);
  if (filters?.service_type) params.append('service_type', filters.service_type);
  if (filters?.state) params.append('state', filters.state);
  if (filters?.city) params.append('city', filters.city);
  
  const response = await api.get(`/service-centers?${params.toString()}`);
  return response.data;
};

export const getServiceCenter = async (id: string): Promise<ServiceCenter> => {
  const response = await api.get(`/service-centers/${id}`);
  return response.data;
};

// Inspectors
export const getInspectors = async (filters?: {
  fuel_type?: string;
  state?: string;
  city?: string;
}): Promise<Inspector[]> => {
  const params = new URLSearchParams();
  if (filters?.fuel_type) params.append('fuel_type', filters.fuel_type);
  if (filters?.state) params.append('state', filters.state);
  if (filters?.city) params.append('city', filters.city);
  
  const response = await api.get(`/inspectors?${params.toString()}`);
  return response.data;
};

export const getInspector = async (id: string): Promise<Inspector> => {
  const response = await api.get(`/inspectors/${id}`);
  return response.data;
};

// User Profile
export const getProfile = async (): Promise<UserProfile> => {
  const response = await api.get('/profile');
  return response.data;
};

export const updateProfile = async (data: Partial<UserProfile>): Promise<UserProfile> => {
  const response = await api.put('/profile', data);
  return response.data;
};

export const addFavoriteStation = async (stationId: string): Promise<void> => {
  await api.post(`/profile/favorites/${stationId}`);
};

export const removeFavoriteStation = async (stationId: string): Promise<void> => {
  await api.delete(`/profile/favorites/${stationId}`);
};

// Fuel Types
export const getFuelTypes = async (): Promise<FuelType[]> => {
  const response = await api.get('/fuel-types');
  return response.data;
};

export default api;
