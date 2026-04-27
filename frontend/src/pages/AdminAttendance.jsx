// Per-event attendance roster with Mark Present / No show / Reset officer actions.
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import AdminNav from "./AdminNav.jsx";
import { fmtDateTime } from "../format.js";

function attendanceState(r) {
  if (r.CheckInTime) return "Present";
  if (r.RSVPStatus === "NoShow") return "No show";
  return r.RSVPStatus;
}

export default function AdminAttendance() {
  const { clubId, eventId } = useParams();
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");

  const load = () => api.get(`/api/admin/${clubId}/events/${eventId}/attendance`).then(setData).catch(e => setErr(e.message));
  useEffect(() => { load(); }, [clubId, eventId]);

  const action = (path) => async (rsvpId) => {
    setErr(""); setMsg("");
    try {
      await api.post(`/api/admin/${clubId}/events/${eventId}/${path}/${rsvpId}`);
      load();
    } catch (e) { setErr(e.message); }
  };
  const markPresent = action("checkin");
  const markNoShow  = action("no-show");
  const resetRsvp   = action("reset");

  if (err && !data) return <main className="container"><div className="error">{err}</div></main>;
  if (!data) return <main className="container"><p>Loading…</p></main>;

  return (
    <main className="container">
      <h1>Attendance — {data.event.EventTitle}</h1>
      <AdminNav active="events" />
      <p>
        <Link to={`/admin/${clubId}/events`}>← Back to events</Link>{" · "}
        <a href={`/api/admin/${clubId}/export/events/${eventId}/attendance.csv`}>Export CSV</a>
      </p>
      {err && <div className="error">{err}</div>}
      {msg && <div className="success">{msg}</div>}
      <p className="muted">
        Mark each attendee as <strong>Present</strong> or <strong>No show</strong> after the event.
        No-shows free up capacity so other students can RSVP.
      </p>
      <table className="table">
        <thead>
          <tr>
            <th>Name</th><th>Email</th><th>State</th>
            <th>Checked in</th><th>Method</th><th></th>
          </tr>
        </thead>
        <tbody>
          {data.rsvps.map(r => {
            const present = !!r.CheckInTime;
            const noShow  = r.RSVPStatus === "NoShow";
            return (
              <tr key={r.RSVPID}>
                <td>{r.FirstName} {r.LastName}</td>
                <td>{r.Email}</td>
                <td>
                  <span className={`role-pill state-${attendanceState(r).replace(/\s+/g, "")}`}>
                    {attendanceState(r)}
                  </span>
                </td>
                <td>{r.CheckInTime ? fmtDateTime(r.CheckInTime) : "—"}</td>
                <td>{r.CheckInMethod || "—"}</td>
                <td>
                  {!present && (
                    <button onClick={() => markPresent(r.RSVPID)}>Mark Present</button>
                  )}
                  {!noShow && !present && (
                    <button className="danger" onClick={() => markNoShow(r.RSVPID)}>No show</button>
                  )}
                  {(present || noShow) && (
                    <button className="danger" onClick={() => resetRsvp(r.RSVPID)}>Reset</button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </main>
  );
}
