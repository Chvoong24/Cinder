import React, { useState } from "react";
import "./FetchData.css";

const API_URL = import.meta.env.VITE_API_URL || "";

const sortWeatherData = (data) => {
  return [...data].sort((a, b) => {
    const cmp = (x, y) =>
      (x ?? "").toLowerCase().localeCompare((y ?? "").toLowerCase());
    return (
      cmp(a.sitrep, b.sitrep) ||
      cmp(a.name, b.name) ||
      (a.forecast_time ?? 0) - (b.forecast_time ?? 0)
    );
  });
};

function FetchData() {
  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");
  const [fh, setFH] = useState("");
  const [fh_max, setMax] = useState("");
  const [fh_min, setMin] = useState("");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const fetchData = async () => {
    setError("");
    setData(null);
    setIsLoading(true);

    try {
      const res = await fetch(
        `${API_URL}/api/data?lat=${lat}&lon=${lon}&fh=${fh}&fh_min=${fh_min}&fh_max=${fh_max}`
      );

      if (!res.ok) throw new Error(`Server error: ${res.status}`);

      const json = await res.json();
      setData(json);
      setIsLoading(false);
    } catch (err) {
      setError(err.message);
      setIsLoading(false);
    }
  };

  const hideFH = fh_min !== "" || fh_max !== "";
  const hideMinMax = fh !== "";

  return (
    <div className="fetch-container">
      <div className="fetch-card">
        <h2 className="title">Cinder ⛅</h2>

        <input
          type="number"
          placeholder="Latitude"
          value={lat}
          onChange={(e) => setLat(e.target.value)}
          className="input"
        />

        <input
          type="number"
          placeholder="Longitude"
          value={lon}
          onChange={(e) => setLon(e.target.value)}
          className="input"
        />

        {!hideFH && (
          <input
            type="number"
            placeholder="Forecast Hour"
            value={fh}
            onChange={(e) => setFH(e.target.value)}
            className="input"
          />
        )}

        {!hideMinMax && (
          <>
            <input
              type="number"
              placeholder="Forecast Min"
              value={fh_min}
              onChange={(e) => setMin(e.target.value)}
              className="range"
            />

            <input
              type="number"
              placeholder="Forecast Max"
              value={fh_max}
              onChange={(e) => setMax(e.target.value)}
              className="range"
            />
          </>
        )}

        <button onClick={fetchData} className="button" disabled={isLoading}>
          {isLoading ? "Loading..." : "Fetch Data"}
        </button>

        {error && <p className="error">{error}</p>}

        {data && data.length > 0 && (
          <div className="table-container">
            <table className="result-table">
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Name</th>
                  <th>Threshold</th>
                  <th>Step Length</th>
                  <th>Forecast Time</th>
                  <th>Value</th>
                </tr>
              </thead>

              <tbody>
                {sortWeatherData(data).map((item, i) => (
                  <tr key={i}>
                    <td>{item.sitrep ?? "-"}</td>
                    <td>{item.name ?? "—"}</td>
                    <td>{item.threshold ?? "—"}</td>
                    <td>{item.step_length ?? "—"}</td>
                    <td>{item.forecast_time ?? "—"}</td>
                    <td>{item.value ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default FetchData;
