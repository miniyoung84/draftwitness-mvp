import { useRouter } from "next/router";
import { useState } from "react";
import Link from "next/link";
import { api, setAuth } from "@/lib/api";

export default function Login() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const data = await api<{ token: string; user: any }>("/auth/login/", {
        method: "POST",
        auth: false,
        body: { username, password },
      });
      setAuth(data.token, data.user);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ maxWidth: 420 }}>
      <h1>Log in</h1>
      <form onSubmit={submit}>
        <label>Username</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} required />
        <label>Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {error && <p className="error">{error}</p>}
        <p>
          <button disabled={busy} type="submit">
            {busy ? "Logging in…" : "Log in"}
          </button>
        </p>
      </form>
      <p className="muted">
        No account? <Link href="/register">Register</Link>
      </p>
    </div>
  );
}
