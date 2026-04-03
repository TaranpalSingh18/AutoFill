import React, { createContext, useState, useEffect } from "react";
import { authService } from "../services/authService";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Initialize auth state from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem("token");
    const savedUser = localStorage.getItem("user");

    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const signup = async (name, email, password) => {
    setLoading(true);
    setError(null);
    try {
      await authService.signup(name, email, password);
      // After signup, auto-login
      const loginRes = await authService.login(email, password);
      const userData = {
        name,
        email,
        id: loginRes.user_id || email,
      };
      authService.setToken(loginRes.access_token, userData);
      setUser(userData);
      setToken(loginRes.access_token);
      return { success: true };
    } catch (err) {
      const errorMsg = err.response?.data?.detail || "Signup failed";
      setError(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    setLoading(true);
    setError(null);
    try {
      const res = await authService.login(email, password);
      const userData = {
        name: res.name || email.split("@")[0],
        email,
        id: res.user_id || email,
      };
      authService.setToken(res.access_token, userData);
      setUser(userData);
      setToken(res.access_token);
      return { success: true };
    } catch (err) {
      const errorMsg = err.response?.data?.detail || "Login failed";
      setError(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    setToken(null);
    setError(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        error,
        signup,
        login,
        logout,
        isAuthenticated: !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
