import mongoose from "mongoose";

const weatherDataSchema = new mongoose.Schema(
  {
    location: {
      type: {
        type: String,
        enum: ["Point"],
        default: "Point",
      },
      coordinates: {
        type: [Number], // [longitude, latitude]
        required: true,
      },
      name: {
        type: String,
        required: true,
      },
    },
    timestamp: {
      type: Date,
      required: true,
      index: true,
    },
    forecastHour: {
      type: Number,
      required: true,
    },
    temperature: {
      current: Number,
      feelsLike: Number,
      min: Number,
      max: Number,
      unit: {
        type: String,
        default: "celsius",
      },
    },
    precipitation: {
      probability: Number, // Percentage
      amount: Number,
      type: String, // rain, snow, mixed
      unit: {
        type: String,
        default: "mm",
      },
    },
    wind: {
      speed: Number,
      direction: Number, // Degrees
      gust: Number,
      unit: {
        type: String,
        default: "km/h",
      },
    },
    humidity: {
      type: Number,
      min: 0,
      max: 100,
    },
    pressure: {
      value: Number,
      unit: {
        type: String,
        default: "hPa",
      },
    },
    cloudCover: {
      type: Number,
      min: 0,
      max: 100,
    },
    visibility: {
      value: Number,
      unit: {
        type: String,
        default: "km",
      },
    },
    uvIndex: Number,
    dewPoint: Number,
    modelSource: {
      type: String,
      default: "NBM", // National Blend of Models
    },
    rawData: {
      type: mongoose.Schema.Types.Mixed, // Store any additional raw GRIB data
    },
  },
  {
    timestamps: true, // Adds createdAt and updatedAt
  }
);

// Create indexes for common queries
weatherDataSchema.index({ "location.coordinates": "2dsphere" });
weatherDataSchema.index({ timestamp: 1, "location.name": 1 });
weatherDataSchema.index({ createdAt: 1 });

const WeatherData = mongoose.model("WeatherData", weatherDataSchema);

export default WeatherData;
