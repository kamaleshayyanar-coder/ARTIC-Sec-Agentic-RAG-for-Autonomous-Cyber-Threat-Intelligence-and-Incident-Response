"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { login, register, saveSession } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const t = mode === "login" ? await login(username, password) : await register(username, email, password);
      saveSession(t);
      router.push("/actions");
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Request failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto mt-20 max-w-md">
      <Card>
        <CardHeader>
          <CardTitle>{mode === "login" ? "Sign in" : "Create account"}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
          {mode === "register" && (
            <Input placeholder="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          )}
          <Input
            placeholder="Password (min 8 chars)"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
          />
          {error && <p className="text-sm text-red-400">{String(error)}</p>}
          <Button onClick={submit} disabled={busy} className="w-full">
            {busy ? "Please wait..." : mode === "login" ? "Sign in" : "Register"}
          </Button>
          <button
            className="w-full text-xs text-slate-400 hover:text-slate-200"
            onClick={() => setMode(mode === "login" ? "register" : "login")}
          >
            {mode === "login" ? "No account? Register (analyst role)" : "Have an account? Sign in"}
          </button>
          <p className="text-xs text-slate-500">
            Auth is only enforced when the backend has AUTH_ENABLED=true. New accounts are analysts; an admin
            promotes users to approver.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
