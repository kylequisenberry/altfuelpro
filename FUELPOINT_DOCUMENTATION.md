# FuelPoint Navigator - Complete Source Code Documentation

## Project Overview
FuelPoint Navigator is a comprehensive mobile application for the Alternative Fuels market built with:
- **Frontend**: Expo/React Native with TypeScript
- **Backend**: FastAPI with Python
- **Database**: MongoDB

## Project Structure

```
fuelpoint-navigator/
├── backend/
│   ├── .env                    # Environment variables
│   ├── requirements.txt        # Python dependencies
│   └── server.py              # FastAPI server with all endpoints
│
├── frontend/
│   ├── .env                    # Expo environment variables
│   ├── package.json           # Node.js dependencies
│   ├── app.json               # Expo configuration
│   ├── tsconfig.json          # TypeScript configuration
│   │
│   ├── app/                   # Expo Router screens (file-based routing)
│   │   ├── _layout.tsx        # Tab navigation layout
│   │   ├── index.tsx          # Stations screen (Map/List)
│   │   ├── regulations.tsx    # Regulations library
│   │   ├── services.tsx       # Service centers directory
│   │   ├── inspectors.tsx     # Certified inspectors
│   │   ├── profile.tsx        # User profile
│   │   ├── station/[id].tsx   # Station detail screen
│   │   ├── regulation/[id].tsx # Regulation detail screen
│   │   ├── service/[id].tsx   # Service center detail screen
│   │   └── inspector/[id].tsx # Inspector detail screen
│   │
│   └── src/
│       ├── types/index.ts     # TypeScript type definitions
│       ├── constants/index.ts # Colors and constants
│       ├── services/api.ts    # API client
│       └── components/        # Reusable UI components
│           ├── MapWrapper.tsx
│           ├── FuelTypeChip.tsx
│           ├── StationCard.tsx
│           ├── RatingStars.tsx
│           ├── FilterModal.tsx
│           └── LoadingSpinner.tsx
```

## Installation & Setup

### Prerequisites
- Node.js 18+
- Python 3.9+
- MongoDB 6.0+
- Expo CLI

### Backend Setup

1. Create virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
# Create .env file
MONGO_URL="mongodb://localhost:27017"
DB_NAME="fuelpoint_db"
```

4. Run the server:
```bash
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
yarn install
# or
npm install
```

2. Configure environment:
```bash
# Create .env file
EXPO_PUBLIC_BACKEND_URL=http://localhost:8001
```

3. Start the development server:
```bash
npx expo start
```

## API Endpoints

### Fuel Stations
- `GET /api/stations` - List all stations (supports filters: fuel_type, state, city, status)
- `GET /api/stations/{id}` - Get station details

### Regulations
- `GET /api/regulations` - List all regulations (supports filters: fuel_type, category, jurisdiction, state)
- `GET /api/regulations/{id}` - Get regulation details

### Service Centers
- `GET /api/service-centers` - List all service centers (supports filters: fuel_type, service_type, state, city)
- `GET /api/service-centers/{id}` - Get service center details

### Inspectors
- `GET /api/inspectors` - List all inspectors (supports filters: fuel_type, state, city)
- `GET /api/inspectors/{id}` - Get inspector details

### User Profile
- `GET /api/profile` - Get user profile
- `PUT /api/profile` - Update user profile
- `POST /api/profile/favorites/{station_id}` - Add station to favorites
- `DELETE /api/profile/favorites/{station_id}` - Remove station from favorites

### Utility
- `GET /api/health` - Health check
- `GET /api/fuel-types` - Get list of fuel types

## Web Deployment

To deploy this as a web application:

### Option 1: Expo Web Build
```bash
cd frontend
npx expo export --platform web
# This creates a 'dist' folder with static files
```

### Option 2: Using a Standard Web Server
1. Build the web version:
```bash
npx expo export --platform web
```

2. Deploy the `dist` folder to any static hosting service:
   - Vercel
   - Netlify
   - AWS S3 + CloudFront
   - Nginx

### Option 3: Create a React Web Version
If you need a pure React web app, you can:
1. Create a new React/Next.js project
2. Copy the component logic and adapt styles
3. Use the same API endpoints

Example React component structure:
```jsx
// Example: Converting to React Web
import React from 'react';
import './StationCard.css';

const StationCard = ({ station, onClick }) => {
  return (
    <div className="station-card" onClick={onClick}>
      <h3>{station.name}</h3>
      <p>{station.address}, {station.city}, {station.state}</p>
      <div className="fuel-types">
        {station.fuel_types.map(type => (
          <span key={type} className={`fuel-chip ${type.toLowerCase()}`}>
            {type}
          </span>
        ))}
      </div>
    </div>
  );
};
```

## Embedding in an Existing Website

### Method 1: iframe Embedding
```html
<iframe 
  src="https://your-expo-web-url.com" 
  width="100%" 
  height="800px"
  frameborder="0">
</iframe>
```

### Method 2: API-Only Integration
Use the backend API directly in your existing website:

```javascript
// Example: Fetching stations in vanilla JavaScript
async function fetchStations(filters = {}) {
  const params = new URLSearchParams(filters);
  const response = await fetch(`https://your-api-url.com/api/stations?${params}`);
  return response.json();
}

// Example: Display stations on a map
async function displayStationsOnMap() {
  const stations = await fetchStations({ fuel_type: 'CNG' });
  stations.forEach(station => {
    // Add marker to your map (Google Maps, Leaflet, etc.)
    addMarker(station.latitude, station.longitude, station.name);
  });
}
```

### Method 3: React Component Library
Create a package of reusable React components:

```jsx
// FuelPointWidget.jsx
import React, { useState, useEffect } from 'react';

export const StationLocator = ({ apiUrl, fuelType }) => {
  const [stations, setStations] = useState([]);

  useEffect(() => {
    fetch(`${apiUrl}/api/stations?fuel_type=${fuelType}`)
      .then(res => res.json())
      .then(data => setStations(data));
  }, [apiUrl, fuelType]);

  return (
    <div className="station-locator">
      {stations.map(station => (
        <div key={station.id} className="station-item">
          <h4>{station.name}</h4>
          <p>{station.address}</p>
        </div>
      ))}
    </div>
  );
};
```

## Color Scheme

```javascript
const COLORS = {
  primary: '#2E7D32',      // Green
  primaryLight: '#4CAF50',
  primaryDark: '#1B5E20',
  secondary: '#1976D2',    // Blue
  accent: '#FF9800',       // Orange
  background: '#F5F5F5',
  surface: '#FFFFFF',
  error: '#D32F2F',
  warning: '#FFA000',
  success: '#388E3C',
  text: '#212121',
  textSecondary: '#757575',
  textLight: '#BDBDBD',
};

const FUEL_TYPE_COLORS = {
  CNG: '#4CAF50',
  LNG: '#2196F3',
  Hydrogen: '#9C27B0',
  Electric: '#FF9800',
  Diesel: '#795548',
  Gasoline: '#F44336',
  Biodiesel: '#8BC34A',
};
```

## Features Summary

1. **Fuel Station Locator**
   - Map and List views
   - Filter by fuel type (CNG, LNG, Hydrogen, EV, Diesel, Biodiesel)
   - Station details with prices, amenities, hours
   - Directions and Call buttons

2. **Regulations Library**
   - Search functionality
   - Filter by category (Safety, Emissions, Installation, Incentive)
   - Filter by jurisdiction (Federal, State)
   - Code references and summaries

3. **Service Centers Directory**
   - Search functionality
   - Filter by service type (In-Shop, Mobile, Both)
   - Ratings and reviews
   - Certifications display

4. **Certified Inspectors**
   - Search functionality
   - Filter by fuel specialization
   - Experience and credentials
   - Service area coverage

5. **User Profile**
   - Personal information management
   - Fuel preferences
   - Favorite stations

## Mock Data

The application includes mock data for:
- 8 fuel stations across different US cities
- 8 regulations covering various fuel types
- 5 service centers
- 5 certified inspectors

This data is automatically seeded to MongoDB on first API call.

## Future Enhancements

1. **AFDC API Integration** - Connect to U.S. DOE Alternative Fuels Data Center
2. **User Authentication** - Add login/signup functionality
3. **Push Notifications** - Station outages, regulatory updates
4. **Fleet Management** - Premium feature for fleet operators
5. **Offline Mode** - Cache data for offline access
6. **Real-time Prices** - Live fuel price updates

---

For complete source code files, please refer to the individual file sections in this documentation or download from the repository.
