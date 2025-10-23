import React from "react";
import "./WeatherDisplay.css";

interface WeatherDisplayProps {
  data: any; // Replace with your actual data type from backend
}

const WeatherDisplay: React.FC<WeatherDisplayProps> = ({ data }) => {
  return (
    <div className="weather-display">
      <div className="weather-main">
        <h2>{data.location || "Location"}</h2>
        <div className="temperature">{data.temperature || "--"}°F</div>
        <div className="condition">{data.condition || "Clear"}</div>
      </div>

      <div className="weather-details">
        <div className="detail-item">
          <span className="detail-label">Humidity</span>
          <span className="detail-value">{data.humidity || "--"}%</span>
        </div>
        <div className="detail-item">
          <span className="detail-label">Wind Speed</span>
          <span className="detail-value">{data.windSpeed || "--"} mph</span>
        </div>
        <div className="detail-item">
          <span className="detail-label">Pressure</span>
          <span className="detail-value">{data.pressure || "--"} mb</span>
        </div>
      </div>
    </div>
  );
};

export default WeatherDisplay;
