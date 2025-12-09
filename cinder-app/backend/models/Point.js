import mongoose from "mongoose";

const pointSchema = new mongoose.Schema({
  lat: Number,
  lon: Number,
  step_length: Number,
  forecast_time: Number,
  value: Number,
  name: String,
  threshold: String,
  sitrep: String,
  anal_date: String,
});

const Point = mongoose.model("Point", pointSchema);
export default Point;