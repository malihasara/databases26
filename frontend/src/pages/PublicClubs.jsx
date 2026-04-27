// Unauthenticated public club directory.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function PublicClubs() {
  const [clubs, setClubs] = useState(null);
  const [q, setQ] = useState("");
  const [err, setErr] = useState("");

  const load = () => {
    const qs = q ? `?q=${encodeURIComponent(q)}` : "";
    api.get(`/api/public/clubs${qs}`).then(d => setClubs(d.clubs)).catch(e => setErr(e.message));
  };
  useEffect(() => { load(); }, []);

  return (
    <main className="container">
      <h1>Public Club Directory</h1>
      <p className="muted">Browse without an account. <Link to="/register">Register</Link> to join.</p>
      <form className="filters" onSubmit={e => { e.preventDefault(); load(); }}>
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="Search by name…" />
        <button type="submit">Search</button>
      </form>
      {err && <div className="error">{err}</div>}
      {!clubs ? <p>Loading…</p> : clubs.length === 0 ? <p className="muted">No clubs.</p> : (
        <div className="grid">
          {clubs.map(c => (
            <div key={c.ClubID} className="card">
              <h3>{c.ClubName}</h3>
              <p className="muted">{c.Categories || "—"}</p>
              <p>{c.ClubDescription}</p>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
