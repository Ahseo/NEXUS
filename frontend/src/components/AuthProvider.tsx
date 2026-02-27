"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { usePathname, useRouter } from "next/navigation";
import { auth } from "@/lib/api";

interface AuthUser {
  user_id: string;
  email: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  loading: true,
  logout: async () => {},
});

const PUBLIC_ROUTES = ["/login", "/onboarding"];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    let cancelled = false;

    async function checkAuth() {
      try {
        const data = await auth.me();
        if (!cancelled) {
          setUser(data);
        }
      } catch {
        if (!cancelled) {
          setUser(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    checkAuth();
    return () => {
      cancelled = true;
    };
  }, []);

  // Route guard
  useEffect(() => {
    if (loading) return;

    const isPublic = PUBLIC_ROUTES.some((r) => pathname.startsWith(r));

    if (!user && !isPublic) {
      router.replace("/login");
    }
  }, [user, loading, pathname, router]);

  const logout = useCallback(async () => {
    try {
      await auth.logout();
    } catch {
      // ignore
    }
    setUser(null);
    router.replace("/login");
  }, [router]);

  const isPublic = PUBLIC_ROUTES.some((r) => pathname.startsWith(r));

  // Show nothing while checking auth on protected routes
  if (loading && !isPublic) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-950">
        <div className="text-sm text-gray-500">Loading...</div>
      </div>
    );
  }

  // Don't render protected content if not authenticated
  if (!loading && !user && !isPublic) {
    return null;
  }

  return (
    <AuthContext.Provider value={{ user, loading, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
