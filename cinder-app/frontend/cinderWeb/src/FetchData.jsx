import React, { useState } from "react";
import "./FetchData.css"; // <-- ADD THIS LINE

function FetchData() {
  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");
  const [fh, setFH] = useState("");
  const [fh_max, setMax] = useState("");
  const [fh_min, setMin] = useState("");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

 const fetchData = async () => {
  setError("");
  setData(null);

  try {
    const res = await fetch(
      `/api/data?lat=${lat}&lon=${lon}&fh=${fh}&fh_min=${fh_min}&fh_max=${fh_max}`
    );
    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const json = await res.json();
    setData(json);
  } catch (err) {
    setError(err.message);
  }
};

  return (
    <div className="fetch-container">
      <div className="fetch-card">
        <h2 className="title">Cinder</h2>

        <input
          type="number"
          step="any"
          placeholder="Latitude"
          value={lat}
          onChange={(e) => setLat(e.target.value)}
          className="input"
        />

        <input
          type="number"
          step="any"
          placeholder="Longitude"
          value={lon}
          onChange={(e) => setLon(e.target.value)}
          className="input"
        />

        <input
          type="number"
          step="any"
          placeholder="Forecast Hour"
          value={fh}
          onChange={(e) => setFH(e.target.value)}
          className="input"
        />

       <input
          type="number"
          step="any"
          placeholder="Forecast Min"
          value={fh_min}
          onChange={(e) => setMin(e.target.value)}
          className="range"
        />
        <input
          type="number"
          step="any"
          placeholder="Forecast Max"
          value={fh_max}
          onChange={(e) => setMax(e.target.value)}
          className="range"
        />

        <button onClick={fetchData} className="button">
          Fetch Data
        </button>

        {error && <p className="error">{error}</p>}

        {data && (
          <pre className="json-box">
            {JSON.stringify(data, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}

export default FetchData;