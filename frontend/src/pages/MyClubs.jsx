import { useEffect, useState } from "react";
import { Link, Navigate, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { fmtDateTime } from "../format.js";
import { useAuth } from "../auth.jsx";

function ClubCard({ club, manage }) {
  return (
    <Link className="club-card" to={`/clubs/${club.ClubID}`}>
      <div className="club-card-head">
        <span className="role-pill">{club.MembershipRole}</span>
        <span className="muted small">{club.CategoryName}</span>
      </div>
      <h3>{club.ClubName}</h3>
      <p className="club-desc">{club.ClubDescription}</p>
      {manage && (
        <Link
          className="manage-link"
          to={`/admin/${club.ClubID}`}
          onClick={(e) => e.stopPropagation()}
        >
          Open admin →
        </Link>
      )}
    </Link>
  );
}

export default function MyClubs() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [params] = useSearchParams();
  const facultyPending = params.get("facultyPending") === "1";

  useEffect(() => {
    if (user?.AccountType === "Faculty") return;
    api.get("/api/my-clubs/").then(setData).catch(e => setErr(e.message));
  }, [user?.AccountType]);

  if (user?.AccountType === "Faculty") {
    return <Navigate to="/admin-portal" replace />;
  }
  if (err) return <main className="container"><div className="error">{err}</div></main>;
  if (!data) return <main className="container"><p>Loading…</p></main>;

  const empty = data.managing.length === 0 && data.member.length === 0;

  return (
    <main className="container">
      <header className="page-head">
        <h1>My Clubs</h1>
        <p className="muted">Clubs you lead and clubs you belong to.</p>
      </header>

      {facultyPending && (
        <div className="info-banner">
          <strong>Faculty access requested.</strong> Your account is currently a student account.
          An existing faculty member will review your request and promote you once approved.
        </div>
      )}

      {empty && (
        <div className="empty">
          <p>You haven't joined any clubs yet.</p>
          <Link className="btn primary" to="/clubs">Browse the directory</Link>
        </div>
      )}

      {data.managing.length > 0 && (
        <section className="manage-section">
          <h2 className="section-h">Clubs you manage</h2>
          <div className="club-grid">
            {data.managing.map(c => <ClubCard key={c.ClubID} club={c} manage />)}
          </div>
        </section>
      )}

      {data.member.length > 0 && (
        <section className="member-section">
          <h2 className="section-h">Clubs you're a member of</h2>
          <div className="club-grid">
            {data.member.map(c => <ClubCard key={c.ClubID} club={c} />)}
          </div>
        </section>
      )}

      {data.pending.length > 0 && (
        <section>
          <h2 className="section-h">Pending requests</h2>
          <ul className="list">
            {data.pending.map(p => (
              <li key={p.ClubID}>
                <strong>{p.ClubName}</strong>
                <span className="muted"> — requested {fmtDateTime(p.RequestTime)}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
