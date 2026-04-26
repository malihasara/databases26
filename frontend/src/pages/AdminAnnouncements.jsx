import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import AdminNav from "./AdminNav.jsx";
import { fmtDate } from "../format.js";

export default function AdminAnnouncements() {
  const { clubId } = useParams();
  const [items, setItems] = useState(null);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [visibility, setVisibility] = useState("Public");
  const [err, setErr] = useState("");

  const load = () => api.get(`/api/admin/${clubId}/announcements/`).then(d => setItems(d.announcements)).catch(e => setErr(e.message));
  useEffect(() => { load(); }, [clubId]);

  const post = async (e) => {
    e.preventDefault();
    setErr("");
    try {
      await api.post(`/api/admin/${clubId}/announcements/`, { title, body, visibility });
      setTitle(""); setBody(""); setVisibility("Public");
      load();
    } catch (e) { setErr(e.message); }
  };
  const remove = async (id) => {
    setErr("");
    if (!confirm("Delete this announcement?")) return;
    try { await api.post(`/api/admin/${clubId}/announcements/${id}/delete`); load(); }
    catch (e) { setErr(e.message); }
  };

  return (
    <main className="container">
      <h1>Announcements</h1>
      <AdminNav active="announcements" />
      {err && <div className="error">{err}</div>}
      <form className="card" onSubmit={post}>
        <label>Title<input value={title} onChange={e => setTitle(e.target.value)} required /></label>
        <label>Body<textarea rows={3} value={body} onChange={e => setBody(e.target.value)} required /></label>
        <label>Visibility
          <select value={visibility} onChange={e => setVisibility(e.target.value)}>
            <option value="Public">Public — anyone can read</option>
            <option value="MembersOnly">Members only — only active members</option>
          </select>
        </label>
        <button type="submit">Post</button>
      </form>
      {!items ? <p>Loading…</p> : (
        <ul className="list">
          {items.length === 0 && <li className="muted">No announcements yet.</li>}
          {items.map(a => (
            <li key={a.AnnouncementID}>
              <strong>{a.AnnouncementTitle}</strong>
              <span className="role-pill" style={{ marginLeft: "0.5rem" }}>{a.AnnouncementVisibility}</span>
              <span className="muted"> — {a.FirstName} {a.LastName} on {fmtDate(a.AnnouncementDate)}</span>
              <p>{a.AnnouncementBody}</p>
              <button className="danger" onClick={() => remove(a.AnnouncementID)}>Delete</button>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
