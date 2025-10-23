import WeatherData from "../models/WeatherData.js";

// Get all weather data with optional filters
export const getAllWeatherData = async (req, res) => {
  try {
    const { location, startDate, endDate, limit = 100 } = req.query;

    let query = {};

    // Filter by location name if provided
    if (location) {
      query["location.name"] = new RegExp(location, "i");
    }

    // Filter by date range if provided
    if (startDate || endDate) {
      query.timestamp = {};
      if (startDate) query.timestamp.$gte = new Date(startDate);
      if (endDate) query.timestamp.$lte = new Date(endDate);
    }

    const weatherData = await WeatherData.find(query)
      .sort({ timestamp: -1 })
      .limit(parseInt(limit));

    res.status(200).json({
      success: true,
      count: weatherData.length,
      data: weatherData,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
};

// Get weather data by ID
export const getWeatherDataById = async (req, res) => {
  try {
    const weatherData = await WeatherData.findById(req.params.id);

    if (!weatherData) {
      return res.status(404).json({
        success: false,
        error: "Weather data not found",
      });
    }

    res.status(200).json({
      success: true,
      data: weatherData,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
};

// Get weather data by location
export const getWeatherByLocation = async (req, res) => {
  try {
    const { locationName } = req.params;
    const { limit = 10 } = req.query;

    const weatherData = await WeatherData.find({
      "location.name": new RegExp(locationName, "i"),
    })
      .sort({ timestamp: -1 })
      .limit(parseInt(limit));

    if (weatherData.length === 0) {
      return res.status(404).json({
        success: false,
        error: `No weather data found for location: ${locationName}`,
      });
    }

    res.status(200).json({
      success: true,
      count: weatherData.length,
      data: weatherData,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
};

// Get current weather (most recent data)
export const getCurrentWeather = async (req, res) => {
  try {
    const { locationName } = req.params;

    const currentWeather = await WeatherData.findOne({
      "location.name": new RegExp(locationName, "i"),
    }).sort({ timestamp: -1 });

    if (!currentWeather) {
      return res.status(404).json({
        success: false,
        error: `No current weather data found for location: ${locationName}`,
      });
    }

    res.status(200).json({
      success: true,
      data: currentWeather,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
};

// Get forecast (future weather data)
export const getForecast = async (req, res) => {
  try {
    const { locationName } = req.params;
    const { hours = 24 } = req.query;

    const now = new Date();
    const futureTime = new Date(now.getTime() + hours * 60 * 60 * 1000);

    const forecast = await WeatherData.find({
      "location.name": new RegExp(locationName, "i"),
      timestamp: {
        $gte: now,
        $lte: futureTime,
      },
    }).sort({ timestamp: 1 });

    res.status(200).json({
      success: true,
      count: forecast.length,
      data: forecast,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
};

// Create new weather data
export const createWeatherData = async (req, res) => {
  try {
    const weatherData = await WeatherData.create(req.body);

    res.status(201).json({
      success: true,
      data: weatherData,
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message,
    });
  }
};

// Bulk create weather data
export const bulkCreateWeatherData = async (req, res) => {
  try {
    const { data } = req.body;

    if (!Array.isArray(data)) {
      return res.status(400).json({
        success: false,
        error: "Data must be an array",
      });
    }

    const weatherData = await WeatherData.insertMany(data);

    res.status(201).json({
      success: true,
      count: weatherData.length,
      data: weatherData,
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message,
    });
  }
};

// Update weather data
export const updateWeatherData = async (req, res) => {
  try {
    const weatherData = await WeatherData.findByIdAndUpdate(
      req.params.id,
      req.body,
      {
        new: true,
        runValidators: true,
      }
    );

    if (!weatherData) {
      return res.status(404).json({
        success: false,
        error: "Weather data not found",
      });
    }

    res.status(200).json({
      success: true,
      data: weatherData,
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message,
    });
  }
};

// Delete weather data
export const deleteWeatherData = async (req, res) => {
  try {
    const weatherData = await WeatherData.findByIdAndDelete(req.params.id);

    if (!weatherData) {
      return res.status(404).json({
        success: false,
        error: "Weather data not found",
      });
    }

    res.status(200).json({
      success: true,
      message: "Weather data deleted successfully",
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
};

// Get unique locations
export const getLocations = async (req, res) => {
  try {
    const locations = await WeatherData.distinct("location.name");

    res.status(200).json({
      success: true,
      count: locations.length,
      data: locations,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
    });
  }
};
