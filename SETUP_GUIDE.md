# 🌤️ Cinder Weather - Complete Setup Guide

## Overview

This project connects Python weather data fetching scripts → MongoDB database → Express API → React frontend

## Architecture

```
Python Scripts (fetch_all.py)
    ↓
Download GRIB files to disk
    ↓
grib_to_mongodb.py (Bridge Script)
    ↓
Parse GRIB → Insert into MongoDB
    ↓
Express API (backend/)
    ↓
React Frontend (frontend/)
```

---

## 📋 Prerequisites

- **Node.js** (v14+)
- **Python** (3.8+)
- **MongoDB** (local or Atlas)
- **Postman** (for API testing)

---

## 🚀 Setup Instructions

### 1. Install Python Dependencies

```bash
cd /Users/duyhuynh/Desktop/project/Cinder/temp_clone

# Install Python packages
pip install -r requirements.txt

# Note: pygrib might require additional system libraries
# On macOS:
brew install eccodes
# On Ubuntu:
# sudo apt-get install libeccodes-dev
```

### 2. Set Up MongoDB

**Option A: Local MongoDB**

```bash
# Install MongoDB (macOS)
brew install mongodb-community

# Start MongoDB
brew services start mongodb-community
```

**Option B: MongoDB Atlas (Cloud)**

- Go to https://www.mongodb.com/cloud/atlas
- Create free cluster
- Get connection string
- Update `.env` file in backend/

### 3. Configure Backend

Your `.env` file in `backend/` should have:

```env
PORT=5000
MONGODB_URI=mongodb://localhost:27017/cinder_weather
MONGODB_PASS=your_password_if_needed
NODE_ENV=development
```

### 4. Install Backend Dependencies

```bash
cd backend
npm install
```

### 5. Install Frontend Dependencies

```bash
cd ../frontend
npm install
```

---

## 🔄 Complete Workflow

### Step 1: Download Weather Data

```bash
# From project root
python fetch_all.py
```

This downloads GRIB files to:

- `nbm_data/nbm_download/`
- `href_data/href_download/`
- `refs_data/refs_download/`

### Step 2: Parse GRIB Files & Populate MongoDB

```bash
# From project root
python grib_to_mongodb.py
```

This will:

- ✅ Read all GRIB files
- ✅ Extract weather data (temp, humidity, wind, pressure)
- ✅ Insert into MongoDB

### Step 3: Start Backend API

```bash
cd backend
npm run dev
```

You should see:

```
Server is running on port 5000
MongoDB Connected: localhost
```

### Step 4: Test API with Postman

Open Postman and test these endpoints:

**1. Health Check**

```
GET http://localhost:5000/api/health
```

**2. Get All Locations**

```
GET http://localhost:5000/api/weather/locations
```

**3. Get Current Weather**

```
GET http://localhost:5000/api/weather/current/Hartford
```

**4. Get All Weather Data**

```
GET http://localhost:5000/api/weather?limit=10
```

**5. Get Forecast**

```
GET http://localhost:5000/api/weather/forecast/Hartford?hours=24
```

### Step 5: Start Frontend

```bash
cd frontend
npm start
```

Open browser to: `http://localhost:3000`

---

## 📬 API Endpoints Reference

| Method | Endpoint                              | Description                         |
| ------ | ------------------------------------- | ----------------------------------- |
| GET    | `/api/health`                         | Check API status                    |
| GET    | `/api/weather`                        | Get all weather data (with filters) |
| GET    | `/api/weather/locations`              | Get all location names              |
| GET    | `/api/weather/current/:locationName`  | Get current weather                 |
| GET    | `/api/weather/forecast/:locationName` | Get forecast                        |
| POST   | `/api/weather`                        | Create weather data                 |
| POST   | `/api/weather/bulk`                   | Bulk insert weather data            |

---

## 🧪 Testing Workflow

### 1. Test Backend Standalone

```bash
# Terminal 1: Start backend
cd backend
npm run dev

# Terminal 2: Test with curl
curl http://localhost:5000/api/health
curl http://localhost:5000/api/weather/locations
```

### 2. Test Full Stack

```bash
# Terminal 1: Backend
cd backend && npm run dev

# Terminal 2: Frontend
cd frontend && npm start

# Browser: Open http://localhost:3000
# Type "Hartford" in search box
```

---

## 📁 Project Structure

```
Cinder/
├── backend/                    # Express.js API
│   ├── src/
│   │   ├── server.js          # Main server
│   │   ├── routes/            # API routes
│   │   ├── controllers/       # Business logic
│   │   ├── models/            # MongoDB schemas
│   │   └── config/            # Database config
│   ├── .env                   # Environment variables
│   └── package.json
│
├── frontend/                   # React app
│   ├── src/
│   │   ├── App.tsx            # Main component
│   │   ├── components/        # UI components
│   │   └── App.css
│   └── package.json
│
├── Fetch_Scripts/             # Python GRIB downloaders
│   ├── get_nbm.py
│   ├── get_href.py
│   └── get_refs.py
│
├── grib_to_mongodb.py         # Bridge script (GRIB → MongoDB)
├── fetch_all.py               # Download all GRIB files
├── requirements.txt           # Python dependencies
└── README.md
```

---

## 🐛 Troubleshooting

### MongoDB Connection Error

```
Error: connect ECONNREFUSED 127.0.0.1:27017
```

**Solution:** Make sure MongoDB is running

```bash
brew services start mongodb-community
# or
mongod
```

### No Data in API Response

```json
{
  "success": false,
  "error": "No weather data found"
}
```

**Solution:** Run the bridge script to populate data

```bash
python grib_to_mongodb.py
```

### CORS Error in Frontend

**Solution:** Make sure backend is running and has CORS enabled (already configured)

### pygrib Installation Error

**Solution:** Install eccodes library first

```bash
# macOS
brew install eccodes

# Ubuntu/Debian
sudo apt-get install libeccodes-dev
```

---

## 🔄 Daily Update Workflow

For production, you'd run this daily (via cron job):

```bash
# 1. Fetch new GRIB data
python fetch_all.py

# 2. Parse and update database
python grib_to_mongodb.py
```

The API and frontend will automatically serve the latest data!

---

## 📊 Sample Postman Collection

Import this JSON into Postman:

```json
{
  "info": {
    "name": "Cinder Weather API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": "http://localhost:5000/api/health"
      }
    },
    {
      "name": "Get Locations",
      "request": {
        "method": "GET",
        "url": "http://localhost:5000/api/weather/locations"
      }
    },
    {
      "name": "Current Weather",
      "request": {
        "method": "GET",
        "url": "http://localhost:5000/api/weather/current/Hartford"
      }
    }
  ]
}
```

---

## ✅ Success Checklist

- [ ] MongoDB is running
- [ ] Python dependencies installed (`pip install -r requirements.txt`)
- [ ] GRIB files downloaded (`python fetch_all.py`)
- [ ] Data in MongoDB (`python grib_to_mongodb.py`)
- [ ] Backend API running (`cd backend && npm run dev`)
- [ ] API returns data in Postman
- [ ] Frontend running (`cd frontend && npm start`)
- [ ] Frontend displays weather data

---

## 🎯 Quick Start (All in One)

```bash
# Terminal 1: Start MongoDB
mongod

# Terminal 2: Populate database
python fetch_all.py
python grib_to_mongodb.py

# Terminal 3: Start backend
cd backend && npm run dev

# Terminal 4: Start frontend
cd frontend && npm start

# Open browser: http://localhost:3000
# Test with Postman: http://localhost:5000/api/health
```

---

Good luck! 🚀
