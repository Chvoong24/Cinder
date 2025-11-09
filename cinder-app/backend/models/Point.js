import mongoose from "mongoose";

const pointSchema = new mongoose.Schema({
  lat: Number,
  lon: Number,
  name: String,
  step_length: Number,
  forecast_time: Number,
  value: Number,
});

const Point = mongoose.model("Point", pointSchema);
export default Point;