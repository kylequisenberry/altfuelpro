# FuelPoint Navigator 🚚⛽

A cross-platform mobile application for the Alternative Fuels market, helping truckers and fleet managers find fuel stations, service centers, and plan routes with optimal refueling stops.

![Platform](https://img.shields.io/badge/Platform-iOS%20%7C%20Android%20%7C%20Web-blue)
![Expo](https://img.shields.io/badge/Expo-SDK%2054-000020)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

### Core Features
- **🗺️ Live Fuel Station Locator** - Real-time data from AFDC/NREL API
- **🔧 Service Center Directory** - 118+ locations across US & Canada
- **📍 Find Nearest** - Geolocation-based search (25mi/40km radius)
- **🧭 Turn-by-Turn Navigation** - Integration with Google Maps, Apple Maps, Waze
- **🛣️ Route Planner** - Plan routes with optimal fuel stops
- **📴 Offline Mode** - Cache data for areas with poor connectivity

### Additional Features
- **📜 Regulations Library** - Searchable database of industry regulations
- **👷 Inspector Directory** - Find certified inspectors (AFVi, CSA links)
- **🏭 Fuel System Providers** - Comprehensive provider directory
- **💬 Support Center** - In-app feedback and support system
- **🔍 Advanced Filters** - Filter by fuel type, location, service type

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React Native, Expo (SDK 54), TypeScript |
| **Backend** | Python, FastAPI, Pydantic |
| **Database** | MongoDB (Motor async driver) |
| **Maps** | Leaflet.js (Web + Mobile via WebView) |
| **API** | AFDC/NREL for live fuel station data |
| **Caching** | AsyncStorage for offline support |

## 📱 Screenshots

| Stations Map | Service Centers | Route Planner |
|:---:|:---:|:---:|
| Interactive map with fuel stations | 118+ service centers | Plan routes with fuel stops |

| Find Nearest | Offline Mode | Navigation |
|:---:|:---:|:---:|
| Geolocation search | Download for offline | Google Maps/Waze integration |

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- MongoDB
- Expo CLI (`npm install -g expo-cli`)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/fuelpoint-navigator.git
   cd fuelpoint-navigator
   ```

2. **Set up Backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your MongoDB URL and AFDC API key
   uvicorn server:app --reload --port 8001
   ```

3. **Set up Frontend**
   ```bash
   cd frontend
   yarn install
   cp .env.example .env
   # Edit .env with your backend URL
   yarn start
   ```

4. **Run on device**
   - Scan QR code with Expo Go app (iOS/Android)
   - Or press `w` for web browser

## ⚙️ Environment Variables

### Backend (`backend/.env`)
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="fuelpoint_db"
NREL_API_KEY="your-afdc-api-key"
```

### Frontend (`frontend/.env`)
```env
EXPO_PUBLIC_BACKEND_URL=http://localhost:8001
```

> Get a free AFDC API key at: https://developer.nrel.gov/signup/

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stations` | Live fuel stations (AFDC) |
| GET | `/api/service-centers` | All service centers |
| GET | `/api/service-centers/nearby/location` | Nearby with distance |
| POST | `/api/route-planner` | Plan route with fuel stops |
| GET | `/api/regulations` | Regulations library |
| GET | `/api/inspectors` | Certified inspectors |
| GET | `/api/providers` | Fuel system providers |
| POST | `/api/feedback` | Submit feedback |

## 📂 Project Structure

```
├── backend/
│   ├── server.py           # FastAPI application
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Environment variables
│
├── frontend/
│   ├── app/               # Expo Router screens
│   │   ├── index.tsx      # Stations (home)
│   │   ├── services.tsx   # Service centers
│   │   ├── regulations.tsx
│   │   ├── inspectors.tsx
│   │   ├── providers.tsx
│   │   └── profile.tsx    # Profile + Offline settings
│   │
│   └── src/
│       ├── components/    # Reusable UI components
│       ├── services/      # API client, offline cache
│       ├── hooks/         # Custom hooks
│       └── utils/         # Utilities
│
└── memory/
    └── PRD.md            # Product Requirements
```

## 🚢 Deployment

### Backend Deployment
Deploy using your preferred platform (Heroku, Railway, AWS, etc.):
```bash
cd backend
# Set environment variables on your platform
# Deploy with uvicorn
uvicorn server:app --host 0.0.0.0 --port $PORT
```

### Mobile App Distribution

**For Beta Testing:**
```bash
# Quick - Use Expo Go
expo publish

# Production - Build standalone apps
eas build --platform ios     # TestFlight
eas build --platform android # Play Store / APK
```

## 🗺️ Fuel Types Supported

- **CNG** - Compressed Natural Gas
- **LNG** - Liquefied Natural Gas
- **Hydrogen** - Fuel Cell
- **Electric** - EV Charging
- **E85** - Ethanol Blend
- **Biodiesel**
- **LPG** - Propane

## 📊 Data Coverage

| Region | Service Centers | Coverage |
|--------|-----------------|----------|
| United States | 106 | 36 states |
| Canada | 12 | AB, BC, ON, QC |
| **Total** | **118** | **40 regions** |

**Major Networks Included:**
- Rush Truck Centers (16 locations)
- Cummins Sales & Service (18 locations)
- Kenworth/MHC Network (34 locations)
- Velocity Truck Centres (5 locations)
- Peterbilt Dealers (8 locations)
- And more...

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [AFDC/NREL](https://developer.nrel.gov/) for fuel station data API
- [Expo](https://expo.dev/) for the amazing mobile development platform
- [Leaflet](https://leafletjs.com/) for interactive maps
- Alternative fuels industry partners for service center data

## 📧 Support

For support, feedback, or feature requests:
- Use the in-app Support Center
- Open an issue on GitHub

---

**Built with ❤️ for the Alternative Fuels Industry**
