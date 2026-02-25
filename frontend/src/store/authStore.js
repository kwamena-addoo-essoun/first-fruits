import { create } from 'zustand';

const decodePayload = (token) => {
  try {
    const b64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(atob(b64));
  } catch {
    return {};
  }
};

const isTokenExpired = (token) => {
  try {
    const payload = decodePayload(token);
    if (!payload?.exp) return false;
    return payload.exp * 1000 <= Date.now();
  } catch {
    return true;
  }
};

export const useAuthStore = create((set) => ({
  isAuthenticated: false,
  token: null,
  isAdmin: false,
  setAuth: (isAuthenticated, token) => {
    if (isAuthenticated && token && isTokenExpired(token)) {
      localStorage.removeItem('token');
      set({ isAuthenticated: false, token: null, isAdmin: false });
      return;
    }
    const isAdmin = token ? (decodePayload(token).is_admin ?? false) : false;
    set({ isAuthenticated, token, isAdmin });
  },
  validateStoredToken: () => {
    const token = localStorage.getItem('token');
    if (!token || isTokenExpired(token)) {
      localStorage.removeItem('token');
      set({ isAuthenticated: false, token: null, isAdmin: false });
      return null;
    }
    const isAdmin = decodePayload(token).is_admin ?? false;
    set({ isAuthenticated: true, token, isAdmin });
    return token;
  },
  logout: () => {
    localStorage.removeItem('token');
    set({ isAuthenticated: false, token: null, isAdmin: false });
  },
}));
