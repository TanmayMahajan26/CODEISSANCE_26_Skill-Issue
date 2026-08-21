import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../api/client';
import { loginUser, getCurrentUser, checkBackendHealth } from '../api';
import { MOCK_DEMO_USERS } from '../utils/mockData';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [backendStatus, setBackendStatus] = useState({ online: false, app: 'Nexus360' });

  // Initial session restore & backend health check
  useEffect(() => {
    async function initAuth() {
      // 1. Check backend health
      const health = await checkBackendHealth();
      setBackendStatus({
        online: health.status === 'ok' || health.status === 'healthy',
        app: health.app || 'Nexus360',
        environment: health.environment,
      });

      // 2. Restore token
      const token = api.getToken();
      if (token) {
        try {
          const profile = await getCurrentUser();
          if (profile) {
            setUser(profile);
          } else {
            // Restore from saved mock session if offline
            const savedUser = localStorage.getItem('nexus360_user');
            if (savedUser) {
              setUser(JSON.parse(savedUser));
            }
          }
        } catch {
          const savedUser = localStorage.getItem('nexus360_user');
          if (savedUser) {
            setUser(JSON.parse(savedUser));
          }
        }
      }
      setLoading(false);
    }

    initAuth();

    // Listen for 401 unauthorized
    const handleUnauthorized = () => {
      setUser(null);
      localStorage.removeItem('nexus360_user');
    };
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, []);

  const login = async (usernameOrEmail, password) => {
    setLoading(true);
    try {
      const resp = await loginUser(usernameOrEmail, password);
      api.setToken(resp.access_token);
      const userData = {
        username: resp.username,
        email: resp.email,
        role: resp.role,
        full_name: resp.full_name,
      };
      setUser(userData);
      localStorage.setItem('nexus360_user', JSON.stringify(userData));
      return { success: true, user: userData };
    } catch (err) {
      return { success: false, error: err.message || 'Login failed' };
    } finally {
      setLoading(false);
    }
  };

  const switchDemoRole = async (targetRole) => {
    const demo = MOCK_DEMO_USERS.find((u) => u.role === targetRole) || MOCK_DEMO_USERS[0];
    return await login(demo.username, demo.password);
  };

  const logout = () => {
    api.setToken(null);
    setUser(null);
    localStorage.removeItem('nexus360_user');
  };

  const hasRole = (...roles) => {
    if (!user) return false;
    return roles.includes(user.role);
  };

  const isRole = (role) => user?.role === role;

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        backendStatus,
        login,
        logout,
        switchDemoRole,
        hasRole,
        isRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
