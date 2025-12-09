import React, { useState } from "react";
import "./FetchData.css";

function convertThreshold(threshold) {
  if (!threshold) return threshold;

  let str = String(threshold).trim();
  let prefix = "";
  if (str.startsWith(">")) {
    prefix = "> ";
    str = str.slice(1).trim();
  } else if (str.startsWith("<")) {
    prefix = "< ";
    str = str.slice(1).trim();
  }

  if (/m\s*s\*\*-1/i.test(str)) {
    const val = parseFloat(str);
    if (!isNaN(val)) return `${prefix}${(val * 2.23694).toFixed(2)} mph`;
  }

  if (/kg\s*m\*\*-2/i.test(str)) {
    const val = parseFloat(str);
    if (!isNaN(val)) return `${prefix}${(val / 25.4).toFixed(2)} in`;
  }

  if (/k$/i.test(str)) {
    const val = parseFloat(str);
    if (!isNaN(val)) {
      const f = ((val - 273.15) * 9/5 + 32).toFixed(2);
      return `${prefix}${f} °F`;
    }
  }

  return threshold;
}

function FetchData() {
  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");

  // ⭐ Single FH
  const [dayOffset, setDayOffset] = useState(0);
  const [hour, setHour] = useState("");

  // ⭐ Range FH
  const [dayOffsetMin, setDayOffsetMin] = useState(0);
  const [hourMin, setHourMin] = useState("");
  const [dayOffsetMax, setDayOffsetMax] = useState(0);
  const [hourMax, setHourMax] = useState("");

  const [useRange, setUseRange] = useState(false);

  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);

  const fetchData = async () => {
    setError("");
    setData(null);
    setIsLoading(true);
    setProgress(15);

    const params = new URLSearchParams();
    params.append("lat", lat);
    params.append("lon", lon);

    if (useRange) {
      params.append("dayOffset_min", dayOffsetMin);
      params.append("hour_min", hourMin);
      params.append("dayOffset_max", dayOffsetMax);
      params.append("hour_max", hourMax);
    } else {
      params.append("dayOffset", dayOffset);
      params.append("hour", hour);
    }

    try {
      const res = await fetch(`/api/data?${params.toString()}`);
      setProgress(60);

      if (!res.ok) {
          const msg = await res.json().catch(() => null);
          throw new Error(
            msg?.error || `Server error: ${res.status}`
          );
        }

        const json = await res.json();
      setProgress(100);

      setTimeout(() => setIsLoading(false), 400);
      setData(json);

    } catch (err) {
      setError(err.message);
      setIsLoading(false);
    }
  };

  return (
    <div className="fetch-container">
      <div className="fetch-card">
        <h2 className="title">Cinder ⛅</h2>

        <input type="number" placeholder="Latitude" value={lat}
               onChange={(e) => setLat(e.target.value)}
               className="input"/>

        <input type="number" placeholder="Longitude" value={lon}
               onChange={(e) => setLon(e.target.value)}
               className="input"/>
        
        {!useRange && (
  <>
    <select value={dayOffset} onChange={(e) => setDayOffset(Number(e.target.value))} className="input">
      <option value={0}>Today</option>
      <option value={1}>Tomorrow</option>
    </select>

    <input type="number" placeholder="Local Hour (0–23)" value={hour}
           onChange={(e) => setHour(e.target.value)} className="input"/>
  </>
)}

{useRange && (
  <>
    <h3 className="range-title">Range Start</h3>
    <select value={dayOffsetMin} onChange={(e) => setDayOffsetMin(Number(e.target.value))} className="input">
      <option value={0}>Today</option>
      <option value={1}>Tomorrow</option>
    </select>
    <input type="number" placeholder="Start Hour" value={hourMin}
           onChange={(e) => setHourMin(e.target.value)} className="input"/>

    <h3 className="range-title">Range End</h3>
    <select value={dayOffsetMax} onChange={(e) => setDayOffsetMax(Number(e.target.value))} className="input">
      <option value={0}>Today</option>
      <option value={1}>Tomorrow</option>
    </select>
    <input type="number" placeholder="End Hour" value={hourMax}
           onChange={(e) => setHourMax(e.target.value)} className="input"/>
  </>
)}

<div className="toggle-row">
  <label className="toggle-switch-container">
    <input
      type="checkbox"
      className="toggle-input"
      checked={useRange}
      onChange={(e) => setUseRange(e.target.checked)}
    />
    <span className="toggle-switch"></span>
  </label>
  <span className="toggle-label">Use Range</span>
</div>

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
                  const sA = (a.sitrep ?? "").toLowerCase();
                  const sB = (b.sitrep ?? "").toLowerCase();
                  if (sA < sB) return -1;
                  if (sA > sB) return 1;

                  const nA = (a.name ?? "").toLowerCase();
                  const nB = (b.name ?? "").toLowerCase();
                  if (nA < nB) return -1;
                  if (nA > nB) return 1;

                  return Number(a.forecast_time ?? 0) -
                         Number(b.forecast_time ?? 0);
                })
                .map((item, i) => (
                  <tr key={i}>
                    <td>
                      {item.sitrep ?? "-"}{" "}
                      {(item.model_run || item.anal_date) && (
                        <span className="model-run">
                          {item.model_run ?? "?"} — {item.anal_date ? item.anal_date.split(" ")[0] : "?"}
                        </span>
                      )}
                    </td>
                    <td>{item.name ?? "—"}</td>
                    <td>{item.threshold ? convertThreshold(item.threshold) : "—"}</td>
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