// Auth context: hydrates the current user via /api/auth/me and exposes login / register / logout.
import { createContext, useContext, useEffect, useState } from "react";
import { api } from "./api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/auth/me")
      .then(d => setUser(d.user))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const login = async (email, password, role) => {
    const d = await api.post("/api/auth/login", { email, password, role });
    setUser(d.user);
    return d.user;
  };

  const register = async (form) => {
    const d = await api.post("/api/auth/register", form);
    setUser(d.user);
    return d;
  };

  const logout = async () => {
    await api.post("/api/auth/logout");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
