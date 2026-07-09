import { useRouter } from "next/router";
import { useState } from "react";
import Link from "next/link";
import { api, setAuth } from "@/lib/api";

export default function Register() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const data = await api<{ token: string; user: any }>(
        "/auth/register/",
        { method: "POST", auth: false, body: { username, email, password } }
      );
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
      <h1>Create an account</h1>
      <form onSubmit={submit}>
        <label>Username</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} required />
        <label>Email (optional)</label>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <label>Password (min 8 characters)</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {error && <p className="error">{error}</p>}
        <p>
          <button disabled={busy} type="submit">
            {busy ? "Creating…" : "Create account"}
          </button>
        </p>
      </form>
      <p className="muted">
        Already have an account? <Link href="/login">Log in</Link>
      </p>
    </div>
  );
}
