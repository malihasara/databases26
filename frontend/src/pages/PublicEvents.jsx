import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { fmtDateTime } from "../format.js";

export default function PublicEvents() {
  const [events, setEvents] = useState(null);
  const [q, setQ] = useState("");
  const [err, setErr] = useState("");

  const load = () => {
    const qs = q ? `?q=${encodeURIComponent(q)}` : "";
    api.get(`/api/public/events${qs}`).then(d => setEvents(d.events)).catch(e => setErr(e.message));
  };
  useEffect(() => { load(); }, []);

  return (
    <main className="container">
      <h1>Public Events</h1>
      <p className="muted"><Link to="/register">Register</Link> to RSVP and check in.</p>
      <form className="filters" onSubmit={e => { e.preventDefault(); load(); }}>
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="Search by title…" />
        <button type="submit">Search</button>
      </form>
      {err && <div className="error">{err}</div>}
      {!events ? <p>Loading…</p> : events.length === 0 ? <p className="muted">No public events.</p> : (
        <ul className="list">
          {events.map(e => (
            <li key={e.EventID}>
              <strong>{e.EventTitle}</strong>
              <span className="muted"> — {e.ClubName} · {fmtDateTime(e.EventStartTime)} · {e.BuildingName} {e.RoomNumber}</span>
              <p>{e.EventDescription}</p>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
