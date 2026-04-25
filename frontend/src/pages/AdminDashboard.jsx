import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import AdminNav from "./AdminNav.jsx";

export default function AdminDashboard() {
  const { clubId } = useParams();
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get(`/api/admin/${clubId}/`).then(setData).catch(e => setErr(e.message));
  }, [clubId]);

  if (err) return <main className="container"><div className="error">{err}</div></main>;
  if (!data) return <main className="container"><p>Loading…</p></main>;

  return (
    <main className="container">
      <h1>{data.club.ClubName}</h1>
      <AdminNav active="dashboard" />
      <div className="grid">
        <div className="card"><h3>{data.counts.members}</h3><p className="muted">Active members</p></div>
        <div className="card"><h3>{data.counts.pending}</h3><p className="muted">Pending requests</p></div>
        <div className="card"><h3>{data.counts.events}</h3><p className="muted">Scheduled events</p></div>
        <div className="card"><h3>{data.counts.posts}</h3><p className="muted">Announcements</p></div>
      </div>
      <p className="muted">
        <a href={`/api/admin/${clubId}/export/members.csv`}>Export members CSV</a>
      </p>
    </main>
  );
}
