import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import AdminNav from "./AdminNav.jsx";

export default function AdminAnnouncements() {
  const { clubId } = useParams();
  const [items, setItems] = useState(null);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [err, setErr] = useState("");

  const load = () => api.get(`/api/admin/${clubId}/announcements/`).then(d => setItems(d.announcements)).catch(e => setErr(e.message));
  useEffect(() => { load(); }, [clubId]);

  const post = async (e) => {
    e.preventDefault();
    setErr("");
    try {
      await api.post(`/api/admin/${clubId}/announcements/`, { title, body });
      setTitle(""); setBody("");
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
        <button type="submit">Post</button>
      </form>
      {!items ? <p>Loading…</p> : (
        <ul className="list">
          {items.length === 0 && <li className="muted">No announcements yet.</li>}
          {items.map(a => (
            <li key={a.AnnouncementID}>
              <strong>{a.AnnouncementTitle}</strong>
              <span className="muted"> — {a.FirstName} {a.LastName} on {a.AnnouncementDate?.slice(0, 10)}</span>
              <p>{a.AnnouncementBody}</p>
              <button className="danger" onClick={() => remove(a.AnnouncementID)}>Delete</button>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
