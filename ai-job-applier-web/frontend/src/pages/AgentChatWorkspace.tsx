import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Form, Input, Modal, message } from 'antd';
import { apiUrl, authHeaders, wsUrl } from '../lib/api';

type Role = 'assistant' | 'user' | 'system' | 'tool';

interface User {
  id: string;
  email?: string;
  nickname?: string;
  plan: string;
  remaining_quota: number;
}

interface LoginFormValues {
  email: string;
  password: string;
  nickname?: string;
}

interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  created_at?: string;
  actions?: Array<Record<string, any>>;
  meta?: Record<string, any>;
}

interface ChatSession {
  id: string;
  title?: string;
  messages?: ChatMessage[];
  context?: Record<string, any>;
}

const STARTER_PROMPTS = [
  '????? AI ??????????',
  '????????????????',
  '??????????????????',
];

const makeId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

const AgentChatWorkspace: React.FC = () => {
  const [token, setToken] = useState('');
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [running, setRunning] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [showLogin, setShowLogin] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [resumeReady, setResumeReady] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    const savedToken = window.localStorage.getItem('token') || '';
    if (!savedToken) {
      setShowLogin(true);
      return;
    }
    setToken(savedToken);
    void bootstrap(savedToken);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages]);

  useEffect(() => {
    const canvas = document.getElementById('agent-chat-canvas') as HTMLCanvasElement | null;
    if (!canvas) return undefined;
    const ctx = canvas.getContext('2d');
    if (!ctx) return undefined;

    let width = window.innerWidth;
    let height = window.innerHeight;
    let raf = 0;
    const mouse = { x: -1000, y: -1000 };
    const particles: Array<{ x: number; y: number; vx: number; vy: number; size: number; alpha: number; glow: number }> = [];
    const particleCount = 520;
    const connectionDistance = 90;
    const forceRadius = 220;

    const resize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width;
      canvas.height = height;
    };

    const seed = () => {
      particles.length = 0;
      for (let i = 0; i < particleCount; i += 1) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * 0.9,
          vy: (Math.random() - 0.5) * 0.9,
          size: Math.random() * 1.2 + 0.3,
          alpha: Math.random() * 0.28 + 0.06,
          glow: 0,
        });
      }
    };

    const drawLines = () => {
      for (let i = 0; i < particles.length; i += 1) {
        const a = particles[i];
        for (let j = i + 1; j < i + 9 && j < particles.length; j += 1) {
          const b = particles[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const d2 = dx * dx + dy * dy;
          if (d2 < connectionDistance * connectionDistance) {
            const d = Math.sqrt(d2);
            const alpha = (1 - d / connectionDistance) * 0.12 + (a.glow + b.glow) * 0.15;
            ctx.beginPath();
            ctx.strokeStyle = `rgba(34,211,238,${Math.min(alpha, 0.32)})`;
            ctx.lineWidth = 0.55;
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }
    };

    const animate = () => {
      ctx.fillStyle = 'rgba(13,14,19,0.18)';
      ctx.fillRect(0, 0, width, height);

      for (let i = 0; i < particles.length; i += 1) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        const dx = mouse.x - p.x;
        const dy = mouse.y - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < forceRadius) {
          const force = (forceRadius - dist) / forceRadius;
          const angle = Math.atan2(dy, dx);
          p.x -= Math.cos(angle) * force * 12;
          p.y -= Math.sin(angle) * force * 12;
          p.glow = force * 0.7;
        } else {
          p.glow *= 0.9;
        }

        ctx.beginPath();
        ctx.fillStyle = '#22D3EE';
        ctx.globalAlpha = Math.min(1, p.alpha + p.glow);
        ctx.arc(p.x, p.y, p.size + p.glow * 1.4, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1;
      }

      drawLines();
      raf = window.requestAnimationFrame(animate);
    };

    const onMove = (event: MouseEvent) => {
      mouse.x = event.clientX;
      mouse.y = event.clientY;
    };

    resize();
    seed();
    animate();
    window.addEventListener('resize', resize);
    window.addEventListener('mousemove', onMove);
    return () => {
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', onMove);
      window.cancelAnimationFrame(raf);
    };
  }, []);

  const bootstrap = async (authToken: string) => {
    await loadUserInfo(authToken);
    await loadResumeState(authToken);
    await ensureSession(authToken);
  };

  const loadUserInfo = async (authToken: string) => {
    const response = await fetch(apiUrl('/api/user/info'), {
      headers: authHeaders({ Authorization: `Bearer ${authToken}` }),
    });
    const payload = await response.json();
    if (payload.success) {
      setUser(payload.user);
    }
  };

  const loadResumeState = async (authToken: string) => {
    const response = await fetch(apiUrl('/api/resume/list'), {
      headers: authHeaders({ Authorization: `Bearer ${authToken}` }),
    });
    const payload = await response.json();
    setResumeReady(Boolean((payload.resumes || []).length));
  };

  const ensureSession = async (authToken: string) => {
    const sessionId = window.localStorage.getItem('chat_session_id') || '';
    if (sessionId) {
      const response = await fetch(apiUrl(`/api/chat/sessions/${sessionId}`), {
        headers: authHeaders({ Authorization: `Bearer ${authToken}` }),
      });
      if (response.ok) {
        const payload = await response.json();
        setSession(payload.session);
        setMessages(payload.session?.messages || []);
        return;
      }
    }

    const response = await fetch(apiUrl('/api/chat/sessions'), {
      method: 'POST',
      headers: authHeaders({ Authorization: `Bearer ${authToken}`, 'Content-Type': 'application/json' }),
      body: JSON.stringify({ title: 'Agent Console' }),
    });
    const payload = await response.json();
    if (payload.success) {
      setSession(payload.session);
      setMessages(payload.session?.messages || []);
      window.localStorage.setItem('chat_session_id', payload.session.id);
    }
  };

  const syncSession = (nextSession: ChatSession) => {
    setSession(nextSession);
    setMessages(nextSession.messages || []);
    window.localStorage.setItem('chat_session_id', nextSession.id);
  };

  const handleAuth = async (values: LoginFormValues) => {
    try {
      const endpoint = authMode === 'login' ? '/api/auth/local-login' : '/api/auth/local-register';
      const response = await fetch(apiUrl(endpoint), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(
          authMode === 'login'
            ? { email: values.email, password: values.password }
            : { email: values.email, password: values.password, nickname: values.nickname },
        ),
      });
      const payload = await response.json();
      if (!payload.success) {
        message.error(payload.detail || payload.message || '????');
        return;
      }
      setToken(payload.token);
      setUser(payload.user);
      window.localStorage.setItem('token', payload.token);
      setShowLogin(false);
      await bootstrap(payload.token);
      message.success(authMode === 'login' ? '????' : '????');
    } catch {
      message.error('????');
    }
  };

  const persistEvent = async (content: string, role: Role = 'system', meta: Record<string, any> = {}) => {
    if (!session?.id || !token) return;
    try {
      const response = await fetch(apiUrl(`/api/chat/sessions/${session.id}/events`), {
        method: 'POST',
        headers: authHeaders({ Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }),
        body: JSON.stringify({ role, content, meta }),
      });
      if (response.ok) {
        const payload = await response.json();
        if (payload.success && payload.session) {
          syncSession(payload.session);
        }
      }
    } catch {
      return;
    }
  };

  const fetchLatestResumeText = async () => {
    const listResponse = await fetch(apiUrl('/api/resume/list'), { headers: authHeaders({ Authorization: `Bearer ${token}` }) });
    const listPayload = await listResponse.json();
    const firstResume = (listPayload.resumes || [])[0];
    if (!firstResume?.filename) {
      return { filename: '', text: '' };
    }
    const textResponse = await fetch(apiUrl(`/api/resume/text/${firstResume.filename}`), { headers: authHeaders({ Authorization: `Bearer ${token}` }) });
    const textPayload = await textResponse.json();
    return { filename: firstResume.filename, text: textPayload.text || '' };
  };

  const executeActions = async (actions: Array<Record<string, any>>) => {
    if (!actions.length) return;
    setRunning(true);
    for (const action of actions) {
      const actionType = String(action.type || '');
      try {
        if (actionType === 'request_resume_upload') {
          await persistEvent('??????????????????????');
          continue;
        }

        if (actionType === 'search_jobs') {
          await persistEvent(`???? ${action.city || '??'} / ${action.keyword || '??'} ...`, 'tool', { action: actionType });
          const response = await fetch(
            apiUrl(`/api/jobs/search?keyword=${encodeURIComponent(action.keyword || '?????')}&city=${encodeURIComponent(action.city || '??')}&max_count=${Number(action.max_count || 10)}`),
            { headers: authHeaders({ Authorization: `Bearer ${token}` }) },
          );
          const payload = await response.json();
          const jobs = payload.jobs || [];
          const sample = jobs.slice(0, 3).map((job: any) => `${job.title || '??'} @ ${job.company || '????'}`).join('?');
          const content = jobs.length
            ? `??? ${jobs.length} ?????? ${payload.provider || 'unknown'}????${sample}`
            : '?????????????';
          await persistEvent(content, 'tool', { action: actionType, count: jobs.length, provider: payload.provider || '' });
          continue;
        }

        if (actionType === 'analyze_resume') {
          const resume = await fetchLatestResumeText();
          if (!resume.text.trim()) {
            await persistEvent('??????????????????????');
            continue;
          }
          const response = await fetch(apiUrl('/api/analysis/resume'), {
            method: 'POST',
            headers: authHeaders({ Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }),
            body: JSON.stringify({ resume_text: resume.text, analysis_type: 'full' }),
          });
          const payload = await response.json();
          const results = payload.results || {};
          const keys = Object.keys(results);
          const preview = keys.slice(0, 3).map((key) => `${key}: ${JSON.stringify(results[key]).slice(0, 90)}`).join(' | ');
          await persistEvent(keys.length ? `???????${preview}` : '???????????', 'tool', { action: actionType, keys });
          continue;
        }

        if (actionType === 'show_records') {
          const response = await fetch(apiUrl(`/api/records?limit=${Number(action.limit || 8)}`), { headers: authHeaders({ Authorization: `Bearer ${token}` }) });
          const payload = await response.json();
          const records = payload.records || [];
          const content = records.length
            ? `?? ${records.length} ????${records.slice(0, 5).map((row: any) => `${row.job_title || row.title} / ${row.status}`).join('?')}`
            : '????????????';
          await persistEvent(content, 'tool', { action: actionType, count: records.length });
          continue;
        }

        if (actionType === 'open_challenge_center') {
          const qs = new URLSearchParams({
            provider: 'boss',
            autostart: '1',
            keyword: String(action.keyword || 'python'),
            city: String(action.city || '??'),
            max_count: String(action.max_count || 10),
          });
          const lastBossSessionId = window.localStorage.getItem('last_boss_session_id') || '';
          if (lastBossSessionId) qs.set('session_id', lastBossSessionId);
          await persistEvent(`?????????? /challenge-center?${qs.toString()}`, 'system', { action: actionType, href: `/challenge-center?${qs.toString()}` });
          continue;
        }

        if (actionType === 'run_apply') {
          const resume = await fetchLatestResumeText();
          if (!resume.text.trim()) {
            await persistEvent('??????????????');
            continue;
          }
          await persistEvent(`?????${action.city || '??'} / ${action.keyword || '??'}`, 'system', { action: actionType });
          await new Promise<void>((resolve) => {
            const ws = new WebSocket(wsUrl('/api/apply/ws'));
            ws.onopen = () => {
              ws.send(JSON.stringify({
                token,
                keyword: action.keyword || '?????',
                city: action.city || '??',
                max_count: Number(action.max_count || 10),
                resume_text: resume.text,
              }));
            };
            ws.onmessage = (event) => {
              const payload = JSON.parse(event.data);
              if (payload.error) {
                void persistEvent(payload.message || '????', 'system', { action: actionType, error: true });
                ws.close();
                return;
              }
              if (payload.stage && payload.message) {
                void persistEvent(`${payload.stage}: ${payload.message}`, 'tool', { action: actionType, stage: payload.stage });
              }
              if (payload.stage === 'completed') {
                ws.close();
              }
            };
            ws.onerror = () => {
              void persistEvent('?????????', 'system', { action: actionType, error: true });
              resolve();
            };
            ws.onclose = () => resolve();
          });
        }
      } catch {
        await persistEvent(`${actionType} ?????`, 'system', { action: actionType, error: true });
      }
    }
    setRunning(false);
  };

  const sendPrompt = async (customPrompt?: string) => {
    if (!session?.id || !token) return;
    const content = (customPrompt || input).trim();
    if (!content) return;
    setSending(true);
    setInput('');
    try {
      const response = await fetch(apiUrl(`/api/chat/sessions/${session.id}/messages`), {
        method: 'POST',
        headers: authHeaders({ Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }),
        body: JSON.stringify({ content }),
      });
      const payload = await response.json();
      if (!response.ok || !payload.success) {
        message.error(payload.detail || payload.message || '????');
        return;
      }
      syncSession(payload.session);
      await executeActions(payload.assistant?.actions || []);
    } catch {
      message.error('????');
    } finally {
      setSending(false);
    }
  };

  const uploadResume = async (file: File) => {
    if (!token) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await fetch(apiUrl('/api/resume/upload'), {
        method: 'POST',
        headers: authHeaders({ Authorization: `Bearer ${token}` }),
        body: formData,
      });
      const payload = await response.json();
      if (!response.ok || !payload.success) {
        message.error(payload.detail || payload.message || '??????');
        return;
      }
      setResumeReady(true);
      setResumeUploadTick((value) => value + 1);
      await persistEvent(`??????${payload.filename}`, 'system', { action: 'resume_upload', filename: payload.filename });
      message.success('??????');
    } catch {
      message.error('??????');
    } finally {
      setUploading(false);
    }
  };

  const handleLogout = () => {
    window.localStorage.removeItem('token');
    window.localStorage.removeItem('chat_session_id');
    setToken('');
    setUser(null);
    setSession(null);
    setMessages([]);
    setShowLogin(true);
  };

  const latestAssistant = useMemo(() => messages.slice().reverse().find((item) => item.role === 'assistant') || null, [messages]);

  const renderMessage = (row: ChatMessage) => {
    const roleLabel = row.role === 'user' ? '??' : row.role === 'assistant' ? '???' : row.role === 'tool' ? '??' : '??';
    const chipClass = row.role === 'user'
      ? 'bg-cyan-400 text-[#0d0e13]'
      : row.role === 'assistant'
        ? 'border border-cyan-400/16 bg-[#10141f]/88 text-cyan-50'
        : 'border border-cyan-400/12 bg-black/26 text-cyan-100/75';
    return (
      <div key={row.id} className={`flex ${row.role === 'user' ? 'justify-end' : 'justify-start'}`}>
        <div className={`max-w-[88%] rounded-[28px] px-5 py-4 text-sm leading-7 md:text-[15px] ${chipClass}`}>
          <div className="mb-1 text-[11px] uppercase tracking-[0.16em] opacity-60">{roleLabel}</div>
          <div className="break-words whitespace-pre-wrap">{row.content}</div>
          {row.actions?.length ? (
            <div className="mt-3 flex flex-wrap gap-2 text-[11px] uppercase tracking-[0.16em] text-cyan-300/70">
              {row.actions.map((action, index) => (
                <span key={`${row.id}-${index}`} className="rounded-full border border-cyan-400/15 px-2 py-1">
                  {String(action.type || 'action')}
                </span>
              ))}
            </div>
          ) : null}
          {row.meta?.action ? (
            <div className="mt-3 rounded-2xl border border-cyan-400/12 bg-cyan-500/5 px-3 py-3 text-xs text-cyan-100/70">
              <div className="uppercase tracking-[0.16em] text-cyan-300/75">???</div>
              <div className="mt-2">???{String(row.meta.action)}</div>
              {row.meta.stage ? <div>???{String(row.meta.stage)}</div> : null}
              {row.meta.provider ? <div>???{String(row.meta.provider)}</div> : null}
              {typeof row.meta.count === 'number' ? <div>???{String(row.meta.count)}</div> : null}
            </div>
          ) : null}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-[#0d0e13] text-cyan-50">
      <canvas id="agent-chat-canvas" className="pointer-events-none fixed inset-0 z-0 h-full w-full" />
      <div className="pointer-events-none fixed inset-0 z-0 bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.16),transparent_40%),radial-gradient(circle_at_bottom,rgba(96,165,250,0.12),transparent_32%)]" />

      <div className="relative z-10 flex min-h-screen flex-col">
        <header className="sticky top-0 z-20 border-b border-cyan-400/20 bg-[#0d0e13]/60 backdrop-blur-3xl">
          <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-4 py-4 md:px-6">
            <div>
              <div className="font-headline text-2xl font-black uppercase tracking-tight text-cyan-300">AgentHelpJob</div>
              <div className="text-xs uppercase tracking-[0.18em] text-cyan-100/45">????? / ????????</div>
            </div>
            <div className="flex items-center gap-3">
              {user ? (
                <>
                  <div className="rounded-full border border-cyan-400/20 bg-black/20 px-4 py-2 text-right">
                    <div className="text-sm font-semibold text-cyan-100">{user.nickname || user.email || 'user'}</div>
                    <div className="text-xs text-cyan-100/50">{user.plan} ? ???? {user.remaining_quota}</div>
                  </div>
                  <button className="rounded-full border border-cyan-400/30 px-4 py-2 text-sm text-cyan-200 transition hover:bg-cyan-400/10" type="button" onClick={handleLogout}>
                    ??
                  </button>
                </>
              ) : (
                <button className="rounded-full bg-cyan-400 px-5 py-2 text-sm font-bold text-[#0d0e13]" type="button" onClick={() => setShowLogin(true)}>
                  ??
                </button>
              )}
            </div>
          </div>
        </header>

        <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-4 pb-6 pt-6 md:px-6">
          <div className="mb-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/25 bg-cyan-500/8 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-cyan-300">
              <span className="h-2 w-2 animate-pulse rounded-full bg-cyan-300" />
              ?????????
            </div>
            <h1 className="mt-5 max-w-4xl font-headline text-4xl font-bold tracking-tight text-white md:text-6xl">
              ??????????
              <span className="block text-cyan-300">??????????</span>
            </h1>
            <p className="mt-4 max-w-3xl text-base leading-7 text-cyan-100/68 md:text-lg">
              ??????????????????????Challenge ????????????? GPT ?????????
            </p>
          </div>

          <div className="grid flex-1 grid-cols-1 gap-4 xl:grid-cols-[1fr_280px]">
            <section className="flex min-h-[65vh] flex-col overflow-hidden rounded-[32px] border border-cyan-400/18 bg-black/28 shadow-[0_20px_80px_rgba(0,0,0,0.35)] backdrop-blur-2xl">
              <div className="border-b border-cyan-400/12 px-5 py-4 md:px-6">
                <div className="text-sm font-semibold text-cyan-100">?????</div>
                <div className="mt-1 text-sm text-cyan-100/52">
                  {running ? '????????????????' : '???????????????????'}
                </div>
              </div>

              <div className="flex-1 overflow-y-auto px-4 py-5 md:px-6">
                {messages.length === 0 ? (
                  <div className="flex h-full flex-col items-center justify-center text-center">
                    <div className="max-w-2xl">
                      <div className="text-2xl font-semibold text-cyan-100">?????????</div>
                      <div className="mt-3 text-cyan-100/55">
                        ???????? AI ?????????????????????????????
                      </div>
                    </div>
                    <div className="mt-8 flex flex-wrap justify-center gap-3">
                      {STARTER_PROMPTS.map((prompt) => (
                        <button key={prompt} className="rounded-full border border-cyan-400/20 bg-cyan-500/6 px-4 py-2 text-sm text-cyan-100/80 transition hover:border-cyan-300/45 hover:bg-cyan-500/12" type="button" onClick={() => void sendPrompt(prompt)}>
                          {prompt}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-5">
                    {messages.map(renderMessage)}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </div>

              <div className="border-t border-cyan-400/12 px-4 py-4 md:px-6">
                <div className="mb-3 flex flex-wrap items-center gap-2 text-xs text-cyan-100/48">
                  <span className="rounded-full border border-cyan-400/12 px-3 py-1">??????? / ?? / Challenge / ???? / ??</span>
                  {resumeReady ? <span className="rounded-full border border-cyan-400/12 px-3 py-1">?????</span> : null}
                  {latestAssistant?.actions?.length ? <span className="rounded-full border border-cyan-400/12 px-3 py-1">???????</span> : null}
                </div>
                <div className="flex items-end gap-3">
                  <button className="rounded-full border border-cyan-400/20 px-4 py-3 text-sm text-cyan-100/75 transition hover:bg-cyan-500/10" type="button" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
                    {uploading ? '???...' : '????'}
                  </button>
                  <div className="flex-1 rounded-[28px] border border-cyan-400/18 bg-black/22 px-4 py-3">
                    <textarea
                      className="min-h-[56px] w-full resize-none bg-transparent text-[15px] leading-7 text-cyan-50 outline-none placeholder:text-cyan-100/32"
                      placeholder="???????? AI ??????????????"
                      value={input}
                      onChange={(event) => setInput(event.target.value)}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter' && !event.shiftKey) {
                          event.preventDefault();
                          void sendPrompt();
                        }
                      }}
                    />
                  </div>
                  <button className="rounded-full bg-cyan-400 px-6 py-3 text-sm font-bold text-[#0d0e13] shadow-[0_0_30px_rgba(34,211,238,0.24)] transition hover:-translate-y-[1px]" type="button" disabled={sending || !input.trim()} onClick={() => void sendPrompt()}>
                    {sending ? '???...' : '??'}
                  </button>
                </div>
                <input ref={fileInputRef} type="file" accept=".pdf,.docx,.txt" className="hidden" onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) void uploadResume(file);
                  event.currentTarget.value = '';
                }} />
              </div>
            </section>

            <aside className="space-y-4">
              <div className="rounded-[28px] border border-cyan-400/16 bg-black/24 p-5 backdrop-blur-xl">
                <div className="text-xs uppercase tracking-[0.16em] text-cyan-300/70">??</div>
                <div className="mt-3 text-sm text-cyan-100/70">{user ? `???${user.nickname || user.email}` : '???'}</div>
                <div className="mt-2 text-sm text-cyan-100/70">{user ? `???${user.plan} ? ???? ${user.remaining_quota}` : '?????'}</div>
                <div className="mt-2 text-sm text-cyan-100/70">???{session?.id ? session.id.slice(0, 8) : '???'}</div>
              </div>

              <div className="rounded-[28px] border border-cyan-400/16 bg-black/24 p-5 backdrop-blur-xl">
                <div className="text-xs uppercase tracking-[0.16em] text-cyan-300/70">???</div>
                <div className="mt-3 space-y-2 text-sm text-cyan-100/70">
                  <div>???????</div>
                  <div>?????????</div>
                  <div>?????????</div>
                  <div>Challenge Center / ????</div>
                </div>
              </div>

              <div className="rounded-[28px] border border-cyan-400/16 bg-black/24 p-5 backdrop-blur-xl">
                <div className="text-xs uppercase tracking-[0.16em] text-cyan-300/70">????</div>
                <div className="mt-3 flex flex-col gap-2">
                  <a className="rounded-full border border-cyan-400/18 px-4 py-2 text-sm text-cyan-100/80 transition hover:bg-cyan-500/10" href="/challenge-center">Challenge Center</a>
                  <a className="rounded-full border border-cyan-400/18 px-4 py-2 text-sm text-cyan-100/80 transition hover:bg-cyan-500/10" href="/dashboard">????</a>
                  <a className="rounded-full border border-cyan-400/18 px-4 py-2 text-sm text-cyan-100/80 transition hover:bg-cyan-500/10" href="/records">????</a>
                </div>
              </div>
            </aside>
          </div>
        </main>
      </div>

      <Modal title={authMode === 'login' ? '?????' : '?????'} open={showLogin} footer={null} onCancel={() => setShowLogin(false)}>
        <Form layout="vertical" onFinish={handleAuth}>
          <Form.Item label="??" name="email" rules={[{ required: true, message: '?????' }]}>
            <Input />
          </Form.Item>
          <Form.Item label="??" name="password" rules={[{ required: true, message: '?????' }]}>
            <Input.Password />
          </Form.Item>
          {authMode === 'register' ? <Form.Item label="??" name="nickname"><Input /></Form.Item> : null}
          <button className="mt-2 w-full rounded-full bg-cyan-400 px-4 py-3 font-bold text-[#0d0e13]" type="submit">
            {authMode === 'login' ? '??' : '??'}
          </button>
        </Form>
        <button className="mt-4 w-full rounded-full border border-cyan-400/18 px-4 py-3 text-sm text-cyan-100/80" type="button" onClick={() => setAuthMode((current) => (current === 'login' ? 'register' : 'login'))}>
          {authMode === 'login' ? '????????' : '????????'}
        </button>
      </Modal>
    </div>
  );
};

export default AgentChatWorkspace;
