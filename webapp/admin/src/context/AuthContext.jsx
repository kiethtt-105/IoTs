import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { authApi, setToken, setUser, getStoredUser } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUserState] = useState(getStoredUser());
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    setUserState(null);
  }, []);

  const login = useCallback(async (email, password) => {
    const data = await authApi.login(email, password);
    setToken(data.access_token);
    setUser(data.user);
    setUserState(data.user);
    return data.user;
  }, []);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    authApi
      .me()
      .then((u) => {
        setUser(u);
        setUserState(u);
      })
      .catch(() => {
        logout();
      })
      .finally(() => setLoading(false));
  }, [logout]);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
