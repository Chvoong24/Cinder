import React, { useState } from "react";
import "./App.css";
import WeatherDisplay from "./components/WeatherDisplay";
import SearchBar from "./components/SearchBar";

interface WeatherData {
  location: string;
  temperature: number | string;
  condition: string;
  humidity: number | string;
  windSpeed: number | string;
  pressure: number | string;
}

function App() {
  const [weatherData, setWeatherData] = useState<WeatherData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchWeather = async (location: string) => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `http://localhost:5001/api/weather/current/${location}`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch weather data");
      }

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.error || "Failed to fetch weather data");
      }

      const transformedData = {
        location: result.data.location.name,
        temperature: result.data.temperature?.current || "--",
        condition: result.data.precipitation?.type || "Clear",
        humidity: result.data.humidity || "--",
        windSpeed: result.data.wind?.speed || "--",
        pressure: result.data.pressure?.value || "--",
      };

      setWeatherData(transformedData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      setWeatherData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🌤️ Cinder Weather</h1>
        <SearchBar onSearch={fetchWeather} />

        {loading && <div className="loading">Loading weather data...</div>}
        {error && <div className="error">{error}</div>}
        {weatherData && <WeatherDisplay data={weatherData} />}
      </header>
    </div>
  );
}

export default App;
