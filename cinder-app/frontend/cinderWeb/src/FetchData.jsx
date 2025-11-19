import { useMemo, useState } from "react";

const CITY_PRESETS = [
  { name: "Hartford", lat: 41.7627, lon: -72.6743 },
  { name: "Middletown", lat: 41.5623, lon: -72.6506 },
  { name: "Bridgeport", lat: 41.1792, lon: -73.1894 },
  { name: "New Haven", lat: 41.3083, lon: -72.9279 },
];

const THRESHOLD_META = {
  temperature: { label: "Temperature", unit: "°C" },
  humidity: { label: "Humidity", unit: "%" },
  wind_speed: { label: "Wind Speed", unit: "km/h" },
  wind_direction: { label: "Wind Direction", unit: "°" },
  precipitation: { label: "Precipitation", unit: "mm" },
  pressure: { label: "Pressure", unit: "hPa" },
};

const DEFAULT_ORDER = [
  "temperature",
  "humidity",
  "wind_speed",
  "wind_direction",
  "precipitation",
  "pressure",
];

function normalize(text) {
  return text.trim().toLowerCase();
}

function FetchData() {
  const [query, setQuery] = useState("");
  const [selectedCity, setSelectedCity] = useState(null);
  const [forecastHour, setForecastHour] = useState("");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("idle");

  const quickHourOptions = useMemo(() => {
    const hours = [];
    for (let i = 0; i <= 48; i += 3) hours.push(i);
    return hours;
  }, []);

  const findCity = (text) => {
    const cleaned = normalize(text);
    if (!cleaned) return null;
    return CITY_PRESETS.find((city) => normalize(city.name) === cleaned);
  };

  const fetchCityData = async (city, hour) => {
    if (!city) return;
    setStatus("loading");
    setError("");
    setData(null);

    try {
      let url = `/api/data?lat=${city.lat}&lon=${city.lon}`;
      if (hour !== "") {
        url += `&fh=${hour}`;
      }
      const res = await fetch(url);
      if (!res.ok) {
        throw new Error("Backend returned an error.");
      }
      const json = await res.json();
      setData(json);
      setStatus("done");
    } catch (err) {
      setError(err.message || "Unable to reach the server.");
      setStatus("idle");
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    const match = findCity(query);
    if (!match) {
      setError("Try Hartford, Middletown, Bridgeport, or New Haven.");
      return;
    }
    setSelectedCity(match);
    fetchCityData(match, forecastHour);
  };

  const handleQuickPick = (city) => {
    setQuery(city.name);
    setSelectedCity(city);
    fetchCityData(city, forecastHour);
  };

  const renderValue = (threshold, value) => {
    const meta = THRESHOLD_META[threshold] || {};
    const rawNumber = typeof value === "number" ? value : Number(value);
    if (Number.isNaN(rawNumber)) return "—";

    const decimals = meta.unit === "mm" ? 2 : meta.unit === "hPa" ? 1 : 1;
    return `${rawNumber.toFixed(decimals)}${meta.unit ? ` ${meta.unit}` : ""}`;
  };

  const hasData = data && Object.keys(data.data || {}).length > 0;

  return (
    <section className="search-panel">
      <form className="search-form" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Search a city (Hartford, Middletown, Bridgeport, New Haven)"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          aria-label="City name"
        />

        <label className="hour-select">
          <span>Forecast hour</span>
          <select
            value={forecastHour}
            onChange={(event) => setForecastHour(event.target.value)}
          >
            <option value="">Newest</option>
            {quickHourOptions.map((hour) => (
              <option key={hour} value={hour}>
                {hour}h
              </option>
            ))}
          </select>
        </label>

        <button type="submit" disabled={status === "loading"}>
          {status === "loading" ? "Loading..." : "Get Forecast"}
        </button>
      </form>

      <div className="quick-picks">
        <span>Quick picks:</span>
        {CITY_PRESETS.map((city) => (
          <button
            type="button"
            key={city.name}
            className="quick-button"
            onClick={() => handleQuickPick(city)}
            disabled={status === "loading"}
          >
            {city.name}
          </button>
        ))}
      </div>

      {error && <p className="status-text error">{error}</p>}
      {!error && status === "loading" && (
        <p className="status-text">Talking to Atlas…</p>
      )}
      {!error && status === "done" && selectedCity && (
        <p className="status-text">
          Showing the latest NBM ensemble mean for {selectedCity.name}
          {forecastHour !== "" ? ` (forecast hour ${forecastHour})` : ""}
        </p>
      )}

      {hasData ? (
        <div className="cards-grid">
          {DEFAULT_ORDER.map((key) => {
            const series = data.data?.[key];
            if (!series) return null;
            const meta = THRESHOLD_META[key] || { label: key };
            return (
              <article className="metric-card" key={key}>
                <div className="metric-title">{meta.label}</div>
                {series.map((entry, index) => (
                  <div className="metric-row" key={`${key}-${index}`}>
                    <span className="metric-value">
                      {renderValue(key, entry.value)}
                    </span>
                    <span className="metric-time">
                      fh {entry.forecast_time ?? "?"}
                      {entry.step_length ? ` • step ${entry.step_length}h` : ""}
                    </span>
                  </div>
                ))}
              </article>
            );
          })}
        </div>
      ) : (
        status === "done" &&
        !error && (
          <p className="status-text">Nothing came back for that request.</p>
        )
      )}
    </section>
  );
}

export default FetchData;
