"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import { api, setAuthToken, clearAuthToken, getAuthToken } from "./api";

export interface UserPreferences {
  confidence_threshold: number;
  anomaly_sensitivity: number;
  budget_alert_threshold: number;
  enable_proactive_alerts: boolean;
  dark_mode?: boolean;
}

export interface User {
  id: number | string;
  email: string;
  full_name?: string;
  name?: string;
  currency?: string;
  monthly_income?: number;
  preferences?: UserPreferences;
}

export interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (token: string, user?: User) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
  isAuthenticated: boolean;
}

const DEFAULT_PREFERENCES: UserPreferences = {
  confidence_threshold: 0.75,
  anomaly_sensitivity: 0.7,
  budget_alert_threshold: 0.8,
  enable_proactive_alerts: true,
  dark_mode: true,
};

const DEFAULT_USER: User = {
  id: "demo-user-1",
  email: "demo@finagent.ai",
  full_name: "Akash U",
  currency: "₹",
  monthly_income: 125000,
  preferences: DEFAULT_PREFERENCES,
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    if (typeof window === "undefined") return DEFAULT_USER;
    try {
      const stored =
        localStorage.getItem("finagent_user") || localStorage.getItem("user");
      if (stored) {
        const parsed = JSON.parse(stored);
        return {
          ...DEFAULT_USER,
          ...parsed,
          preferences: {
            ...DEFAULT_PREFERENCES,
            ...(parsed.preferences || {}),
          },
        };
      }
    } catch (e) {
      console.error("Failed parsing stored user:", e);
    }
    return DEFAULT_USER;
  });

  const [token, setToken] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    return getAuthToken() || localStorage.getItem("token");
  });

  const [loading, setLoading] = useState(false);

  const refreshUser = useCallback(async () => {
    try {
      const userData = await api.getMe();
      if (userData && userData.email) {
        const mergedPreferences: UserPreferences = {
          ...DEFAULT_PREFERENCES,
          ...(userData.preferences || {}),
        };
        const updatedUser: User = {
          ...DEFAULT_USER,
          ...userData,
          preferences: mergedPreferences,
        };
        setUser(updatedUser);
        if (typeof window !== "undefined") {
          localStorage.setItem("finagent_user", JSON.stringify(updatedUser));
          localStorage.setItem("user", JSON.stringify(updatedUser));
        }
      }
    } catch (error) {
      console.warn("Could not sync user profile with backend:", error);
    }
  }, []);

  useEffect(() => {
    if (token) {
      setAuthToken(token);
      refreshUser();
    }
  }, [token, refreshUser]);

  const login = (newToken: string, newUser?: User) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("token", newToken);
      localStorage.setItem("finagent_token", newToken);
    }
    setAuthToken(newToken);
    setToken(newToken);

    if (newUser) {
      const mergedPreferences: UserPreferences = {
        ...DEFAULT_PREFERENCES,
        ...(newUser.preferences || {}),
      };
      const mergedUser: User = {
        ...DEFAULT_USER,
        ...newUser,
        preferences: mergedPreferences,
      };
      if (typeof window !== "undefined") {
        localStorage.setItem("user", JSON.stringify(mergedUser));
        localStorage.setItem("finagent_user", JSON.stringify(mergedUser));
      }
      setUser(mergedUser);
    }

    refreshUser();
  };

  const logout = () => {
    clearAuthToken();
    if (typeof window !== "undefined") {
      localStorage.removeItem("token");
      localStorage.removeItem("finagent_token");
      localStorage.removeItem("user");
      localStorage.removeItem("finagent_user");
    }
    setToken(null);
    setUser(DEFAULT_USER);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        logout,
        refreshUser,
        isAuthenticated: !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}