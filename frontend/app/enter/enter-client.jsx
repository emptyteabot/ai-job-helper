"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import styles from "./enter-client.module.css";

const HERO_EYEBROW = "AGENTHELPJOB";
const HERO_TITLE = "多 Agent 帮你改简历，自动投简历";
const HERO_SUBTITLE =
  "岗位筛选、简历重写、投递执行与失败回退全部自动衔接。你只做关键确认，其余流程由多 Agent 并行推进。";

const TRUST_POINTS = ["岗位详情真伪校验", "验证码节点可追踪", "按量计费，单岗位消耗 1 Credit"];

const TERMINAL_EVENTS = [
  { stage: "intake", status: "running", chunk: "接收简历并生成岗位执行图..." },
  { stage: "intake", status: "done", chunk: "执行图完成：改写、校验、投递三路并行。" },
  { stage: "rewrite", status: "running", chunk: "按 JD 重写简历，强化量化成果与关键词..." },
  { stage: "rewrite", status: "done", chunk: "简历 v4 已生成，匹配度从 62% 提升到 87%。" },
  { stage: "verify", status: "running", chunk: "多源解析岗位链接并过滤入口页..." },
  { stage: "verify", status: "done", chunk: "锁定 12 条可直接申请的岗位详情页。" },
  { stage: "apply", status: "running", chunk: "本机浏览器执行投递，等待必要人工确认..." },
  { stage: "apply", status: "done", chunk: "已完成 7 份投递，5 份在验证码后继续。" },
];

const STREAM_LINES = TERMINAL_EVENTS.map((item, index) => ({
  id: `${index}-${item.stage}-${item.status}`,
  prompt: item.status === "done" ? ">" : "$",
  text: item.chunk,
  done: item.status === "done",
}));

const CAPABILITIES = [
  {
    title: "多源真链路解析",
    detail: "聚合多来源检索与结构化规则，剔除频道页，仅保留可直达投递的岗位详情页。",
  },
  {
    title: "本机自动化执行",
    detail: "关键操作在你本地浏览器执行，账号与会话不离开设备。",
  },
  {
    title: "结果导向计费",
    detail: "以可验证结果作为计费节点，避免只按过程消耗预算。",
  },
];

export default function EnterClient({ redirectTo = "/" }) {
  const router = useRouter();
  const [visibleStreamCount, setVisibleStreamCount] = useState(1);
  const [activeStreamIndex, setActiveStreamIndex] = useState(0);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  const [accessCode, setAccessCode] = useState("");
  const [redeemBusy, setRedeemBusy] = useState(false);
  const [redeemStatus, setRedeemStatus] = useState({ type: "idle", text: "" });
  const redeemInputRef = useRef(null);

  const loginPath =
    redirectTo && redirectTo !== "/"
      ? `/login?from=${encodeURIComponent(redirectTo)}`
      : "/login";

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return undefined;
    }

    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setPrefersReducedMotion(mediaQuery.matches);
    update();

    mediaQuery.addEventListener("change", update);
    return () => mediaQuery.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    if (prefersReducedMotion) {
      setVisibleStreamCount(STREAM_LINES.length);
      setActiveStreamIndex(-1);
      return undefined;
    }

    setVisibleStreamCount(1);
    setActiveStreamIndex(0);

    let nextIndex = 1;
    const timers = [];

    const queueNext = () => {
      if (nextIndex >= STREAM_LINES.length) {
        const endTimer = window.setTimeout(() => setActiveStreamIndex(-1), 360);
        timers.push(endTimer);
        return;
      }

      const delay = STREAM_LINES[nextIndex].done ? 380 : 520;
      const timer = window.setTimeout(() => {
        setVisibleStreamCount(nextIndex + 1);
        setActiveStreamIndex(nextIndex);
        nextIndex += 1;
        queueNext();
      }, delay);
      timers.push(timer);
    };

    const startTimer = window.setTimeout(queueNext, 420);
    timers.push(startTimer);

    return () => {
      timers.forEach((timer) => window.clearTimeout(timer));
    };
  }, [prefersReducedMotion]);

  async function handleRedeemAccessCode(event) {
    event.preventDefault();
    const code = accessCode.trim().toUpperCase();
    if (!code) {
      setRedeemStatus({ type: "error", text: "访问码不能为空。" });
      return;
    }

    setRedeemBusy(true);
    setRedeemStatus({ type: "info", text: "" });
    try {
      const response = await fetch("/api/access", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          code,
          machine_name:
            typeof window !== "undefined"
              ? `${window.navigator.platform || "browser"} / ${window.navigator.language || ""}`
              : "",
        }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok || !payload?.success) {
        throw new Error(payload?.message || payload?.error || "访问码兑换失败");
      }

      setRedeemStatus({ type: "ok", text: "访问码已通过，正在进入工作台..." });
      router.replace(redirectTo || "/");
      router.refresh();
    } catch (error) {
      setRedeemStatus({
        type: "error",
        text: error?.message || "访问码兑换失败，请稍后重试。",
      });
    } finally {
      setRedeemBusy(false);
    }
  }

  return (
    <main className={styles.page}>
      <div className={styles.backdrop} aria-hidden="true" />
      <div className={styles.particleField} aria-hidden="true" />

      <header className={styles.nav}>
        <button className={styles.brand} onClick={() => router.push("/")}>
          agenthelpjob
        </button>
        <button className={styles.navAction} onClick={() => router.push(loginPath)}>
          登录
        </button>
      </header>

      <section className={styles.hero}>
        <p className={styles.eyebrow}>
          <span className={styles.eyebrowDot} />
          {HERO_EYEBROW}
        </p>
        <h1 className={styles.title}>{HERO_TITLE}</h1>
        <p className={styles.subtitle}>{HERO_SUBTITLE}</p>
        <div className={styles.actions}>
          <button
            className={styles.primaryButton}
            onClick={() => redeemInputRef.current?.focus()}
          >
            输入访问码
          </button>
          <button className={styles.secondaryButton} onClick={() => router.push(loginPath)}>
            登录工作台
          </button>
        </div>
        <form className={styles.redeemPanel} onSubmit={handleRedeemAccessCode}>
          <div className={styles.redeemCopy}>
            <strong>付款后拿到访问码，直接在这里进入</strong>
            <p>不要再走共享万能码，也不要继续依赖一条坏掉的公开 checkout。付款后拿到访问码，就在这里兑换。</p>
          </div>
          <div className={styles.redeemRow}>
            <input
              ref={redeemInputRef}
              className={styles.redeemInput}
              value={accessCode}
              onChange={(event) => setAccessCode(event.target.value)}
              placeholder="输入访问码"
            />
            <button type="submit" className={styles.primaryButton} disabled={redeemBusy}>
              {redeemBusy ? "校验中..." : "兑换访问码"}
            </button>
          </div>
          {redeemStatus.text ? (
            <p
              className={
                redeemStatus.type === "error"
                  ? `${styles.redeemStatus} ${styles.redeemStatusError}`
                  : redeemStatus.type === "ok"
                    ? `${styles.redeemStatus} ${styles.redeemStatusOk}`
                    : styles.redeemStatus
              }
            >
              {redeemStatus.text}
            </p>
          ) : null}
        </form>
        <ul className={styles.trustRow}>
          {TRUST_POINTS.map((point) => (
            <li key={point}>{point}</li>
          ))}
        </ul>
      </section>

      <section className={styles.streamSection}>
        <div className={styles.streamHead}>
          <h2>实时流式执行</h2>
          <p>按阶段连续输出，关键节点可回溯。</p>
        </div>
        <div className={styles.streamPanel} role="log" aria-live="polite" aria-atomic="false">
          <div className={styles.streamPanelHead}>
            <span className={styles.streamDotRed} />
            <span className={styles.streamDotAmber} />
            <span className={styles.streamDotGreen} />
            <strong>agenthelpjob execution stream</strong>
          </div>
          <div className={styles.streamPanelBody}>
            {STREAM_LINES.slice(0, visibleStreamCount).map((line, index) => {
              const lineClassName = [
                styles.streamLine,
                line.done ? styles.streamLineDone : "",
                index === activeStreamIndex ? styles.streamLineActive : "",
              ]
                .filter(Boolean)
                .join(" ");

              return (
                <p key={line.id} className={lineClassName}>
                  <span className={styles.streamPrompt}>{line.prompt}</span>
                  <span>{line.text}</span>
                </p>
              );
            })}
          </div>
        </div>
      </section>

      <section className={styles.capabilitySection}>
        <ul className={styles.capabilityGrid}>
          {CAPABILITIES.map((item) => (
            <li key={item.title} className={styles.capabilityCard}>
              <h3>{item.title}</h3>
              <p>{item.detail}</p>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
