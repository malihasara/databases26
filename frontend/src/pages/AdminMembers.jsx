// Club roster + dual-approval member-action queue (Pres + VP must both approve).
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import AdminNav from "./AdminNav.jsx";
import { fmtDate, fmtDateTime } from "../format.js";
import { useAuth } from "../auth.jsx";

const ROLE_LABEL = {
  President:     "President",
  VicePresident: "Vice President",
  Officer:       "Officer",
  Member:        "Member",
};

const ACTION_OPTIONS = [
  { value: "Demote",            label: "Demote to Member"        },
  { value: "Remove",            label: "Remove from club"        },
  { value: "PromoteOfficer",    label: "Promote to Officer"      },
  { value: "PromoteVP",         label: "Promote to Vice President" },
  { value: "PromotePresident",  label: "Promote to President (replaces current)" },
];

const ROLE_OPTIONS = [
  { value: "Member",        label: "Member" },
  { value: "Officer",       label: "Officer" },
  { value: "VicePresident", label: "Vice President" },
  { value: "President",     label: "President (replaces current)" },
];

export default function AdminMembers() {
  const { clubId } = useParams();
  const { user } = useAuth();
  const isAdmin = user?.AccountType === "Admin";
  const [members, setMembers] = useState(null);
  const [actions, setActions] = useState([]);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [target, setTarget] = useState(null);
  const [actionType, setActionType] = useState("Demote");

  const loadAll = () => {
    api.get(`/api/admin/${clubId}/members`).then(d => setMembers(d.members)).catch(e => setErr(e.message));
    api.get(`/api/admin/${clubId}/member-actions`).then(d => setActions(d.actions)).catch(() => {});
  };
  useEffect(() => { loadAll(); }, [clubId]);

  const submitAction = async () => {
    setErr(""); setMsg("");
    try {
      await api.post(`/api/admin/${clubId}/member-actions`, {
        target_user_id: target.UserID,
        action: actionType,
      });
      setTarget(null);
      setMsg("Action requested. Both the President and Vice President must approve.");
      loadAll();
    } catch (e) { setErr(e.message); }
  };

  const decide = async (id, verb) => {
    setErr("");
    try { await api.post(`/api/admin/${clubId}/member-actions/${id}/${verb}`); loadAll(); }
    catch (e) { setErr(e.message); }
  };

  const adminSetRole = async (m, role) => {
    setErr(""); setMsg("");
    try {
      await api.post(`/api/admin/${clubId}/members/${m.UserID}/role`, { role });
      setMsg(`${m.FirstName} ${m.LastName} is now ${ROLE_LABEL[role]}.`);
      loadAll();
    } catch (e) { setErr(e.message); }
  };
  const adminRemove = async (m) => {
    if (!confirm(`Remove ${m.FirstName} ${m.LastName} from this club?`)) return;
    setErr(""); setMsg("");
    try {
      await api.post(`/api/admin/${clubId}/members/${m.UserID}/remove`);
      setMsg(`${m.FirstName} ${m.LastName} removed.`);
      loadAll();
    } catch (e) { setErr(e.message); }
  };

  const pendingActions = actions.filter(a => a.RequestStatus === "Pending");

  return (
    <main className="container">
      <h1>Members</h1>
      <AdminNav active="members" />
      {err && <div className="error">{err}</div>}
      {msg && <div className="success">{msg}</div>}

      {pendingActions.length > 0 && (
        <section>
          <h2 className="section-h">Pending member actions
            <span className="role-pill">{pendingActions.length}</span>
          </h2>
          <ul className="list">
            {pendingActions.map(a => (
              <li key={a.RequestID} className="request-row">
                <div>
                  <strong>{a.TargetFirstName} {a.TargetLastName}</strong>
                  <span className="muted"> · current role: {ROLE_LABEL[a.TargetRoleNow] || a.TargetRoleNow || "—"}</span>
                  <div className="muted small">
                    {a.ActionType} requested by {a.RequesterFirstName} {a.RequesterLastName} on {fmtDateTime(a.RequestTime)}
                  </div>
                  <div className="muted small">
                    Pres approved: {a.PresApproved ? "✓" : "—"} · VP approved: {a.VPApproved ? "✓" : "—"}
                  </div>
                </div>
                <div className="actions">
                  <button onClick={() => decide(a.RequestID, "approve")}>Approve</button>
                  <button className="danger" onClick={() => decide(a.RequestID, "reject")}>Reject</button>
                  <button onClick={() => decide(a.RequestID, "cancel")}>Cancel</button>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      <h2 className="section-h">Roster</h2>
      <p className="muted">
        {isAdmin
          ? "As an admin you can change a member's role or remove them from the club directly."
          : "Officers can post events and announcements but cannot demote or remove members on their own. Demote / remove / promote actions go through a dual-approval queue (President + Vice President)."}
      </p>
      {!members ? <p>Loading…</p> : (
        <table className="table">
          <thead>
            <tr>
              <th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Joined</th><th></th>
            </tr>
          </thead>
          <tbody>
            {members.map(m => (
              <tr key={m.UserID}>
                <td>{m.FirstName} {m.LastName}</td>
                <td>{m.Email}</td>
                <td>
                  {isAdmin ? (
                    <select value={m.MembershipRole} onChange={e => adminSetRole(m, e.target.value)}>
                      {ROLE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                    </select>
                  ) : (
                    <span className="role-pill">{ROLE_LABEL[m.MembershipRole] || m.MembershipRole}</span>
                  )}
                </td>
                <td>{m.MembershipStatus}</td>
                <td>{fmtDate(m.MembershipJoinDate)}</td>
                <td>
                  {isAdmin ? (
                    <button className="danger" onClick={() => adminRemove(m)}>Remove</button>
                  ) : (
                    <button onClick={() => setTarget(m)}>Request action…</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {target && (
        <div className="modal-backdrop" onClick={() => setTarget(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Request action on {target.FirstName} {target.LastName}</h2>
            <p className="muted">
              Current role: {ROLE_LABEL[target.MembershipRole] || target.MembershipRole}.
              Both the President and Vice President must approve before this takes effect.
            </p>
            <label>Action
              <select value={actionType} onChange={e => setActionType(e.target.value)}>
                {ACTION_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </label>
            <div className="actions">
              <button onClick={() => setTarget(null)}>Cancel</button>
              <button className="primary" onClick={submitAction}>Submit request</button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
