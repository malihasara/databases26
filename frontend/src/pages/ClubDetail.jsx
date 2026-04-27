// Single-club page: description, join/leave, announcements, upcoming events, officer-side join requests.
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth.jsx";
import { fmtDate, fmtDateTime, fmtTime } from "../format.js";

export default function ClubDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [requests, setRequests] = useState(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");

  const isAdmin = user?.AccountType === "Admin";
  const isOfficer = ["President", "VicePresident", "Officer"].includes(data?.membership?.MembershipRole);
  const canManageRequests = isAdmin || isOfficer;

  const loadClub = () => api.get(`/api/clubs/${id}`).then(setData).catch(e => setErr(e.message));
  const loadRequests = () => api.get(`/api/admin/${id}/requests`).then(d => setRequests(d.requests)).catch(() => setRequests([]));

  useEffect(() => { loadClub(); }, [id]);
  useEffect(() => {
    if (canManageRequests) loadRequests();
    else setRequests(null);
  }, [id, canManageRequests]);

  if (err) return <main className="container"><div className="error">{err}</div></main>;
  if (!data) return <main className="container"><p>Loading…</p></main>;

  const { club, membership, has_pending, announcements, upcoming } = data;

  const join = async () => {
    setErr(""); setMsg("");
    try { await api.post(`/api/clubs/${id}/join`); setMsg("Join request sent."); loadClub(); }
    catch (e) { setErr(e.message); }
  };
  const leave = async () => {
    setErr(""); setMsg("");
    try { await api.post(`/api/clubs/${id}/leave`); setMsg("You have left the club."); loadClub(); }
    catch (e) { setErr(e.message); }
  };
  const decideRequest = async (rid, action) => {
    setErr(""); setMsg("");
    try {
      await api.post(`/api/admin/${id}/requests/${rid}/${action}`);
      setMsg(`Request ${action}d.`);
      loadRequests(); loadClub();
    } catch (e) { setErr(e.message); }
  };

  const pendingRequests = (requests || []).filter(r => r.RequestStatus === "Pending");

  return (
    <main className="container">
      <header className="page-head">
        <h1>{club.ClubName}</h1>
        <p className="muted">
          {(club.Categories || []).map(c => c.CategoryName).join(" · ") || "—"} · created {fmtDate(club.ClubCreationDate)}
        </p>
      </header>

      <div className="card">
        <p>{club.ClubDescription}</p>

        {msg && <div className="success">{msg}</div>}
        <div className="actions">
          {isAdmin ? (
            <Link className="badge" to={`/admin/${club.ClubID}`}>Admin tools →</Link>
          ) : membership && membership.MembershipStatus === "Active" ? (
            <>
              <span className="badge">You are a {membership.MembershipRole}</span>
              {isOfficer && <Link className="badge" to={`/admin/${club.ClubID}`}>Open admin →</Link>}
              <button className="danger" onClick={leave}>Leave club</button>
            </>
          ) : has_pending ? (
            <span className="badge">Request pending</span>
          ) : (
            <button onClick={join}>Request to join</button>
          )}
        </div>
      </div>

      {canManageRequests && (
        <section>
          <h2 className="section-h">
            Pending join requests
            {pendingRequests.length > 0 && <span className="role-pill">{pendingRequests.length}</span>}
          </h2>
          {requests === null ? <p>Loading…</p> :
            pendingRequests.length === 0 ? (
              <div className="empty"><p>No pending requests right now.</p></div>
            ) : (
              <ul className="list">
                {pendingRequests.map(r => (
                  <li key={r.RequestID} className="request-row">
                    <div>
                      <strong>{r.FirstName} {r.LastName}</strong>
                      <span className="muted"> · {r.Email}</span>
                      <div className="muted small">requested {fmtDateTime(r.RequestTime)}</div>
                    </div>
                    <div className="actions">
                      <button onClick={() => decideRequest(r.RequestID, "approve")}>Approve</button>
                      <button className="danger" onClick={() => decideRequest(r.RequestID, "reject")}>Reject</button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
        </section>
      )}

      <section>
        <h2 className="section-h">Announcements</h2>
        {announcements.length === 0 ? (
          <div className="empty"><p>No announcements yet.</p></div>
        ) : (
          <div className="grid">
            {announcements.map(a => (
              <article key={a.AnnouncementID} className="card announcement">
                <header>
                  <h3>{a.AnnouncementTitle}</h3>
                  <span className="muted small">{fmtDate(a.AnnouncementDate)}</span>
                </header>
                {a.AnnouncementVisibility === "MembersOnly" && (
                  <span className="role-pill">Members only</span>
                )}
                <p>{a.AnnouncementBody}</p>
              </article>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="section-h">Upcoming events</h2>
        {upcoming.length === 0 ? (
          <div className="empty"><p>No upcoming events.</p></div>
        ) : (
          <div className="club-grid">
            {upcoming.map(e => (
              <Link key={e.EventID} className="club-card" to={`/events/${e.EventID}`}>
                <div className="club-card-head">
                  <span className="role-pill">{e.EventVisibility}</span>
                  <span className="muted small">{fmtDate(e.EventStartTime)}</span>
                </div>
                <h3>{e.EventTitle}</h3>
                <p className="muted small">{fmtTime(e.EventStartTime)}</p>
              </Link>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
