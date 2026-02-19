export interface FuelStation {
  id: string;
  name: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  latitude: number;
  longitude: number;
  fuel_types: string[];
  phone?: string;
  hours?: string;
  amenities: string[];
  card_accepted: string[];
  last_updated?: string;
  status: string;
  prices?: Record<string, number>;
  network?: string;
  access_type?: string;
  ev_connector_types?: string[];
  ev_network?: string;
}

export interface Regulation {
  id: string;
  title: string;
  description: string;
  fuel_types: string[];
  category: string;
  jurisdiction: string;
  state?: string;
  code_reference?: string;
  effective_date?: string;
  summary: string;
  pdf_url?: string;
}

export interface ServiceCenter {
  id: string;
  name: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  latitude: number;
  longitude: number;
  phone: string;
  email?: string;
  website?: string;
  fuel_specializations: string[];
  service_type: string;
  certifications: string[];
  rating: number;
  review_count: number;
  hours?: string;
  services_offered: string[];
}

export interface Inspector {
  id: string;
  name: string;
  company?: string;
  phone: string;
  email: string;
  city: string;
  state: string;
  latitude: number;
  longitude: number;
  fuel_specializations: string[];
  certifications: string[];
  license_number?: string;
  years_experience: number;
  service_area: string[];
  rating: number;
  review_count: number;
  bio?: string;
}

export interface UserProfile {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  preferred_fuel_types: string[];
  favorite_stations: string[];
  created_at: string;
}

export interface FuelType {
  id: string;
  name: string;
  icon: string;
  afdc_code?: string;
}

export interface FuelSystemProvider {
  id: string;
  name: string;
  logo_url?: string;
  description: string;
  fuel_types: string[];
  website: string;
  support_url?: string;
  documentation_url?: string;
  phone?: string;
  email?: string;
  headquarters?: string;
  products: string[];
  formerly_known_as?: string;
  status?: string;  // "active", "discontinued", etc.
  locations?: Record<string, string>;  // Additional location details
}

export interface InspectorLookupLinks {
  afvi: {
    name: string;
    description: string;
    url: string;
    certifications: string[];
  };
  csa: {
    name: string;
    description: string;
    url: string;
    certifications: string[];
  };
}
