// Registration page with Student / Admin tabs; Admin requests are queued for an existing admin to approve.
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import TorchLogo from "../components/TorchLogo.jsx";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [requestedRole, setRequestedRole] = useState("Student");
  const [form, setForm] = useState({ first_name: "", last_name: "", email: "", password: "" });
  const [err, setErr] = useState("");

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const onSubmit = async (e) => {
    e.preventDefault();
    setErr("");
    try {
      const d = await register({ ...form, requested_account_type: requestedRole });
      navigate(d.admin_request_pending ? "/my-clubs?adminPending=1" : "/my-clubs", { replace: true });
    } catch (e) {
      setErr(e.message);
    }
  };

  return (
    <main className="container narrow">
      <div className="auth-card">
        <div className="auth-brand">
          <TorchLogo size={40} />
          <h1>Create your account</h1>
        </div>

        <div className="role-tabs">
          <button type="button"
                  className={requestedRole === "Student" ? "active" : ""}
                  onClick={() => setRequestedRole("Student")}>Student</button>
          <button type="button"
                  className={requestedRole === "Admin" ? "active" : ""}
                  onClick={() => setRequestedRole("Admin")}>Admin</button>
        </div>

        {requestedRole === "Admin" && (
          <div className="info-banner">
            Admin access requires approval. Your account will be created as a student
            and a request will be sent to existing admins for review.
          </div>
        )}

        {err && <div className="error">{err}</div>}

        <form onSubmit={onSubmit}>
          <div className="form-row">
            <label>First name<input value={form.first_name} onChange={set("first_name")} required /></label>
            <label>Last name<input value={form.last_name} onChange={set("last_name")} required /></label>
          </div>
          <label>Email<input type="email" value={form.email} onChange={set("email")} required /></label>
          <label>Password<input type="password" minLength={8} value={form.password} onChange={set("password")} required /></label>
          <button type="submit" className="primary block">
            {requestedRole === "Admin" ? "Sign up & request admin access" : "Create student account"}
          </button>
        </form>

        <p className="muted center">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </div>
    </main>
  );
}
