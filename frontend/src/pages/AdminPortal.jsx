import { useEffect, useState } from "react";
import { Link, NavLink, Route, Routes } from "react-router-dom";
import { api } from "../api";


function PortalNav({ pendingCount }) {
  return (
    <nav className="subnav">
      <NavLink to="/admin-portal" end>Overview</NavLink>
      <NavLink to="/admin-portal/clubs">Clubs</NavLink>
      <NavLink to="/admin-portal/users">Users</NavLink>
      <NavLink to="/admin-portal/approvals">
        Faculty approvals
        {pendingCount > 0 && <span className="role-pill" style={{ marginLeft: "0.5rem" }}>{pendingCount}</span>}
      </NavLink>
      <NavLink to="/admin-portal/attendance">Attendance</NavLink>
    </nav>
  );
}


function Overview() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  useEffect(() => { api.get("/api/admin-portal/overview").then(setData).catch(e => setErr(e.message)); }, []);
  if (err) return <div className="error">{err}</div>;
  if (!data) return <p>Loading…</p>;
  const { counts, clubs } = data;
  const stats = [
    ["Users",        counts.users],
    ["Faculty",      counts.faculty],
    ["Clubs",        counts.clubs],
    ["Scheduled events", counts.scheduled_events],
    ["Going RSVPs",  counts.going_rsvps],
    ["Check-ins",    counts.check_ins],
  ];
  return (
    <>
      <div className="stat-grid">
        {stats.map(([label, n]) => (
          <div key={label} className="stat">
            <div className="stat-num">{n}</div>
            <div className="stat-lbl">{label}</div>
          </div>
        ))}
      </div>
      <h2 className="section-h">All clubs</h2>
      <table className="table">
        <thead><tr><th>Club</th><th>Category</th><th>Members</th><th>Events</th><th>Check-ins</th><th></th></tr></thead>
        <tbody>
          {clubs.map(c => (
            <tr key={c.ClubID}>
              <td>{c.ClubName}</td>
              <td>{c.CategoryName}</td>
              <td>{c.members}</td>
              <td>{c.events}</td>
              <td>{c.check_ins}</td>
              <td><Link to={`/admin/${c.ClubID}`}>Manage</Link></td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}


function Users() {
  const [users, setUsers] = useState(null);
  const [q, setQ] = useState("");
  const [err, setErr] = useState("");

  const load = (query = q) => {
    const qs = query ? `?q=${encodeURIComponent(query)}` : "";
    api.get(`/api/admin-portal/users${qs}`).then(d => setUsers(d.users)).catch(e => setErr(e.message));
  };
  useEffect(() => { load(""); }, []);

  const setRole = async (uid, account_type) => {
    setErr("");
    try { await api.post(`/api/admin-portal/users/${uid}/account-type`, { account_type }); load(); }
    catch (e) { setErr(e.message); }
  };
  const setStatus = async (uid, status) => {
    setErr("");
    try { await api.post(`/api/admin-portal/users/${uid}/status`, { status }); load(); }
    catch (e) { setErr(e.message); }
  };

  return (
    <>
      <p className="muted">
        New users sign up themselves on the registration page. Faculty access requests appear under
        <Link to="/admin-portal/approvals"> Faculty approvals</Link>.
      </p>
      <form onSubmit={e => { e.preventDefault(); load(); }} className="filters">
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="Search name or email…" />
        <button type="submit">Search</button>
      </form>

      {err && <div className="error">{err}</div>}
      {!users ? <p>Loading…</p> : (
        <table className="table">
          <thead><tr><th>Name</th><th>Email</th><th>Type</th><th>Status</th><th>Created</th></tr></thead>
          <tbody>
            {users.map(u => (
              <tr key={u.UserID}>
                <td>{u.FirstName} {u.LastName}</td>
                <td>{u.Email}</td>
                <td>
                  <select value={u.AccountType} onChange={e => setRole(u.UserID, e.target.value)}>
                    <option value="Student">Student</option>
                    <option value="Faculty">Faculty</option>
                  </select>
                </td>
                <td>
                  <select value={u.AccountStatus} onChange={e => setStatus(u.UserID, e.target.value)}>
                    <option value="Active">Active</option>
                    <option value="Inactive">Inactive</option>
                  </select>
                </td>
                <td>{u.AccountCreationDate?.slice(0, 10)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}


function FacultyApprovals({ onChange }) {
  const [rows, setRows] = useState(null);
  const [err, setErr] = useState("");

  const load = () => api.get("/api/admin-portal/faculty-requests")
    .then(d => { setRows(d.requests); onChange?.(d.requests.length); })
    .catch(e => setErr(e.message));
  useEffect(() => { load(); }, []);

  const decide = async (uid, action) => {
    setErr("");
    try { await api.post(`/api/admin-portal/faculty-requests/${uid}/${action}`); load(); }
    catch (e) { setErr(e.message); }
  };

  if (err) return <div className="error">{err}</div>;
  if (!rows) return <p>Loading…</p>;
  if (rows.length === 0) {
    return <div className="empty"><p>No pending faculty access requests.</p></div>;
  }

  return (
    <ul className="list">
      {rows.map(r => (
        <li key={r.UserID} className="request-row">
          <div>
            <strong>{r.FirstName} {r.LastName}</strong>
            <span className="muted"> · {r.Email}</span>
            <div className="muted small">
              requested {r.FacultyRequestTime ? new Date(r.FacultyRequestTime).toLocaleString() : "—"}
            </div>
          </div>
          <div className="actions">
            <button onClick={() => decide(r.UserID, "approve")}>Approve faculty access</button>
            <button className="danger" onClick={() => decide(r.UserID, "reject")}>Reject</button>
          </div>
        </li>
      ))}
    </ul>
  );
}


function Attendance() {
  const [events, setEvents] = useState(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    api.get("/api/admin-portal/attendance").then(d => setEvents(d.events)).catch(e => setErr(e.message));
  }, []);
  if (err) return <div className="error">{err}</div>;
  if (!events) return <p>Loading…</p>;
  return (
    <table className="table">
      <thead><tr><th>Event</th><th>Club</th><th>Start</th><th>Going</th><th>Attended</th><th>Capacity</th></tr></thead>
      <tbody>
        {events.map(e => (
          <tr key={e.EventID}>
            <td>{e.EventTitle}</td>
            <td>{e.ClubName}</td>
            <td>{new Date(e.EventStartTime).toLocaleString()}</td>
            <td>{e.going}</td>
            <td>{e.attended}</td>
            <td>{e.EventCapacity}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}


function Clubs() {
  const [opts, setOpts] = useState(null);
  const [overview, setOverview] = useState(null);
  const [err, setErr] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [confirmId, setConfirmId] = useState(null);
  const [form, setForm] = useState({ name: "", description: "", category_id: "", owner_user_id: "" });

  const load = () => {
    api.get("/api/admin-portal/club-options").then(setOpts).catch(e => setErr(e.message));
    api.get("/api/admin-portal/overview").then(setOverview).catch(e => setErr(e.message));
  };
  useEffect(() => { load(); }, []);

  const onCreate = async (e) => {
    e.preventDefault();
    setErr("");
    try {
      await api.post("/api/admin-portal/clubs", form);
      setShowCreate(false);
      setForm({ name: "", description: "", category_id: "", owner_user_id: "" });
      load();
    } catch (e) { setErr(e.message); }
  };

  const onDelete = async (clubId) => {
    setErr("");
    try {
      await api.post(`/api/admin-portal/clubs/${clubId}/delete`);
      setConfirmId(null);
      load();
    } catch (e) { setErr(e.message); }
  };

  const target = confirmId ? overview?.clubs.find(c => c.ClubID === confirmId) : null;

  return (
    <>
      <div className="page-actions">
        <div />
        <button className="primary" onClick={() => setShowCreate(s => !s)}>
          {showCreate ? "Cancel" : "+ New club"}
        </button>
      </div>

      {showCreate && (
        <form className="card create-user" onSubmit={onCreate}>
          <label>Club name<input value={form.name} onChange={e => setForm({...form, name: e.target.value})} required /></label>
          <label>Description<textarea rows={3} value={form.description} onChange={e => setForm({...form, description: e.target.value})} required /></label>
          <div className="form-row">
            <label>Category
              <select value={form.category_id} onChange={e => setForm({...form, category_id: e.target.value})} required>
                <option value="">—</option>
                {opts?.categories.map(c => <option key={c.CategoryID} value={c.CategoryID}>{c.CategoryName}</option>)}
              </select>
            </label>
            <label>Owner
              <select value={form.owner_user_id} onChange={e => setForm({...form, owner_user_id: e.target.value})} required>
                <option value="">—</option>
                {opts?.owners.map(o => <option key={o.UserID} value={o.UserID}>{o.FirstName} {o.LastName} · {o.Email}</option>)}
              </select>
            </label>
          </div>
          <button type="submit" className="primary">Create club</button>
        </form>
      )}

      {err && <div className="error">{err}</div>}
      {!overview ? <p>Loading…</p> : (
        <table className="table">
          <thead><tr><th>Club</th><th>Category</th><th>Members</th><th>Events</th><th></th></tr></thead>
          <tbody>
            {overview.clubs.map(c => (
              <tr key={c.ClubID}>
                <td>{c.ClubName}</td>
                <td>{c.CategoryName}</td>
                <td>{c.members}</td>
                <td>{c.events}</td>
                <td>
                  <Link to={`/admin/${c.ClubID}`}>Manage</Link>{" · "}
                  <button className="danger" onClick={() => setConfirmId(c.ClubID)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {target && (
        <div className="modal-backdrop" onClick={() => setConfirmId(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Delete “{target.ClubName}”?</h2>
            <p>
              This will permanently remove the club, its <strong>{target.members}</strong> members,
              all events, RSVPs, attendance records, and announcements.
              <br/>
              <strong>This cannot be undone</strong> and affects every user.
            </p>
            <div className="actions">
              <button onClick={() => setConfirmId(null)}>Cancel</button>
              <button className="danger" onClick={() => onDelete(target.ClubID)}>
                Yes, delete club
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}


export default function AdminPortal() {
  const [pendingCount, setPendingCount] = useState(0);
  useEffect(() => {
    api.get("/api/admin-portal/faculty-requests")
      .then(d => setPendingCount(d.requests.length))
      .catch(() => setPendingCount(0));
  }, []);

  return (
    <main className="container">
      <header className="page-head">
        <h1>Admin Portal</h1>
        <p className="muted">Faculty controls for users, clubs, and attendance across the platform.</p>
      </header>
      <PortalNav pendingCount={pendingCount} />
      <Routes>
        <Route index               element={<Overview />} />
        <Route path="clubs"        element={<Clubs />} />
        <Route path="users"        element={<Users />} />
        <Route path="approvals"    element={<FacultyApprovals onChange={setPendingCount} />} />
        <Route path="attendance"   element={<Attendance />} />
      </Routes>
    </main>
  );
}
