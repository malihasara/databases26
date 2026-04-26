import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import AdminNav from "./AdminNav.jsx";
import { fmtDateTime } from "../format.js";

export default function AdminRequests() {
  const { clubId } = useParams();
  const [rows, setRows] = useState(null);
  const [err, setErr] = useState("");

  const load = () => api.get(`/api/admin/${clubId}/requests`).then(d => setRows(d.requests)).catch(e => setErr(e.message));
  useEffect(() => { load(); }, [clubId]);

  const decide = async (rid, action) => {
    setErr("");
    try { await api.post(`/api/admin/${clubId}/requests/${rid}/${action}`); load(); }
    catch (e) { setErr(e.message); }
  };

  return (
    <main className="container">
      <h1>Join Requests</h1>
      <AdminNav active="requests" />
      {err && <div className="error">{err}</div>}
      {!rows ? <p>Loading…</p> : rows.length === 0 ? <p className="muted">No requests yet.</p> : (
        <table className="table">
          <thead><tr><th>Requester</th><th>Email</th><th>Status</th><th>When</th><th></th></tr></thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.RequestID}>
                <td>{r.FirstName} {r.LastName}</td>
                <td>{r.Email}</td>
                <td>{r.RequestStatus}</td>
                <td>{fmtDateTime(r.RequestTime)}</td>
                <td>
                  {r.RequestStatus === "Pending" && (
                    <>
                      <button onClick={() => decide(r.RequestID, "approve")}>Approve</button>{" "}
                      <button className="danger" onClick={() => decide(r.RequestID, "reject")}>Reject</button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
