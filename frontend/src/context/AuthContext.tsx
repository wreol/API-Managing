import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import apiClient from '../api/client';
import type { User, TokenResponse } from '../types';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, display_name: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function storeTokens(access: string, refresh: string) {
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
}

function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

function getStoredTokens() {
  return {
    accessToken: localStorage.getItem('access_token'),
    refreshToken: localStorage.getItem('refresh_token'),
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    accessToken: null,
    refreshToken: null,
    isLoading: true,
    isAuthenticated: false,
  });

  const refreshUser = useCallback(async () => {
    try {
      const { data } = await apiClient.get<User>('/auth/me');
      setState((prev) => ({
        ...prev,
        user: data as User,
        isLoading: false,
        isAuthenticated: true,
      }));
    } catch {
      setState((prev) => ({
        ...prev,
        user: null,
        isLoading: false,
        isAuthenticated: false,
      }));
    }
  }, []);

  useEffect(() => {
    const { accessToken, refreshToken } = getStoredTokens();
    if (accessToken) {
      setState((prev) => ({
        ...prev,
        accessToken,
        refreshToken,
      }));
      refreshUser();
    } else {
      setState((prev) => ({ ...prev, isLoading: false }));
    }
  }, [refreshUser]);

  const login = useCallback(async (email: string, password: string) => {
    const { data } = await apiClient.post<TokenResponse>('/auth/login', { email, password });
    storeTokens(data.access_token, data.refresh_token);
    setState({
      user: data.user,
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      isLoading: false,
      isAuthenticated: true,
    });
  }, []);

  const register = useCallback(async (email: string, password: string, display_name: string) => {
    const { data } = await apiClient.post<TokenResponse>('/auth/register', { email, password, display_name });
    storeTokens(data.access_token, data.refresh_token);
    setState({
      user: data.user,
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      isLoading: false,
      isAuthenticated: true,
    });
  }, []);

  const logout = useCallback(() => {
    clearTokens();
    setState({
      user: null,
      accessToken: null,
      refreshToken: null,
      isLoading: false,
      isAuthenticated: false,
    });
  }, []);

  return (
    <AuthContext.Provider
      value={{ ...state, login, register, logout, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}
