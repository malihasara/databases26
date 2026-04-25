import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api";

export default function ClubDirectory() {
  const [params, setParams] = useSearchParams();
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");

  const q = params.get("q") || "";
  const category = params.get("category") || "";
  const sort = params.get("sort") || "name";

  useEffect(() => {
    const qs = new URLSearchParams({ q, category, sort }).toString();
    api.get(`/api/clubs/?${qs}`).then(setData).catch(e => setErr(e.message));
  }, [q, category, sort]);

  const onSubmit = (e) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    setParams(Object.fromEntries(fd));
  };

  return (
    <main className="container">
      <h1>Club Directory</h1>
      <form className="filters" onSubmit={onSubmit}>
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

      {err && <div className="error">{err}</div>}
      {!data ? <p>Loading…</p> :
        data.clubs.length === 0 ? <p className="muted">No clubs match.</p> : (
          <div className="grid">
            {data.clubs.map(c => (
              <Link key={c.ClubID} className="card tile" to={`/clubs/${c.ClubID}`}>
                <h3>{c.ClubName}</h3>
                <p className="muted">{c.CategoryName}</p>
                <p>{c.ClubDescription}</p>
              </Link>
            ))}
          </div>
        )}
    </main>
  );
}
