import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api";

export default function EventList() {
  const [params, setParams] = useSearchParams();
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");

  const filters = {
    q: params.get("q") || "",
    club: params.get("club") || "",
    type: params.get("type") || "",
    visibility: params.get("visibility") || "",
    sort: params.get("sort") || "soonest",
  };

  useEffect(() => {
    const qs = new URLSearchParams(filters).toString();
    api.get(`/api/events/?${qs}`).then(setData).catch(e => setErr(e.message));
  }, [params]);

  const onSubmit = (e) => {
    e.preventDefault();
    setParams(Object.fromEntries(new FormData(e.currentTarget)));
  };

  return (
    <main className="container">
      <h1>Events</h1>
      <form className="filters" onSubmit={onSubmit}>
        <input name="q" placeholder="Title…" defaultValue={filters.q} />
        <select name="club" defaultValue={filters.club}>
          <option value="">All clubs</option>
          {data?.clubs?.map(c => <option key={c.ClubID} value={c.ClubID}>{c.ClubName}</option>)}
        </select>
        <select name="type" defaultValue={filters.type}>
          <option value="">All types</option>
          {data?.types?.map(t => <option key={t.EventTypeID} value={t.EventTypeID}>{t.EventTypeName}</option>)}
        </select>
        <select name="visibility" defaultValue={filters.visibility}>
          <option value="">Any visibility</option>
          <option value="Public">Public</option>
          <option value="MembersOnly">Members Only</option>
        </select>
        <select name="sort" defaultValue={filters.sort}>
          <option value="soonest">Soonest</option>
          <option value="latest">Latest</option>
        </select>
        <button type="submit">Apply</button>
      </form>

      {err && <div className="error">{err}</div>}
      {!data ? <p>Loading…</p> :
        data.events.length === 0 ? <p className="muted">No events match.</p> : (
          <ul className="list">
            {data.events.map(e => (
              <li key={e.EventID}>
                <Link to={`/events/${e.EventID}`}><strong>{e.EventTitle}</strong></Link>
                <span className="muted"> — {e.ClubName} · {new Date(e.EventStartTime).toLocaleString()} · {e.BuildingName} {e.RoomNumber} · {e.EventVisibility}</span>
                <p>{e.EventDescription}</p>
              </li>
            ))}
          </ul>
        )}
    </main>
  );
}
