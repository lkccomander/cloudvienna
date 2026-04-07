import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from "react";
import { api, ApiError } from "../../lib/api/client";
import type { AuthUser } from "../../lib/api/types";
import { clearStoredToken, getStoredToken, setStoredToken } from "../../lib/auth-storage";

interface AuthContextValue {
  token: string | null;
  user: AuthUser | null;
  booting: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const [user, setUser] = useState<AuthUser | null>(null);
  const [booting, setBooting] = useState(true);

  async function login(username: string, password: string) {
    const response = await api.login(username, password);
    setStoredToken(response.access_token);
    setToken(response.access_token);
    const me = await api.me(response.access_token);
    setUser(me);
  }

  function logout() {
    clearStoredToken();
    setToken(null);
    setUser(null);
  }

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      if (!token) {
        if (!cancelled) setBooting(false);
        return;
      }
      try {
        const me = await api.me(token);
        if (!cancelled) setUser(me);
      } catch (error) {
        if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
          clearStoredToken();
          if (!cancelled) {
            setToken(null);
            setUser(null);
          }
        }
      } finally {
        if (!cancelled) setBooting(false);
      }
    };
    void run();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const value = useMemo<AuthContextValue>(
    () => ({ token, user, booting, login, logout }),
    [token, user, booting],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
