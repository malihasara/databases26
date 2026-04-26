import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import { fmtDateTime } from "../format.js";

export default function EventDetail() {
  const { id } = useParams();
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

  const { event, rsvp, checked_in, going_count } = data;

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
    </main>
  );
}
