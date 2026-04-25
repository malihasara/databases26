import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import AdminNav from "./AdminNav.jsx";

export default function AdminAttendance() {
  const { clubId, eventId } = useParams();
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");

  const load = () => api.get(`/api/admin/${clubId}/events/${eventId}/attendance`).then(setData).catch(e => setErr(e.message));
  useEffect(() => { load(); }, [clubId, eventId]);

  const checkIn = async (rsvpId) => {
    setErr("");
    try { await api.post(`/api/admin/${clubId}/events/${eventId}/checkin/${rsvpId}`); load(); }
    catch (e) { setErr(e.message); }
  };

  if (err) return <main className="container"><div className="error">{err}</div></main>;
  if (!data) return <main className="container"><p>Loading…</p></main>;

  return (
    <main className="container">
      <h1>Attendance — {data.event.EventTitle}</h1>
      <AdminNav active="events" />
      <p>
        <Link to={`/admin/${clubId}/events`}>← Back to events</Link>{" · "}
        <a href={`/api/admin/${clubId}/export/events/${eventId}/attendance.csv`}>Export CSV</a>
      </p>
      <table className="table">
        <thead><tr><th>Name</th><th>Email</th><th>RSVP</th><th>Checked in</th><th>Method</th><th></th></tr></thead>
        <tbody>
          {data.rsvps.map(r => (
            <tr key={r.RSVPID}>
              <td>{r.FirstName} {r.LastName}</td>
              <td>{r.Email}</td>
              <td>{r.RSVPStatus}</td>
              <td>{r.CheckInTime ? new Date(r.CheckInTime).toLocaleString() : "—"}</td>
              <td>{r.CheckInMethod || "—"}</td>
              <td>{r.RSVPStatus === "Going" && !r.CheckInTime &&
                <button onClick={() => checkIn(r.RSVPID)}>Check in</button>}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
