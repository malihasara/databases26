import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import AdminNav from "./AdminNav.jsx";
import { fmtDateTime } from "../format.js";

export default function AdminEvents() {
  const { clubId } = useParams();
  const [events, setEvents] = useState(null);
  const [err, setErr] = useState("");

  const load = () => api.get(`/api/admin/${clubId}/events`).then(d => setEvents(d.events)).catch(e => setErr(e.message));
  useEffect(() => { load(); }, [clubId]);

  const remove = async (eid) => {
    setErr("");
    if (!confirm("Delete event?")) return;
    try { await api.post(`/api/admin/${clubId}/events/${eid}/delete`); load(); }
    catch (e) { setErr(e.message); }
  };

  return (
    <main className="container">
      <h1>Events</h1>
      <AdminNav active="events" />
      <p><Link className="badge" to={`/admin/${clubId}/events/new`}>+ New event</Link></p>
      {err && <div className="error">{err}</div>}
      {!events ? <p>Loading…</p> : (
        <table className="table">
          <thead><tr><th>Title</th><th>Start</th><th>Status</th><th>Visibility</th><th>Going / Cap</th><th>Attended</th><th></th></tr></thead>
          <tbody>
            {events.map(e => (
              <tr key={e.EventID}>
                <td>{e.EventTitle}</td>
                <td>{fmtDateTime(e.EventStartTime)}</td>
                <td>{e.EventStatus}</td>
                <td>{e.EventVisibility}</td>
                <td>{e.going} / {e.EventCapacity}</td>
                <td>{e.attended}</td>
                <td>
                  <Link to={`/admin/${clubId}/events/${e.EventID}/edit`}>Edit</Link>{" | "}
                  <Link to={`/admin/${clubId}/events/${e.EventID}/attendance`}>Attendance</Link>{" | "}
                  <button className="danger" onClick={() => remove(e.EventID)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
