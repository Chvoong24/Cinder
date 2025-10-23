import express from "express";
import {
  getAllWeatherData,
  getWeatherDataById,
  getWeatherByLocation,
  getCurrentWeather,
  getForecast,
  createWeatherData,
  bulkCreateWeatherData,
  updateWeatherData,
  deleteWeatherData,
  getLocations,
} from "../controllers/weatherController.js";

const router = express.Router();

// Get all locations
router.get("/locations", getLocations);

// Get all weather data with filters
router.get("/", getAllWeatherData);

// Get weather data by ID
router.get("/:id", getWeatherDataById);

// Get weather by location
router.get("/location/:locationName", getWeatherByLocation);

// Get current weather for a location
router.get("/current/:locationName", getCurrentWeather);

// Get forecast for a location
router.get("/forecast/:locationName", getForecast);

// Create new weather data
router.post("/", createWeatherData);

// Bulk create weather data
router.post("/bulk", bulkCreateWeatherData);

// Update weather data
router.put("/:id", updateWeatherData);

// Delete weather data
router.delete("/:id", deleteWeatherData);

export default router;
