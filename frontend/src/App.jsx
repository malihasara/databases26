import { Link, NavLink, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "./auth.jsx";
import TorchLogo from "./components/TorchLogo.jsx";
import ThemeToggle from "./components/ThemeToggle.jsx";

import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import MyClubs from "./pages/MyClubs.jsx";
import ClubDirectory from "./pages/ClubDirectory.jsx";
import ClubDetail from "./pages/ClubDetail.jsx";
import EventList from "./pages/EventList.jsx";
import EventDetail from "./pages/EventDetail.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";
import AdminMembers from "./pages/AdminMembers.jsx";
import AdminRequests from "./pages/AdminRequests.jsx";
import AdminEvents from "./pages/AdminEvents.jsx";
import AdminEventForm from "./pages/AdminEventForm.jsx";
import AdminAttendance from "./pages/AdminAttendance.jsx";
import AdminAnnouncements from "./pages/AdminAnnouncements.jsx";
import AdminPortal from "./pages/AdminPortal.jsx";
import PublicClubs from "./pages/PublicClubs.jsx";
import PublicEvents from "./pages/PublicEvents.jsx";


function RequireAuth({ children, role }) {
  const { user, loading } = useAuth();
  const loc = useLocation();
  if (loading) return <main className="container"><p>Loading…</p></main>;
  if (!user) return <Navigate to={`/login?next=${encodeURIComponent(loc.pathname)}`} replace />;
  if (role && user.AccountType !== role) return <Navigate to="/" replace />;
  return children;
}


function Nav() {
  const { user, logout } = useAuth();
  const isFaculty = user?.AccountType === "Faculty";
  return (
    <header className="topbar">
      <Link className="brand" to="/">
        <TorchLogo size={32} />
        <span>VioletConnect</span>
      </Link>
      <nav>
        {user ? (
          <>
            {isFaculty
              ? <NavLink to="/admin-portal">Admin Portal</NavLink>
              : <NavLink to="/my-clubs">My Clubs</NavLink>}
            <NavLink to="/clubs">Clubs</NavLink>
            <NavLink to="/events">Events</NavLink>
            <span className="who">
              {user.FirstName}
              {isFaculty && <span className="faculty-pill">Faculty</span>}
            </span>
            <button className="link" onClick={logout}>Log out</button>
            <ThemeToggle />
          </>
        ) : (
          <>
            <NavLink to="/public/clubs">Browse</NavLink>
            <NavLink to="/login">Log in</NavLink>
            <NavLink to="/register">Register</NavLink>
            <ThemeToggle />
          </>
        )}
      </nav>
    </header>
  );
}


function HomeRedirect() {
  const { user, loading } = useAuth();
  if (loading) return <main className="container"><p>Loading…</p></main>;
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={user.AccountType === "Faculty" ? "/admin-portal" : "/my-clubs"} replace />;
}


export default function App() {
  return (
    <>
      <Nav />
      <Routes>
        <Route path="/"             element={<HomeRedirect />} />
        <Route path="/login"        element={<Login />} />
        <Route path="/register"     element={<Register />} />

        <Route path="/my-clubs"     element={<RequireAuth><MyClubs /></RequireAuth>} />
        <Route path="/clubs"        element={<RequireAuth><ClubDirectory /></RequireAuth>} />
        <Route path="/clubs/:id"    element={<RequireAuth><ClubDetail /></RequireAuth>} />
        <Route path="/events"       element={<RequireAuth><EventList /></RequireAuth>} />
        <Route path="/events/:id"   element={<RequireAuth><EventDetail /></RequireAuth>} />

        <Route path="/admin/:clubId"                            element={<RequireAuth><AdminDashboard /></RequireAuth>} />
        <Route path="/admin/:clubId/members"                    element={<RequireAuth><AdminMembers /></RequireAuth>} />
        <Route path="/admin/:clubId/requests"                   element={<RequireAuth><AdminRequests /></RequireAuth>} />
        <Route path="/admin/:clubId/events"                     element={<RequireAuth><AdminEvents /></RequireAuth>} />
        <Route path="/admin/:clubId/events/new"                 element={<RequireAuth><AdminEventForm mode="create" /></RequireAuth>} />
        <Route path="/admin/:clubId/events/:eventId/edit"       element={<RequireAuth><AdminEventForm mode="edit" /></RequireAuth>} />
        <Route path="/admin/:clubId/events/:eventId/attendance" element={<RequireAuth><AdminAttendance /></RequireAuth>} />
        <Route path="/admin/:clubId/announcements"              element={<RequireAuth><AdminAnnouncements /></RequireAuth>} />

        <Route path="/admin-portal/*" element={<RequireAuth role="Faculty"><AdminPortal /></RequireAuth>} />

        <Route path="/public/clubs"  element={<PublicClubs />} />
        <Route path="/public/events" element={<PublicEvents />} />

        <Route path="*" element={<main className="container"><p>Not found.</p></main>} />
      </Routes>
    </>
  );
}
