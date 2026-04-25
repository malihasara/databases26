import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import AdminNav from "./AdminNav.jsx";

export default function AdminMembers() {
  const { clubId } = useParams();
  const [members, setMembers] = useState(null);
  const [err, setErr] = useState("");

  const load = () => api.get(`/api/admin/${clubId}/members`).then(d => setMembers(d.members)).catch(e => setErr(e.message));
  useEffect(() => { load(); }, [clubId]);

  const setRole = async (userId, role) => {
    setErr("");
    try { await api.post(`/api/admin/${clubId}/members/${userId}/role`, { role }); load(); }
    catch (e) { setErr(e.message); }
  };
  const remove = async (userId) => {
    setErr("");
    if (!confirm("Remove this member?")) return;
    try { await api.post(`/api/admin/${clubId}/members/${userId}/remove`); load(); }
    catch (e) { setErr(e.message); }
  };

  return (
    <main className="container">
      <h1>Members</h1>
      <AdminNav active="members" />
      {err && <div className="error">{err}</div>}
      {!members ? <p>Loading…</p> : (
        <table className="table">
          <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Joined</th><th></th></tr></thead>
          <tbody>
            {members.map(m => (
              <tr key={m.UserID}>
                <td>{m.FirstName} {m.LastName}</td>
                <td>{m.Email}</td>
                <td>
                  <select value={m.MembershipRole} onChange={e => setRole(m.UserID, e.target.value)}>
                    <option value="Owner">Owner</option>
                    <option value="Officer">Officer</option>
                    <option value="Member">Member</option>
                  </select>
                </td>
                <td>{m.MembershipStatus}</td>
                <td>{m.MembershipJoinDate?.slice(0, 10)}</td>
                <td><button className="danger" onClick={() => remove(m.UserID)}>Remove</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
