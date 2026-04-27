// Event detail with RSVP + self check-in for students; admins see attendance roster instead.
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import { fmtDateTime } from "../format.js";
import { useAuth } from "../auth.jsx";

const STATUS_LABEL = {
  Going:     "Going",
  Tentative: "Tentative",
  NotGoing:  "Not going",
  NoShow:    "No show",
};

export default function EventDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const isAdmin = user?.AccountType === "Admin";
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [status, setStatus] = useState("Going");

  const load = () => api.get(`/api/events/${id}`).then(d => {
    setData(d);
    if (d.rsvp?.RSVPStatus) setStatus(d.rsvp.RSVPStatus);
  }).catch(e => setErr(e.message));

  useEffect(() => { load(); }, [id]);

  if (err) return <main className="container"><div className="error">{err}</div></main>;
  if (!data) return <main className="container"><p>Loading…</p></main>;

  const { event, rsvp, checked_in, going_count, tentative_count = 0, notgoing_count = 0,
          noshow_count = 0, attended_count = 0, roster = [], is_officer = false } = data;
  const ended = new Date(event.EventEndTime) <= new Date();
  const cancelled = event.EventStatus === "Cancelled";
  const rsvpClosed = ended || cancelled;
  const showRoster = isAdmin || is_officer;

  const saveRsvp = async () => {
    setErr(""); setMsg("");
    try { await api.post(`/api/events/${id}/rsvp`, { status }); setMsg("RSVP saved."); load(); }
    catch (e) { setErr(e.message); }
  };
  const checkIn = async () => {
    setErr(""); setMsg("");
    try { await api.post(`/api/events/${id}/check-in`); setMsg("Checked in."); load(); }
    catch (e) { setErr(e.message); }
  };

  return (
    <main className="container">
      <h1>{event.EventTitle}</h1>
      <p className="muted">{event.ClubName} · {event.EventTypeName} · {event.EventVisibility}</p>
      <p>
        <strong>When:</strong> {fmtDateTime(event.EventStartTime)} – {fmtDateTime(event.EventEndTime)}<br/>
        <strong>Where:</strong> {event.BuildingName} {event.RoomNumber} — {event.HomeAddress}<br/>
        <strong>Capacity:</strong> {going_count} / {event.EventCapacity} going ({event.SeatsLeft} seats left)
      </p>
      <p>{event.EventDescription}</p>

      {msg && <div className="success">{msg}</div>}
      {err && <div className="error">{err}</div>}

      {!isAdmin && (
        rsvpClosed ? (
          <>
            <h2>Your RSVP</h2>
            <div className="info-banner">
              {cancelled
                ? "This event was cancelled. RSVP is closed."
                : "This event has ended. RSVP is closed."}
              {rsvp?.RSVPStatus && (
                <> Your last response was <strong>{rsvp.RSVPStatus}</strong>.
                  {checked_in ? " You were checked in." : ""}
                </>
              )}
            </div>
          </>
        ) : (
          <>
            <h2>Your RSVP</h2>
            <div className="actions">
              <select value={status} onChange={e => setStatus(e.target.value)}>
                <option value="Going">Going</option>
                <option value="Tentative">Tentative</option>
                <option value="NotGoing">Not going</option>
              </select>
              <button onClick={saveRsvp}>Save RSVP</button>
              {rsvp?.RSVPStatus === "Going" && (
                <button onClick={checkIn} disabled={checked_in}>
                  {checked_in ? "Checked in" : "Check in"}
                </button>
              )}
            </div>
          </>
        )
      )}

      {showRoster && (
        <>
          <h2>Roster &amp; attendance</h2>
          <div className="stat-grid">
            <div className="stat"><div className="stat-num">{going_count}</div><div className="stat-lbl">Going</div></div>
            <div className="stat"><div className="stat-num">{tentative_count}</div><div className="stat-lbl">Tentative</div></div>
            <div className="stat"><div className="stat-num">{notgoing_count}</div><div className="stat-lbl">Not going</div></div>
            <div className="stat"><div className="stat-num">{noshow_count}</div><div className="stat-lbl">No show</div></div>
            <div className="stat"><div className="stat-num">{attended_count}</div><div className="stat-lbl">Checked in</div></div>
          </div>
          {roster.length === 0 ? (
            <div className="empty"><p>No RSVPs yet.</p></div>
          ) : (
            <table className="table">
              <thead><tr><th>Name</th><th>Email</th><th>RSVP</th><th>Checked in</th><th>Method</th></tr></thead>
              <tbody>
                {roster.map(r => (
                  <tr key={r.RSVPID}>
                    <td>{r.FirstName} {r.LastName}</td>
                    <td>{r.Email}</td>
                    <td>{STATUS_LABEL[r.RSVPStatus] || r.RSVPStatus}</td>
                    <td>{r.CheckInTime ? fmtDateTime(r.CheckInTime) : "—"}</td>
                    <td>{r.CheckInMethod || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </main>
  );
}
