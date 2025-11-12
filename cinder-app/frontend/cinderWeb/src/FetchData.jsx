import React, { useState } from "react";

function FetchData() {
  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");
  const [fh , setFH] = useState("");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const fetchData = async () => {
    setError("");
    setData(null);

    try {
      const res = await fetch(`/api/data?lat=${lat}&lon=${lon}`);
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const json = await res.json();
      setData(json);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div style={{ marginTop: "2rem" }}>
      <input
        type="number"
        step="any"
        placeholder="Latitude"
        value={lat}
        onChange={(e) => setLat(e.target.value)}
        style={{ marginRight: "1rem", padding: "0.5rem" }}
      />
      <input
        type="number"
        step="any"
        placeholder="Longitude"
        value={lon}
        onChange={(e) => setLon(e.target.value)}
        style={{ marginRight: "1rem", padding: "0.5rem" }}
      />
      <input
        type="number"
        step="any"
        placeholder="Forecast Hour"
        value={fh}
        onChange ={(e) => setFH(e.target.value)}
        style={{ marginRight: "1rem", padding: "0.5rem"}}
      />
      <button onClick={fetchData} style={{ padding: "0.5rem 1rem" }}>
        Fetch Data
      </button>

      {error && <p style={{ color: "red" }}>{error}</p>}
      {data && (
       <pre
  style={{
    backgroundColor: "#1e1e1e",
    color: "#00ffcc",
    padding: "1rem",
    borderRadius: "8px",
    overflowX: "auto",
  }}
>
  {JSON.stringify(data, null, 2)}
</pre>
      )}
    </div>
  );
}

export default FetchData;