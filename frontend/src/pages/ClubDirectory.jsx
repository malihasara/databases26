// Browseable club grid with name/category filters and a student "Request a club" form.
import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth.jsx";

export default function ClubDirectory() {
  const { user } = useAuth();
  const isAdmin = user?.AccountType === "Admin";
  const [params, setParams] = useSearchParams();
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [showRequest, setShowRequest] = useState(false);
  const [reqForm, setReqForm] = useState({
    name: "", description: "", category_ids: [], officer_user_id: user?.UserID || "",
  });
  const [reqMsg, setReqMsg] = useState("");

  const q = params.get("q") || "";
  const category = params.get("category") || "";
  const sort = params.get("sort") || "name";

  const reload = useMemo(() => () => {
    const qs = new URLSearchParams({ q, category, sort }).toString();
    api.get(`/api/clubs/?${qs}`).then(setData).catch(e => setErr(e.message));
  }, [q, category, sort]);

  useEffect(() => { reload(); }, [reload]);
  useEffect(() => {
    if (user) setReqForm(f => ({ ...f, officer_user_id: user.UserID }));
  }, [user]);

  const onSubmit = (e) => {
    e.preventDefault();
    setParams(Object.fromEntries(new FormData(e.currentTarget)));
  };

  const toggleCategory = (cid) =>
    setReqForm(f => ({
      ...f,
      category_ids: f.category_ids.includes(cid)
        ? f.category_ids.filter(x => x !== cid)
        : [...f.category_ids, cid],
    }));

  const submitRequest = async (e) => {
    e.preventDefault();
    setErr(""); setReqMsg("");
    try {
      await api.post("/api/clubs/request", reqForm);
      setShowRequest(false);
      setReqMsg("Request submitted. An admin will review it.");
      setReqForm({ name: "", description: "", category_ids: [], officer_user_id: user.UserID });
    } catch (e) { setErr(e.message); }
  };

  return (
    <main className="container">
      <header className="page-head">
        <h1>Club Directory</h1>
        <p className="muted">Browse all clubs, filter by category, or propose a new one.</p>
      </header>

      <div className="page-actions">
        <form className="filters" onSubmit={onSubmit} style={{ flex: 1 }}>
          <input name="q" placeholder="Search by name…" defaultValue={q} />
          <select name="category" defaultValue={category}>
            <option value="">All categories</option>
            {data?.categories?.map(c => <option key={c.CategoryID} value={c.CategoryID}>{c.CategoryName}</option>)}
          </select>
          <select name="sort" defaultValue={sort}>
            <option value="name">Name</option>
            <option value="newest">Newest</option>
          </select>
          <button type="submit">Apply</button>
        </form>
        {!isAdmin && user && (
          <button className="primary" onClick={() => setShowRequest(s => !s)}>
            {showRequest ? "Cancel" : "+ Request a club"}
          </button>
        )}
      </div>

      {reqMsg && <div className="success">{reqMsg}</div>}

      {showRequest && (
        <form className="card" onSubmit={submitRequest}>
          <h2 style={{ marginTop: 0 }}>Propose a new club</h2>
          <p className="muted">Admins will review and approve. You'll be the initial President once approved.</p>
          <label>Club name<input value={reqForm.name} onChange={e => setReqForm({...reqForm, name: e.target.value})} required /></label>
          <label>Description<textarea rows={3} value={reqForm.description} onChange={e => setReqForm({...reqForm, description: e.target.value})} required /></label>
          <label>Categories (pick one or more)
            <div className="checkbox-grid">
              {data?.categories?.map(c => (
                <label key={c.CategoryID} className="check">
                  <input type="checkbox"
                         checked={reqForm.category_ids.includes(c.CategoryID)}
                         onChange={() => toggleCategory(c.CategoryID)} />
                  <span>{c.CategoryName}</span>
                </label>
              ))}
            </div>
          </label>
          <button type="submit" className="primary">Submit request</button>
        </form>
      )}

      {err && <div className="error">{err}</div>}
      {!data ? <p>Loading…</p> :
        data.clubs.length === 0 ? <p className="muted">No clubs match.</p> : (
          <div className="grid">
            {data.clubs.map(c => (
              <Link key={c.ClubID} className="card tile" to={`/clubs/${c.ClubID}`}>
                <h3>{c.ClubName}</h3>
                <p className="muted">{(c.Categories || []).map(x => x.CategoryName).join(" · ") || "—"}</p>
                <p>{c.ClubDescription}</p>
              </Link>
            ))}
          </div>
        )}
    </main>
  );
}
