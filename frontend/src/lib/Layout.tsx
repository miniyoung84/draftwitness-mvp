import Link from "next/link";
import { useRouter } from "next/router";
import { ReactNode, useEffect, useState } from "react";
import { clearAuth, getUser, DwUser } from "./api";

// Shared nav + page shell. Kept intentionally simple.
export default function Layout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<DwUser | null>(null);

  useEffect(() => {
    setUser(getUser());
  }, [router.pathname]);

  function logout() {
    clearAuth();
    router.push("/login");
  }

  return (
    <>
      <nav className="nav">
        <Link href="/" className="brand">
          DraftWitness
        </Link>
        {user && <Link href="/dashboard">Dashboard</Link>}
        {user?.is_reviewer && <Link href="/review">Review</Link>}
        <span className="spacer" />
        {user ? (
          <>
            <span className="muted">{user.username}</span>
            <button className="secondary" onClick={logout}>
              Log out
            </button>
          </>
        ) : (
          <>
            <Link href="/login">Log in</Link>
            <Link href="/register">Register</Link>
          </>
        )}
      </nav>
      <main className="container">{children}</main>
    </>
  );
}

// Small helper to redirect to /login when there is no token.
export function useRequireAuth() {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (!getUser()) {
      router.replace("/login");
    } else {
      setReady(true);
    }
  }, [router]);
  return ready;
}
