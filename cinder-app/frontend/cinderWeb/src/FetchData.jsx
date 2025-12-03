import React, { useState } from "react";
import "./FetchData.css";

export async function getUser() {
  const API_URL = import.meta.env.VITE_API_URL;

  const res = await fetch(`${API_URL}/api/user`);
  return res.json();
}

function FetchData() {
  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");
  const [fh, setFH] = useState("");
  const [fh_max, setMax] = useState("");
  const [fh_min, setMin] = useState("");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);

  const fetchData = async () => {
    setError("");
    setData(null);

    setIsLoading(true);
    setProgress(15);

    try {
      const res = await fetch(
        `/api/data?lat=${lat}&lon=${lon}&fh=${fh}&fh_min=${fh_min}&fh_max=${fh_max}`
      );

      setProgress(60);

      if (!res.ok) throw new Error(`Server error: ${res.status}`);

      const json = await res.json();

      setProgress(100);

      setTimeout(() => setIsLoading(false), 400);

      setData(json);
    } catch (err) {
      setError(err.message);
      setIsLoading(false);
    }
  };

  React.useEffect(() => {
    const evtSource = new EventSource("http://localhost:5050/progress");

    evtSource.onmessage = (event) => {
      const p = Number(event.data);
      if (!isNaN(p)) {
        setIsLoading(true);
        setProgress(p);

        if (p >= 100) {
          setTimeout(() => setIsLoading(false), 300);
        }
      }
    };

    evtSource.onerror = () => {
      console.log("Progress stream error");
    };

    return () => evtSource.close();
  }, []);

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

        <button onClick={fetchData} className="button">
          Fetch Data
        </button>

        {isLoading && (
          <div className="loading-bar-container">
            <div className="loading-bar" style={{ width: `${progress}%` }}></div>
          </div>
        )}

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
                {[...data]
                  .sort((a, b) => {
                    // 1) Sort by sitrep (model) alphabetically, case-insensitive
                    const sA = (a.sitrep ?? "").toLowerCase();
                    const sB = (b.sitrep ?? "").toLowerCase();
                    if (sA < sB) return -1;
                    if (sA > sB) return 1;

                    // 2) If same sitrep, sort by name alphabetically
                    const nameA = (a.name ?? "").toLowerCase();
                    const nameB = (b.name ?? "").toLowerCase();
                    if (nameA < nameB) return -1;
                    if (nameA > nameB) return 1;

                    // 3) If same name, sort by forecast_time numerically
                    const fA = Number(a.forecast_time ?? 0);
                    const fB = Number(b.forecast_time ?? 0);
                    return fA - fB;
                  })
                  .map((item, i) => (
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