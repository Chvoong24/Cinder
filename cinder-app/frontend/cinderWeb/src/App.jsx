import "./App.css";
import FetchData from "./FetchData";

function App() {
  return (
    <main className="app-shell">
      <header className="app-header">
        <h1>Cinder Weather Desk</h1>
        <p className="app-tagline">
          Type a Connecticut city and pull the latest NBM ensemble mean.
        </p>
      </header>

      <FetchData />
    </main>
  );
}

export default App;
