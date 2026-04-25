import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import TorchLogo from "../components/TorchLogo.jsx";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [role, setRole] = useState("Student");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");

  const onSubmit = async (e) => {
    e.preventDefault();
    setErr("");
    try {
      const user = await login(email, password, role);
      const next = params.get("next") || (user.AccountType === "Faculty" ? "/admin-portal" : "/my-clubs");
      navigate(next, { replace: true });
    } catch (e) {
      setErr(e.message);
    }
  };

  return (
    <main className="container narrow">
      <div className="auth-card">
        <div className="auth-brand">
          <TorchLogo size={40} />
          <h1>VioletConnect</h1>
        </div>

        <div className="role-tabs">
          <button type="button"
                  className={role === "Student" ? "active" : ""}
                  onClick={() => setRole("Student")}>Student</button>
          <button type="button"
                  className={role === "Faculty" ? "active" : ""}
                  onClick={() => setRole("Faculty")}>Faculty / Admin</button>
        </div>

        {err && <div className="error">{err}</div>}

        <form onSubmit={onSubmit}>
          <label>Email
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required />
          </label>
          <label>Password
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required />
          </label>
          <button type="submit" className="primary block">
            Log in as {role}
          </button>
        </form>

        <p className="muted center">
          New student? <Link to="/register">Create an account</Link>
        </p>
      </div>
    </main>
  );
}
