# Cinder Weather Backend API

RESTful API for the Cinder Weather Application built with Node.js, Express, and MongoDB.

## Prerequisites

- Node.js (v14 or higher)
- MongoDB (running locally or MongoDB Atlas)
- npm or yarn

## Installation

1. Navigate to the backend directory:

```bash
cd backend
```

2. Install dependencies:

```bash
npm install
```

3. Create a `.env` file in the backend root directory:

```env
PORT=5000
MONGODB_URI=mongodb://localhost:27017/cinder_weather
NODE_ENV=development
```

4. Make sure MongoDB is running locally, or update `MONGODB_URI` with your MongoDB Atlas connection string.

## Running the Server

### Development Mode (with auto-restart):

```bash
npm run dev
```

### Production Mode:

```bash
npm start
```

The server will start on `http://localhost:5000`

## API Endpoints

### Health Check

- **GET** `/api/health` - Check if the API is running

### Weather Data Endpoints

#### Get All Weather Data

- **GET** `/api/weather`
- Query Parameters:
  - `location` (optional): Filter by location name
  - `startDate` (optional): Filter by start date (ISO format)
  - `endDate` (optional): Filter by end date (ISO format)
  - `limit` (optional, default: 100): Limit number of results

#### Get Weather Data by ID

- **GET** `/api/weather/:id`
- Returns a single weather data entry

#### Get Weather by Location

- **GET** `/api/weather/location/:locationName`
- Query Parameters:
  - `limit` (optional, default: 10): Limit number of results

#### Get Current Weather

- **GET** `/api/weather/current/:locationName`
- Returns the most recent weather data for a location

#### Get Forecast

- **GET** `/api/weather/forecast/:locationName`
- Query Parameters:
  - `hours` (optional, default: 24): Number of hours to forecast

#### Get All Locations

- **GET** `/api/weather/locations`
- Returns list of all unique location names

#### Create Weather Data

- **POST** `/api/weather`
- Body: Weather data object (see Data Model below)

#### Bulk Create Weather Data

- **POST** `/api/weather/bulk`
- Body: `{ "data": [array of weather data objects] }`

#### Update Weather Data

- **PUT** `/api/weather/:id`
- Body: Updated weather data object

#### Delete Weather Data

- **DELETE** `/api/weather/:id`

## Data Model

```javascript
{
  location: {
    type: "Point",
    coordinates: [longitude, latitude],
    name: "Location Name"
  },
  timestamp: Date,
  forecastHour: Number,
  temperature: {
    current: Number,
    feelsLike: Number,
    min: Number,
    max: Number,
    unit: "celsius"
  },
  precipitation: {
    probability: Number,
    amount: Number,
    type: String,
    unit: "mm"
  },
  wind: {
    speed: Number,
    direction: Number,
    gust: Number,
    unit: "km/h"
  },
  humidity: Number,
  pressure: {
    value: Number,
    unit: "hPa"
  },
  cloudCover: Number,
  visibility: {
    value: Number,
    unit: "km"
  },
  uvIndex: Number,
  dewPoint: Number,
  modelSource: "NBM",
  rawData: Object
}
```

## Example Requests

### Get current weather for a location:

```bash
curl http://localhost:5000/api/weather/current/Boston
```

### Get 48-hour forecast:

```bash
curl http://localhost:5000/api/weather/forecast/Boston?hours=48
```

### Create new weather data:

```bash
curl -X POST http://localhost:5000/api/weather \
  -H "Content-Type: application/json" \
  -d '{
    "location": {
      "coordinates": [-71.0589, 42.3601],
      "name": "Boston"
    },
    "timestamp": "2025-10-17T12:00:00Z",
    "forecastHour": 0,
    "temperature": {
      "current": 20,
      "unit": "celsius"
    }
  }'
```

## Error Handling

All endpoints return JSON responses in the format:

```javascript
{
  "success": true/false,
  "data": {...},      // on success
  "error": "message"  // on error
}
```

## Project Structure

```
backend/
├── src/
│   ├── config/
│   │   └── database.js       # MongoDB connection
│   ├── controllers/
│   │   └── weatherController.js  # API logic
│   ├── models/
│   │   └── WeatherData.js    # Mongoose schema
│   ├── routes/
│   │   └── weatherRoutes.js  # API routes
│   ├── middleware/           # Custom middleware (future)
│   └── server.js             # Main entry point
├── .env                      # Environment variables
├── .gitignore
├── package.json
└── README.md
```

## Next Steps

1. Set up MongoDB locally or get a MongoDB Atlas connection string
2. Populate the database with weather data from the Python GRIB scripts
3. Test the API endpoints using Postman or curl
4. Connect the React frontend to these endpoints

## License

GPL-3.0
