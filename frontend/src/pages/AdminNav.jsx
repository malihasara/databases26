// Subnav for the per-club officer admin pages (dashboard, members, requests, events, announcements).
import { NavLink, useParams } from "react-router-dom";

export default function AdminNav({ active }) {
  const { clubId } = useParams();
  const tabs = [
    ["dashboard",     `/admin/${clubId}`,                "Dashboard"],
    ["members",       `/admin/${clubId}/members`,        "Members"],
    ["requests",      `/admin/${clubId}/requests`,       "Requests"],
    ["events",        `/admin/${clubId}/events`,         "Events"],
    ["announcements", `/admin/${clubId}/announcements`,  "Announcements"],
  ];
  return (
    <nav className="subnav">
      {tabs.map(([key, to, label]) => (
        <NavLink key={key} to={to} className={active === key ? "active" : ""} end>{label}</NavLink>
      ))}
      <NavLink to={`/clubs/${clubId}`}>Back to club</NavLink>
    </nav>
  );
}
