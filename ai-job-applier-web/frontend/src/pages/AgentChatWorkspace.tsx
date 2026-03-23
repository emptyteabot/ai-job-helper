import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Form, Input, Modal, message } from 'antd';
import { apiUrl, authHeaders, wsUrl } from '../lib/api';

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
  role: 'assistant' | 'user' | 'system' | 'tool';
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

const starterPrompts = [
  'Help me find AI product internships in Shanghai and start execution.',
  'Analyze my current resume and tell me the top three fixes.',
  'Show my recent records first, then adjust my next round.',
];

const AgentChatWorkspace: React.FC = () => {
  const [token, setToken] = useState('');
  const [user, setUser] = useState<User | null>(null);
  const [showLogin, setShowLogin] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [session, setSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [uploadingResume, setUploadingResume] = useState(false);
  const [actionState, setActionState] = useState<'idle' | 'running'>('idle');
  const [resumeUploadTick, setResumeUploadTick] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    const savedToken = window.localStorage.getItem('token');
    if (!savedToken) {
      setShowLogin(true);
      return;
    }
    setToken(savedToken);
    void bootstrap(savedToken);
  }, []);

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
    const particleCount = 720;
    const connectionDistance = 92;
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
          vx: (Math.random() - 0.5) * 0.95,
          vy: (Math.random() - 0.5) * 0.95,
          size: Math.random() * 1.1 + 0.35,
          alpha: Math.random() * 0.32 + 0.08,
          glow: 0,
        });
      }
    };

    const drawConnections = () => {
      for (let i = 0; i < particles.length; i += 1) {
        const a = particles[i];
        for (let j = i + 1; j < i + 10 && j < particles.length; j += 1) {
          const b = particles[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const d2 = dx * dx + dy * dy;
          if (d2 < connectionDistance * connectionDistance) {
            const dist = Math.sqrt(d2);
            const alpha = (1 - dist / connectionDistance) * 0.12 + (a.glow + b.glow) * 0.16;
            ctx.beginPath();
                        ctx.strokeStyle = `rgba(34,211,238,${Math.min(alpha, 0.35)})`;
            ctx.lineWidth = 0.55;
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }
    };

    const onPointer = (event: MouseEvent) => {
      mouse.x = event.clientX;
      mouse.y = event.clientY;
    };

    const animate = () => {
      ctx.fillStyle = 'rgba(13,14,19,0.16)';
      ctx.fillRect(0, 0, width, height);

      for (let i = 0; i < particles.length; i += 1) {
        const point = particles[i];
        point.x += point.vx;
        point.y += point.vy;

        if (point.x < 0) point.x = width;
        if (point.x > width) point.x = 0;
        if (point.y < 0) point.y = height;
        if (point.y > height) point.y = 0;

        const dx = mouse.x - point.x;
        const dy = mouse.y - point.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < forceRadius) {
          const force = (forceRadius - dist) / forceRadius;
          const angle = Math.atan2(dy, dx);
          point.x -= Math.cos(angle) * force * 12;
          point.y -= Math.sin(angle) * force * 12;
          point.glow = force * 0.72;
        } else {
          point.glow *= 0.92;
        }

        ctx.beginPath();
        ctx.fillStyle = '#22D3EE';
        ctx.globalAlpha = Math.min(1, point.alpha + point.glow);
        ctx.arc(point.x, point.y, point.size + point.glow * 1.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1;
      }

      drawConnections();
      raf = window.requestAnimationFrame(animate);
    };

    resize();
    seed();
    animate();
    window.addEventListener('resize', resize);
    window.addEventListener('mousemove', onPointer);
    return () => {
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', onPointer);
      window.cancelAnimationFrame(raf);
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages]);

  const bootstrap = async (authToken: string) => {
    await loadUserInfo(authToken);
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

  const ensureSession = async (authToken: string) => {
    const existingId = window.localStorage.getItem('chat_session_id') || '';
    if (existingId) {
      const existing = await fetch(apiUrl(`/api/chat/sessions/${existingId}`), {
        headers: authHeaders({ Authorization: `Bearer ${authToken}` }),
      });
      if (existing.ok) {
        const payload = await existing.json();
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
      window.localStorage.setItem('chat_session_id', payload.session.id);
      setSession(payload.session);
      setMessages(payload.session.messages || []);
    }
  };

  const syncSessionMessages = (nextSession: ChatSession) => {
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
        message.error(payload.detail || payload.message || 'Application records');
        return;
      }
      setToken(payload.token);
      setUser(payload.user);
      window.localStorage.setItem('token', payload.token);
      setShowLogin(false);
      await ensureSession(payload.token);
      message.success(authMode === 'login' ? 'Application records' : 'Application records');
    } catch (error) {
      message.error('Application records');
    }
  };

  const appendLocalMessage = (messageRow: ChatMessage) => {
    setMessages((current) => [...current, messageRow]);
  };

  const persistEvent = async (content: string, role: 'system' | 'tool' | 'assistant' = 'system', meta: Record<string, any> = {}) => {
    if (!session?.id || !token) return;
    try {
      const response = await fetch(apiUrl(`/api/chat/sessions/${session.id}/events`), {
        method: 'POST',
        headers: authHeaders({ Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }),
        body: JSON.stringify({ role, content, meta }),
      });
      if (!response.ok) return;
      const payload = await response.json();
      if (payload.success && payload.session) {
        syncSessionMessages(payload.session);
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
    const textResponse = await fetch(apiUrl(`/api/resume/text/${firstResume.filename}`), {
      headers: authHeaders({ Authorization: `Bearer ${token}` }),
    });
    const textPayload = await textResponse.json();
    return { filename: firstResume.filename, text: textPayload.text || '' };
  };

  const executeActions = async (actions: Array<Record<string, any>>) => {
    if (!actions.length) return;
    setActionState('running');
    for (const action of actions) {
      const actionType = String(action.type || '');
      try {
        if (actionType === 'request_resume_upload') {
          const content = 'Application recordsApplication recordsApplication recordsApplication recordsApplication recordsSign up';
          appendLocalMessage({ id: crypto.randomUUID(), role: 'system', content });
          await persistEvent(content);
          continue;
        }

        if (actionType === 'search_jobs') {
          const content = `Application records ${action.city || 'Sign up'} / ${action.keyword || 'Sign up'} ...`;
          appendLocalMessage({ id: crypto.randomUUID(), role: 'system', content });
          const response = await fetch(
            apiUrl(`/api/jobs/search?keyword=${encodeURIComponent(action.keyword || 'Application records?')}&city=${encodeURIComponent(action.city || 'Sign up')}&max_count=${Number(action.max_count || 10)}`),
            { headers: authHeaders({ Authorization: `Bearer ${token}` }) },
          );
          const payload = await response.json();
          const jobs = payload.jobs || [];
          const sample = jobs.slice(0, 3).map((job: any) => `${job.title || 'Sign up'} @ ${job.company || 'Application records'}`).join('?');
          const resultText = jobs.length
            ? `Sign up? ${jobs.length} Application recordsSign up ${payload.provider || 'unknown'}Application records${sample}`
            : 'Application recordsApplication recordsApplication recordsSign up?';
          appendLocalMessage({ id: crypto.randomUUID(), role: 'tool', content: resultText });
          await persistEvent(resultText, 'tool', { action: actionType, count: jobs.length, provider: payload.provider || '' });
          continue;
        }

        if (actionType === 'analyze_resume') {
          const resume = await fetchLatestResumeText();
          if (!resume.text.trim()) {
            const content = 'Application recordsApplication recordsApplication recordsApplication recordsApplication recordsApplication records?';
            appendLocalMessage({ id: crypto.randomUUID(), role: 'system', content });
            await persistEvent(content, 'system', { action: actionType });
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
          const preview = keys.slice(0, 3).map((key) => `${key}: ${JSON.stringify(results[key]).slice(0, 120)}`).join(' | ');
          const content = keys.length ? `Application recordsSign up?${preview}` : 'Application recordsApplication recordsApplication records?';
          appendLocalMessage({ id: crypto.randomUUID(), role: 'tool', content });
          await persistEvent(content, 'tool', { action: actionType, keys });
          continue;
        }

        if (actionType === 'show_records') {
          const response = await fetch(apiUrl(`/api/records?limit=${Number(action.limit || 8)}`), {
            headers: authHeaders({ Authorization: `Bearer ${token}` }),
          });
          const payload = await response.json();
          const records = payload.records || [];
          const content = records.length
            ? `Sign up ${records.length} Application records${records.slice(0, 5).map((row: any) => `${row.job_title || row.title} / ${row.status}`).join('?')}`
            : 'Application recordsApplication recordsApplication recordsSign up';
          appendLocalMessage({ id: crypto.randomUUID(), role: 'tool', content });
          await persistEvent(content, 'tool', { action: actionType, count: records.length });
          continue;
        }

        if (actionType === 'open_challenge_center') {
          const qs = new URLSearchParams({
            provider: 'boss',
            autostart: '1',
            keyword: String(action.keyword || 'python'),
            city: String(action.city || 'Sign up'),
            max_count: String(action.max_count || 10),
          });
          const sessionId = window.localStorage.getItem('last_boss_session_id') || '';
          if (sessionId) qs.set('session_id', sessionId);
          const content = `Application recordsApplication recordsApplication records?/challenge-center?${qs.toString()}`;
          appendLocalMessage({ id: crypto.randomUUID(), role: 'system', content });
          await persistEvent(content, 'system', { action: actionType, href: `/challenge-center?${qs.toString()}` });
          continue;
        }

        if (actionType === 'run_apply') {
          const resume = await fetchLatestResumeText();
          if (!resume.text.trim()) {
            const content = 'Application recordsApplication recordsApplication recordsApplication recordsApplication recordsSign up?';
            appendLocalMessage({ id: crypto.randomUUID(), role: 'system', content });
            await persistEvent(content, 'system', { action: actionType });
            continue;
          }
          const startText = `Application records?${action.city || 'Sign up'} / ${action.keyword || 'Sign up'}`;
          appendLocalMessage({ id: crypto.randomUUID(), role: 'system', content: startText });
          await persistEvent(startText, 'system', { action: actionType });
          await new Promise<void>((resolve) => {
            const ws = new WebSocket(wsUrl('/api/apply/ws'));
            ws.onopen = () => {
              ws.send(JSON.stringify({
                token,
                keyword: action.keyword || 'Application records?',
                city: action.city || 'Sign up',
                max_count: Number(action.max_count || 10),
                resume_text: resume.text,
              }));
            };
            ws.onmessage = (event) => {
              const payload = JSON.parse(event.data);
              if (payload.error) {
                const content = payload.message || 'Application records';
                appendLocalMessage({ id: crypto.randomUUID(), role: 'system', content });
                void persistEvent(content, 'system', { action: actionType, error: true });
                ws.close();
                return;
              }
              if (payload.stage && payload.message) {
                const content = `${payload.stage}: ${payload.message}`;
                appendLocalMessage({ id: crypto.randomUUID(), role: 'tool', content });
                void persistEvent(content, 'tool', { action: actionType, stage: payload.stage });
              }
              if (payload.stage === 'completed') {
                ws.close();
              }
            };
            ws.onerror = () => {
              const content = 'Application recordsApplication records?';
              appendLocalMessage({ id: crypto.randomUUID(), role: 'system', content });
              void persistEvent(content, 'system', { action: actionType, error: true });
              resolve();
            };
            ws.onclose = () => resolve();
          });
        }
      } catch (error) {
        const content = `${actionType} Application records?`;
        appendLocalMessage({ id: crypto.randomUUID(), role: 'system', content });
        await persistEvent(content, 'system', { action: actionType, error: true });
      }
    }
    setActionState('idle');
  };

  const sendPrompt = async (customText?: string) => {
    if (!session?.id || !token) return;
    const content = (customText || input).trim();
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
        message.error(payload.detail || payload.message || 'Application records');
        return;
      }
      syncSessionMessages(payload.session);
      const actions = payload.assistant?.actions || [];
      await executeActions(actions);
    } catch (error) {
      message.error('Application records');
    } finally {
      setSending(false);
    }
  };

  const uploadResume = async (file: File) => {
    if (!token) return;
    setUploadingResume(true);
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
        message.error(payload.detail || payload.message || 'Application recordsSign up');
        return;
      }
      setResumeUploadTick((current) => current + 1);
      const content = `Application recordsSign up${payload.filename}`;
      appendLocalMessage({ id: crypto.randomUUID(), role: 'system', content });
      await persistEvent(content, 'system', { action: 'resume_upload', filename: payload.filename });
      message.success('Application recordsSign up');
    } catch (error) {
      message.error('Application recordsSign up');
    } finally {
      setUploadingResume(false);
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

  const displayMessages = useMemo(() => messages, [messages]);

  return (
    <div className="min-h-screen bg-[#0d0e13] text-cyan-50">
      <canvas id="agent-chat-canvas" className="pointer-events-none fixed inset-0 z-0 h-full w-full" />
      <div className="pointer-events-none fixed inset-0 z-0 bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.16),transparent_40%),radial-gradient(circle_at_bottom,rgba(96,165,250,0.12),transparent_32%)]" />

      <div className="relative z-10 flex min-h-screen flex-col">
        <header className="sticky top-0 z-20 border-b border-cyan-400/20 bg-[#0d0e13]/60 backdrop-blur-3xl">
          <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-4 py-4 md:px-6">
            <div>
              <div className="font-headline text-2xl font-black uppercase tracking-tight text-cyan-300">AgentHelpJob</div>
              <div className="text-xs uppercase tracking-[0.18em] text-cyan-100/45">Agent Console / hidden tools underneath</div>
            </div>
            <div className="flex items-center gap-3">
              {user ? (
                <>
                  <div className="rounded-full border border-cyan-400/20 bg-black/20 px-4 py-2 text-right">
                    <div className="text-sm font-semibold text-cyan-100">{user.nickname || user.email || 'user'}</div>
                    <div className="text-xs text-cyan-100/50">{user.plan} ? quota {user.remaining_quota}</div>
                  </div>
                  <button className="rounded-full border border-cyan-400/30 px-4 py-2 text-sm text-cyan-200 transition hover:bg-cyan-400/10" type="button" onClick={handleLogout}>
                    Sign up
                  </button>
                </>
              ) : (
                <button className="rounded-full bg-cyan-400 px-5 py-2 text-sm font-bold text-[#0d0e13]" type="button" onClick={() => setShowLogin(true)}>
                  Sign up
                </button>
              )}
            </div>
          </div>
        </header>

        <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-4 pb-6 pt-6 md:px-6">
          <div className="mb-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/25 bg-cyan-500/8 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-cyan-300">
              <span className="h-2 w-2 animate-pulse rounded-full bg-cyan-300" />
              agentic console ready
            </div>
            <h1 className="mt-5 max-w-4xl font-headline text-4xl font-bold tracking-tight text-white md:text-6xl">
              Application recordsApplication recordsSign up?
              <span className="block text-cyan-300">Application recordsApplication recordsSign up?</span>
            </h1>
            <p className="mt-4 max-w-3xl text-base leading-7 text-cyan-100/68 md:text-lg">
              Application recordsApplication recordsApplication recordsApplication recordsApplication recordsApplication recordsSign up?Challenge Application recordsApplication recordsApplication recordsSign up? LLM Application recordsApplication recordsSign up
            </p>
          </div>

          <div className="grid flex-1 grid-cols-1 gap-4 xl:grid-cols-[1fr_280px]">
            <section className="flex min-h-[65vh] flex-col overflow-hidden rounded-[32px] border border-cyan-400/18 bg-black/28 shadow-[0_20px_80px_rgba(0,0,0,0.35)] backdrop-blur-2xl">
              <div className="border-b border-cyan-400/12 px-5 py-4 md:px-6">
                <div className="text-sm font-semibold text-cyan-100">Application records?</div>
                <div className="mt-1 text-sm text-cyan-100/52">
                  {actionState === 'running' ? 'Application recordsApplication recordsApplication recordsApplication recordsSign up' : 'Application recordsApplication recordsApplication recordsApplication recordsSign up?'}
                </div>
              </div>

              <div className="flex-1 overflow-y-auto px-4 py-5 md:px-6">
                {displayMessages.length === 0 ? (
                  <div className="flex h-full flex-col items-center justify-center text-center">
                    <div className="max-w-2xl">
                      <div className="text-2xl font-semibold text-cyan-100">Application recordsApplication records?</div>
                      <div className="mt-3 text-cyan-100/55">
                        Application recordsApplication records AI Application recordsApplication recordsApplication recordsApplication recordsApplication recordsApplication recordsApplication recordsApplication recordsApplication records
                      </div>
                    </div>
                    <div className="mt-8 flex flex-wrap justify-center gap-3">
                      {starterPrompts.map((prompt) => (
                        <button
                          key={prompt}
                          className="rounded-full border border-cyan-400/20 bg-cyan-500/6 px-4 py-2 text-sm text-cyan-100/80 transition hover:border-cyan-300/45 hover:bg-cyan-500/12"
                          type="button"
                          onClick={() => void sendPrompt(prompt)}
                        >
                          {prompt}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-5">
                    {displayMessages.map((row) => (
                      <div key={row.id} className={`flex ${row.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div
                          className={`max-w-[88%] rounded-[28px] px-5 py-4 text-sm leading-7 md:text-[15px] ${
                            row.role === 'user'
                              ? 'bg-cyan-400 text-[#0d0e13] shadow-[0_0_30px_rgba(34,211,238,0.22)]'
                              : row.role === 'assistant'
                                ? 'border border-cyan-400/16 bg-[#10141f]/88 text-cyan-50'
                                : 'border border-cyan-400/12 bg-black/26 text-cyan-100/75'
                          }`}
                        >
                          <div className="mb-1 text-[11px] uppercase tracking-[0.16em] opacity-60">
                            {row.role === 'user' ? 'you' : row.role === 'assistant' ? 'agent' : 'system'}
                          </div>
                          <div className="break-words whitespace-pre-wrap">{row.content}</div>
                          {row.role === 'assistant' && row.actions?.length ? (
                            <div className="mt-3 flex flex-wrap gap-2 text-[11px] uppercase tracking-[0.16em] text-cyan-300/70">
                              {row.actions.map((action, index) => (
                                <span key={`${row.id}-${index}`} className="rounded-full border border-cyan-400/15 px-2 py-1">
                                  {String(action.type || 'action')}
                                </span>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      </div>
                    ))}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </div>

              <div className="border-t border-cyan-400/12 px-4 py-4 md:px-6">
                <div className="mb-3 flex flex-wrap items-center gap-2 text-xs text-cyan-100/48">
                  <span className="rounded-full border border-cyan-400/12 px-3 py-1">Application recordsSign up? / Sign up / Challenge / Application records / Sign up</span>
                  {resumeUploadTick > 0 ? <span className="rounded-full border border-cyan-400/12 px-3 py-1">Application records?</span> : null}
                </div>
                <div className="flex items-end gap-3">
                  <button className="rounded-full border border-cyan-400/20 px-4 py-3 text-sm text-cyan-100/75 transition hover:bg-cyan-500/10" type="button" onClick={() => fileInputRef.current?.click()} disabled={uploadingResume}>
                    {uploadingResume ? 'Sign up?...' : 'Application records'}
                  </button>
                  <div className="flex-1 rounded-[28px] border border-cyan-400/18 bg-black/22 px-4 py-3">
                    <textarea
                      className="min-h-[56px] w-full resize-none bg-transparent text-[15px] leading-7 text-cyan-50 outline-none placeholder:text-cyan-100/32"
                      placeholder="Application recordsApplication recordsApplication recordsSign up? AI Application recordsApplication recordsApplication recordsApplication records"
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
                    {sending ? 'Sign up?...' : 'Sign up'}
                  </button>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.txt"
                  className="hidden"
                  onChange={(event) => {
                    const file = event.target.files?.[0];
                    if (file) {
                      void uploadResume(file);
                    }
                    event.currentTarget.value = '';
                  }}
                />
              </div>
            </section>

            <aside className="space-y-4">
              <div className="rounded-[28px] border border-cyan-400/16 bg-black/24 p-5 backdrop-blur-xl">
                <div className="text-xs uppercase tracking-[0.16em] text-cyan-300/70">Sign up</div>
                <div className="mt-3 text-sm text-cyan-100/70">{user ? `Sign up?${user.nickname || user.email}` : 'Sign up?'}</div>
                <div className="mt-2 text-sm text-cyan-100/70">{user ? `Sign up?${user.plan} ? Application records ${user.remaining_quota}` : 'Application records?'}</div>
                <div className="mt-2 text-sm text-cyan-100/70">Sign up?{session?.id ? session.id.slice(0, 8) : 'Sign up?'}</div>
              </div>

              <div className="rounded-[28px] border border-cyan-400/16 bg-black/24 p-5 backdrop-blur-xl">
                <div className="text-xs uppercase tracking-[0.16em] text-cyan-300/70">Application records</div>
                <div className="mt-3 space-y-2 text-sm text-cyan-100/70">
                  <div>Application recordsApplication records?</div>
                  <div>Application recordsApplication records?</div>
                  <div>Application recordsApplication records?</div>
                  <div>Challenge Center / Application records</div>
                </div>
              </div>

              <div className="rounded-[28px] border border-cyan-400/16 bg-black/24 p-5 backdrop-blur-xl">
                <div className="text-xs uppercase tracking-[0.16em] text-cyan-300/70">Application records</div>
                <div className="mt-3 flex flex-col gap-2">
                  <a className="rounded-full border border-cyan-400/18 px-4 py-2 text-sm text-cyan-100/80 transition hover:bg-cyan-500/10" href="/challenge-center">
                    Challenge Center
                  </a>
                  <a className="rounded-full border border-cyan-400/18 px-4 py-2 text-sm text-cyan-100/80 transition hover:bg-cyan-500/10" href="/dashboard">
                    Application records
                  </a>
                  <a className="rounded-full border border-cyan-400/18 px-4 py-2 text-sm text-cyan-100/80 transition hover:bg-cyan-500/10" href="/records">
                    Application records
                  </a>
                </div>
              </div>
            </aside>
          </div>
        </main>
      </div>

      <Modal title={authMode === 'login' ? 'Application records?' : 'Application records?'} open={showLogin} footer={null} onCancel={() => setShowLogin(false)}>
        <Form layout="vertical" onFinish={handleAuth}>
          <Form.Item label="Sign up" name="email" rules={[{ required: true, message: 'Application records?' }]}>
            <Input />
          </Form.Item>
          <Form.Item label="Sign up" name="password" rules={[{ required: true, message: 'Application records?' }]}>
            <Input.Password />
          </Form.Item>
          {authMode === 'register' ? (
            <Form.Item label="Sign up" name="nickname">
              <Input />
            </Form.Item>
          ) : null}
          <button className="mt-2 w-full rounded-full bg-cyan-400 px-4 py-3 font-bold text-[#0d0e13]" type="submit">
            {authMode === 'login' ? 'Sign up' : 'Sign up'}
          </button>
        </Form>
        <button className="mt-4 w-full rounded-full border border-cyan-400/18 px-4 py-3 text-sm text-cyan-100/80" type="button" onClick={() => setAuthMode((current) => (current === 'login' ? 'register' : 'login'))}>
          {authMode === 'login' ? 'Application recordsApplication records' : 'Application recordsApplication records'}
        </button>
      </Modal>
    </div>
  );
};

export default AgentChatWorkspace;
