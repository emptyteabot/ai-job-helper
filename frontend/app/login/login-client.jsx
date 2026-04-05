"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import styles from "./login-client.module.css";

const SOCIAL_PROVIDERS = Object.freeze([
  { id: "google", label: "Google" },
  { id: "github", label: "GitHub" },
  { id: "linkedin", label: "LinkedIn" },
  { id: "wechat", label: "微信" },
]);

function pickMessage(payload, fallback) {
  return payload?.message || payload?.error || payload?.detail || fallback;
}

function normalizeSocialStatus(payload) {
  const providers = Array.isArray(payload?.providers) ? payload.providers : [];
  const byId = new Map(
    providers
      .filter((item) => item && typeof item === "object")
      .map((item) => [String(item.id || "").trim().toLowerCase(), item]),
  );

  return SOCIAL_PROVIDERS.map((item) => {
    const raw = byId.get(item.id);
    const configured = Boolean(raw?.configured);
    const available = Boolean(raw?.available);
    return {
      ...item,
      configured,
      available,
      message: String(raw?.message || (configured ? "可用" : "未配置")).trim(),
    };
  });
}

export default function LoginClient({ initialMode = "login" }) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const redirectTo = useMemo(() => {
    const from = String(searchParams?.get("from") || "").trim();
    if (from && from.startsWith("/")) {
      return from;
    }
    return "/app";
  }, [searchParams]);

  const [mode, setMode] = useState(initialMode === "register" ? "register" : "login");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState({ type: "idle", text: "" });
  const [socialStatus, setSocialStatus] = useState(
    SOCIAL_PROVIDERS.map((item) => ({ ...item, configured: false, available: false, message: "未配置" })),
  );
  const [form, setForm] = useState({
    email: "",
    password: "",
    name: "",
    access_code: "",
  });

  useEffect(() => {
    setMode(initialMode === "register" ? "register" : "login");
  }, [initialMode]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const response = await fetch("/api/auth/social-status", { cache: "no-store" });
        const payload = await response.json().catch(() => ({}));
        if (!cancelled) {
          setSocialStatus(normalizeSocialStatus(payload));
        }
      } catch {
        if (!cancelled) {
          setSocialStatus(normalizeSocialStatus({}));
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleAuthSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setStatus({ type: "info", text: "" });
    try {
      const endpoint = mode === "register" ? "/api/auth/register" : "/api/auth/login";
      const payload = {
        email: form.email.trim(),
        password: form.password,
        name: form.name.trim(),
        access_code: form.access_code.trim().toUpperCase(),
      };
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || !data?.success) {
        throw new Error(
          pickMessage(data, mode === "register" ? "注册失败，请再试一次" : "登录失败，请检查邮箱和密码"),
        );
      }
      setStatus({
        type: "ok",
        text: mode === "register" ? "注册成功，正在进入工作台..." : "登录成功，正在进入工作台...",
      });
      router.replace(redirectTo);
      router.refresh();
    } catch (error) {
      setStatus({ type: "error", text: error.message || "操作失败，请稍后重试" });
    } finally {
      setBusy(false);
    }
  }

  async function handleSocialLogin(provider) {
    setBusy(true);
    setStatus({ type: "info", text: "" });
    try {
      const response = await fetch("/api/auth/social-login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider,
          name: form.name.trim() || form.email.trim().split("@")[0] || `${provider}_user`,
          provider_user_id: form.email.trim() || `${provider}_${Date.now()}`,
          access_code: form.access_code.trim().toUpperCase(),
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || !data?.success) {
        throw new Error(pickMessage(data, `${provider} 登录暂时不可用`));
      }
      setStatus({ type: "ok", text: `${provider} 登录成功，正在进入工作台...` });
      router.replace(redirectTo);
      router.refresh();
    } catch (error) {
      setStatus({ type: "error", text: error.message || "第三方登录失败，请稍后再试" });
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className={styles.page}>
      <section className={styles.card}>
        <p className={styles.eyebrow}>agenthelpjob account</p>
        <h1>登录 / 注册</h1>
        <p className={styles.desc}>用邮箱登录；如果你买了访问码，也可以在这里一起填，权限会自动绑定到当前账号。</p>

        <div className={styles.modeRow}>
          <button
            type="button"
            className={mode === "login" ? styles.modeActive : styles.modeButton}
            onClick={() => setMode("login")}
            disabled={busy}
          >
            登录
          </button>
          <button
            type="button"
            className={mode === "register" ? styles.modeActive : styles.modeButton}
            onClick={() => setMode("register")}
            disabled={busy}
          >
            注册
          </button>
        </div>

        <form className={styles.form} onSubmit={handleAuthSubmit}>
          <label>
            邮箱
            <input
              type="email"
              required
              value={form.email}
              onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
              placeholder="you@example.com"
            />
          </label>
          <label>
            密码
            <input
              type="password"
              required
              value={form.password}
              onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
              placeholder="至少 6 位"
            />
          </label>
          <label>
            昵称（可选）
            <input
              value={form.name}
              onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
              placeholder="你希望展示的名字"
            />
          </label>
          <label>
            访问码（可选）
            <input
              value={form.access_code}
              onChange={(event) => setForm((current) => ({ ...current, access_code: event.target.value }))}
              placeholder="买了访问码就填，登录后会自动关联权限"
            />
          </label>
          <button type="submit" className={styles.primary} disabled={busy}>
            {busy ? "处理中..." : mode === "register" ? "注册并进入工作台" : "登录并进入工作台"}
          </button>
        </form>

        <div className={styles.social}>
          <p>第三方登录</p>
          <div className={styles.socialGrid}>
            {socialStatus.map((item) => {
              const disabled = busy || !item.configured;
              return (
                <button
                  key={item.id}
                  type="button"
                  className={styles.socialButton}
                  disabled={disabled}
                  onClick={() => handleSocialLogin(item.id)}
                >
                  <span>{item.label}</span>
                  <span className={item.configured ? styles.socialStateReady : styles.socialStatePending}>
                    {item.configured ? "已配置" : "即将可用"}
                  </span>
                </button>
              );
            })}
          </div>
          <p className={styles.socialHint}>显示“即将可用”代表后端还没配置对应平台。</p>
        </div>

        {status.text ? (
          <p
            className={
              status.type === "error"
                ? `${styles.status} ${styles.statusError}`
                : status.type === "ok"
                  ? `${styles.status} ${styles.statusOk}`
                  : styles.status
            }
          >
            {status.text}
          </p>
        ) : null}

        <div className={styles.switchRow}>
          {mode === "login" ? (
            <button type="button" className={styles.linkButton} onClick={() => router.push("/register")} disabled={busy}>
              没有账号？去注册
            </button>
          ) : (
            <button type="button" className={styles.linkButton} onClick={() => router.push("/login")} disabled={busy}>
              已有账号？去登录
            </button>
          )}
        </div>

        <button type="button" className={styles.backButton} onClick={() => router.push("/enter")} disabled={busy}>
          返回介绍页
        </button>
      </section>
    </main>
  );
}
