import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import AdminNav from "./AdminNav.jsx";

const toLocalInput = (iso) => iso ? iso.replace(" ", "T").slice(0, 16) : "";

export default function AdminEventForm({ mode }) {
  const { clubId, eventId } = useParams();
  const navigate = useNavigate();
  const [opts, setOpts] = useState(null);
  const [form, setForm] = useState({
    title: "", description: "", start: "", end: "",
    capacity: 30, visibility: "Public",
    location_id: "", type_id: "", status: "Scheduled",
  });
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get(`/api/admin/${clubId}/event-form-options`).then(setOpts).catch(e => setErr(e.message));
    if (mode === "edit") {
      api.get(`/api/admin/${clubId}/events/${eventId}`).then(d => {
        const e = d.event;
        setForm({
          title: e.EventTitle,
          description: e.EventDescription,
          start: toLocalInput(e.EventStartTime),
          end: toLocalInput(e.EventEndTime),
          capacity: e.EventCapacity,
          visibility: e.EventVisibility,
          location_id: e.LocationID,
          type_id: e.EventTypeID,
          status: e.EventStatus,
        });
      }).catch(e => setErr(e.message));
    }
  }, [clubId, eventId, mode]);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const onSubmit = async (e) => {
    e.preventDefault();
    setErr("");
    try {
      if (mode === "create") await api.post(`/api/admin/${clubId}/events`, form);
      else await api.post(`/api/admin/${clubId}/events/${eventId}`, form);
      navigate(`/admin/${clubId}/events`);
    } catch (e) { setErr(e.message); }
  };

  return (
    <main className="container">
      <h1>{mode === "create" ? "New event" : "Edit event"}</h1>
      <AdminNav active="events" />
      {err && <div className="error">{err}</div>}
      {!opts ? <p>Loading…</p> : (
        <form className="card" onSubmit={onSubmit}>
          <label>Title<input value={form.title} onChange={set("title")} required /></label>
          <label>Description<textarea rows={4} value={form.description} onChange={set("description")} required /></label>
          <label>Start<input type="datetime-local" value={form.start} onChange={set("start")} required /></label>
          <label>End<input type="datetime-local" value={form.end} onChange={set("end")} required /></label>
          <label>Capacity<input type="number" min="1" value={form.capacity} onChange={set("capacity")} required /></label>
          <label>Visibility
            <select value={form.visibility} onChange={set("visibility")}>
              <option value="Public">Public</option>
              <option value="MembersOnly">Members only</option>
            </select>
          </label>
          <label>Location
            <select value={form.location_id} onChange={set("location_id")} required>
              <option value="">—</option>
              {opts.locations.map(l => <option key={l.LocationID} value={l.LocationID}>{l.BuildingName} {l.RoomNumber}</option>)}
            </select>
          </label>
          <label>Type
            <select value={form.type_id} onChange={set("type_id")} required>
              <option value="">—</option>
              {opts.types.map(t => <option key={t.EventTypeID} value={t.EventTypeID}>{t.EventTypeName}</option>)}
            </select>
          </label>
          {mode === "edit" && (
            <label>Status
              <select value={form.status} onChange={set("status")}>
                <option value="Scheduled">Scheduled</option>
                <option value="Cancelled">Cancelled</option>
                <option value="Completed">Completed</option>
              </select>
            </label>
          )}
          <button type="submit">{mode === "create" ? "Create event" : "Save changes"}</button>
        </form>
      )}
    </main>
  );
}
