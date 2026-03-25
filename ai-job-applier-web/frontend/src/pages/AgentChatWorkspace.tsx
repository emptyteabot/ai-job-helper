import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Form, Input, message } from 'antd';
import { apiUrl, authHeaders, wsUrl } from '../lib/api';
import { assistedGuidance, AssistedStatus, deriveAssistedStatus } from './assistedGuidance';

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
  '帮我找上海 AI 产品实习，并开始执行。',
  '先分析我当前简历，指出最该改的三处。',
  '先看最近投递记录，再帮我调整下一轮方向。',
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
  const [stage, setStage] = useState('等待启动');
  const [progress, setProgress] = useState(0);
  const [successCount, setSuccessCount] = useState(0);
  const [failedCount, setFailedCount] = useState(0);
  const [assistedStatus, setAssistedStatus] = useState<AssistedStatus>('standby');
  const [seedPromptPending, setSeedPromptPending] = useState('');
  const [seedPromptAutoSent, setSeedPromptAutoSent] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const seeded = (params.get('seed_prompt') || '').trim();
    if (seeded) {
      setSeedPromptPending(seeded);
      setInput((current) => current || seeded);
      setStage('已接收首页指令');
      params.delete('seed_prompt');
      const nextQuery = params.toString();
      const nextUrl = `${window.location.pathname}${nextQuery ? `?${nextQuery}` : ''}${window.location.hash || ''}`;
      window.history.replaceState({}, '', nextUrl);
    }

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
    const particleCount = 480;
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
          vx: (Math.random() - 0.5) * 0.9,
          vy: (Math.random() - 0.5) * 0.9,
          size: Math.random() * 1.15 + 0.3,
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
            const dist = Math.sqrt(d2);
            const alpha = (1 - dist / connectionDistance) * 0.12 + (a.glow + b.glow) * 0.16;
            ctx.beginPath();
            ctx.strokeStyle = `rgba(34,211,238,${Math.min(alpha, 0.34)})`;
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
    await Promise.all([loadUserInfo(authToken), loadResumeState(authToken)]);
    await ensureSession(authToken);
  };

  const loadUserInfo = async (authToken: string) => {
    const response = await fetch(apiUrl('/api/user/info'), {
      headers: authHeaders({ Authorization: `Bearer ${authToken}` }),
    });
    const payload = await response.json();
    if (payload.success) setUser(payload.user);
  };

  const loadResumeState = async (authToken: string) => {
    const response = await fetch(apiUrl('/api/resume/list'), {
      headers: authHeaders({ Authorization: `Bearer ${authToken}` }),
    });
    const payload = await response.json();
    setResumeReady(Boolean((payload.resumes || []).length));
  };

  const ensureSession = async (authToken: string) => {
    const existingId = window.localStorage.getItem('chat_session_id') || '';
    if (existingId) {
      const response = await fetch(apiUrl(`/api/chat/sessions/${existingId}`), {
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
      body: JSON.stringify({ title: 'AI 求职舱' }),
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
        message.error(payload.detail || payload.message || '登录失败');
        return;
      }
      setToken(payload.token);
      setUser(payload.user);
      window.localStorage.setItem('token', payload.token);
      setShowLogin(false);
      await bootstrap(payload.token);
      message.success(authMode === 'login' ? '登录成功' : '注册成功');
    } catch {
      message.error('登录失败');
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
      if (!response.ok) return;
      const payload = await response.json();
      if (payload.success && payload.session) syncSession(payload.session);
    } catch {
      return;
    }
  };

  const fetchLatestResumeText = async () => {
    const listResponse = await fetch(apiUrl('/api/resume/list'), { headers: authHeaders({ Authorization: `Bearer ${token}` }) });
    const listPayload = await listResponse.json();
    const firstResume = (listPayload.resumes || [])[0];
    if (!firstResume?.filename) return { filename: '', text: '' };
    const textResponse = await fetch(apiUrl(`/api/resume/text/${firstResume.filename}`), { headers: authHeaders({ Authorization: `Bearer ${token}` }) });
    const textPayload = await textResponse.json();
    return { filename: firstResume.filename, text: textPayload.text || '' };
  };

  const executeActions = async (actions: Array<Record<string, any>>) => {
    if (!actions.length) return;
    const total = actions.length;
    let completed = 0;
    let runSuccess = 0;
    let runFailed = 0;
    setRunning(true);
    setStage('准备执行');
    setProgress(4);
    setAssistedStatus('standby');

    const markProgress = (nextStage: string, floor: number) => {
      setStage(nextStage);
      setProgress((value) => Math.max(value, Math.min(95, Math.max(floor, Math.round((completed / total) * 100)))));
    };

    for (const action of actions) {
      const actionType = String(action.type || '');
      let actionSucceeded = false;
      try {
        if (actionType === 'request_resume_upload') {
          markProgress('等待简历上传', 14);
          await persistEvent('当前还没有可用简历。先上传一份简历，我再继续推进。');
          actionSucceeded = true;
          continue;
        }

        if (actionType === 'search_jobs') {
          markProgress('搜索岗位', 20);
          await persistEvent(`正在搜索 ${action.city || '全国'} / ${action.keyword || '岗位'} ...`, 'tool', { action: actionType });
          const response = await fetch(
            apiUrl(`/api/jobs/search?keyword=${encodeURIComponent(action.keyword || '产品实习生')}&city=${encodeURIComponent(action.city || '全国')}&max_count=${Number(action.max_count || 10)}`),
            { headers: authHeaders({ Authorization: `Bearer ${token}` }) },
          );
          const payload = await response.json();
          const jobs = payload.jobs || [];
          const sample = jobs.slice(0, 3).map((job: any) => `${job.title || '岗位'} @ ${job.company || '未知公司'}`).join('；');
          const content = jobs.length
            ? `已找到 ${jobs.length} 个岗位，来源 ${payload.provider || 'unknown'}。样例：${sample}`
            : '这轮搜索没有返回可用岗位结果。';
          await persistEvent(content, 'tool', { action: actionType, count: jobs.length, provider: payload.provider || '' });
          actionSucceeded = response.ok;
          continue;
        }

        if (actionType === 'analyze_resume') {
          markProgress('分析简历', 38);
          const resume = await fetchLatestResumeText();
          if (!resume.text.trim()) {
            await persistEvent('当前没有可分析的简历文本。先上传简历，再让我分析。');
            actionSucceeded = false;
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
          await persistEvent(keys.length ? `简历分析完成。${preview}` : '简历分析没有返回有效结果。', 'tool', { action: actionType, keys });
          actionSucceeded = response.ok && keys.length > 0;
          continue;
        }

        if (actionType === 'show_records') {
          markProgress('读取记录', 52);
          const response = await fetch(apiUrl(`/api/records?limit=${Number(action.limit || 8)}`), { headers: authHeaders({ Authorization: `Bearer ${token}` }) });
          const payload = await response.json();
          const records = payload.records || [];
          const content = records.length
            ? `最近 ${records.length} 条记录：${records.slice(0, 5).map((row: any) => `${row.job_title || row.title} / ${row.status}`).join('；')}`
            : '当前还没有可展示的执行记录。';
          await persistEvent(content, 'tool', { action: actionType, count: records.length });
          actionSucceeded = response.ok;
          continue;
        }

        if (actionType === 'open_challenge_center') {
          markProgress('等待人工接管', 70);
          setAssistedStatus('challenge_required');
          const qs = new URLSearchParams({
            provider: 'boss',
            autostart: '1',
            keyword: String(action.keyword || 'python'),
            city: String(action.city || '全国'),
            max_count: String(action.max_count || 10),
          });
          const lastBossSessionId = window.localStorage.getItem('last_boss_session_id') || '';
          if (lastBossSessionId) qs.set('session_id', lastBossSessionId);
          await persistEvent(`需要人工接管时，请进入 /challenge-center?${qs.toString()}`, 'system', { action: actionType, href: `/challenge-center?${qs.toString()}` });
          actionSucceeded = true;
          continue;
        }

        if (actionType === 'run_apply') {
          markProgress('执行投递', 82);
          const resume = await fetchLatestResumeText();
          if (!resume.text.trim()) {
            await persistEvent('执行前缺少简历文本。先上传简历。');
            actionSucceeded = false;
            continue;
          }
          await persistEvent(`开始执行：${action.city || '全国'} / ${action.keyword || '岗位'}`, 'system', { action: actionType });
          let wsCompleted = false;
          let wsErrored = false;
          await new Promise<void>((resolve) => {
            const ws = new WebSocket(wsUrl('/api/apply/ws'));
            ws.onopen = () => {
              ws.send(JSON.stringify({
                token,
                keyword: action.keyword || '产品实习生',
                city: action.city || '全国',
                max_count: Number(action.max_count || 10),
                resume_text: resume.text,
              }));
            };
            ws.onmessage = (event) => {
              const payload = JSON.parse(event.data);
              if (payload.error) {
                wsErrored = true;
                void persistEvent(payload.message || '执行失败', 'system', { action: actionType, error: true });
                ws.close();
                return;
              }
              if (payload.stage && payload.message) {
                void persistEvent(`${payload.stage}: ${payload.message}`, 'tool', { action: actionType, stage: payload.stage });
              }
              if (payload.stage === 'completed') {
                wsCompleted = true;
                ws.close();
              }
            };
            ws.onerror = () => {
              wsErrored = true;
              void persistEvent('执行链路连接异常。', 'system', { action: actionType, error: true });
              resolve();
            };
            ws.onclose = () => resolve();
          });
          actionSucceeded = wsCompleted && !wsErrored;
          continue;
        }

        markProgress(`执行 ${actionType || '动作'}`, 60);
        await persistEvent(`暂未实现动作：${actionType || 'unknown'}`, 'system', { action: actionType, error: true });
        actionSucceeded = false;
      } catch {
        await persistEvent(`${actionType} 执行失败。`, 'system', { action: actionType, error: true });
        actionSucceeded = false;
      } finally {
        completed += 1;
        if (actionSucceeded) {
          runSuccess += 1;
          setSuccessCount((value) => value + 1);
        } else {
          runFailed += 1;
          setFailedCount((value) => value + 1);
        }
        setProgress((value) => Math.max(value, Math.min(98, Math.round((completed / total) * 100))));
      }
    }
    setStage(runFailed > 0 ? '部分完成' : '执行完成');
    setProgress((value) => Math.max(value, runFailed > 0 ? 96 : 100));
    setRunning(false);
  };

  const requireReadyWorkspace = (pendingContent?: string) => {
    if (token && session?.id) return true;
    if (pendingContent?.trim()) {
      setInput(pendingContent.trim());
    }
    setShowLogin(true);
    if (!token) {
      setStage('等待登录');
      message.warning('请先登录后再发送任务。');
      return false;
    }
    setStage('恢复会话中');
    void ensureSession(token);
    message.warning('会话尚未就绪，请先完成登录验证。');
    return false;
  };

  const sendPrompt = async (customPrompt?: string) => {
    const content = (customPrompt || input).trim();
    if (!content) return;
    if (!requireReadyWorkspace(content)) return;
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
        message.error(payload.detail || payload.message || '发送失败');
        return;
      }
      syncSession(payload.session);
      await executeActions(payload.assistant?.actions || []);
    } catch {
      message.error('发送失败');
    } finally {
      setSending(false);
    }
  };

  useEffect(() => {
    if (!seedPromptPending || seedPromptAutoSent) return;
    if (!token || !session?.id) return;
    setSeedPromptAutoSent(true);
    void sendPrompt(seedPromptPending);
    setSeedPromptPending('');
  }, [seedPromptPending, seedPromptAutoSent, token, session?.id]);

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
        message.error(payload.detail || payload.message || '简历上传失败');
        return;
      }
      setResumeReady(true);
      await persistEvent(`简历已上传：${payload.filename}`, 'system', { action: 'resume_upload', filename: payload.filename });
      message.success('简历上传成功');
    } catch {
      message.error('简历上传失败');
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
    setStage('等待启动');
    setProgress(0);
    setSuccessCount(0);
    setFailedCount(0);
    setAssistedStatus('standby');
  };

  const latestAssistant = useMemo(() => messages.slice().reverse().find((item) => item.role === 'assistant') || null, [messages]);
  const completionRate = successCount + failedCount > 0 ? Math.round((successCount / (successCount + failedCount)) * 100) : 0;
  const guidance = assistedGuidance[assistedStatus];

  const renderMessage = (row: ChatMessage) => {
    const roleLabel = row.role === 'user'
      ? '用户'
      : row.role === 'assistant'
        ? '智能体'
        : row.role === 'tool'
          ? '工具'
          : '系统';

    if (row.role === 'user') {
      return (
        <div key={row.id} className="flex justify-end">
          <div className="max-w-[88%] rounded-[28px] bg-cyan-500/10 px-5 py-4 text-sm leading-7 md:text-[15px] text-[#0d0e13]">
            <div className="mb-1 text-[11px] uppercase tracking-[0.16em] text-cyan-100/70">{roleLabel}</div>
            <div className="break-words whitespace-pre-wrap">{row.content}</div>
          </div>
        </div>
      );
    }

    const isTool = row.role === 'tool';
    const isTakeover = Boolean(row.meta?.href) || String(row.meta?.action || '').toLowerCase().includes('challenge');
    const cardLabel = isTakeover ? '接管卡' : isTool ? '工具结果卡' : '状态卡';
    const variant = isTakeover
      ? {
        border: 'border-amber-400/50',
        bg: 'bg-gradient-to-br from-amber-500/15 via-black/40 to-black/80',
        shadow: 'shadow-[0_25px_70px_rgba(191,129,16,0.35)]',
        text: 'text-amber-100',
      }
      : isTool
        ? {
          border: 'border-cyan-400/30',
          bg: 'bg-cyan-500/10',
          shadow: 'shadow-[0_20px_50px_rgba(34,211,238,0.25)]',
          text: 'text-cyan-100',
        }
        : {
          border: 'border-cyan-400/20',
          bg: 'bg-[#10131f]/90',
          shadow: 'shadow-[0_20px_60px_rgba(6,10,18,0.8)]',
          text: 'text-cyan-200',
        };

    const metaEntries: React.ReactNode[] = [];
    if (row.meta?.action) {
      metaEntries.push(
        <div key={`${row.id}-action`} className="text-xs text-cyan-100/70">
          动作：{String(row.meta.action)}
        </div>,
      );
    }
    if (row.meta?.stage) {
      metaEntries.push(
        <div key={`${row.id}-stage`} className="text-xs text-cyan-100/70">
          阶段：{String(row.meta.stage)}
        </div>,
      );
    }
    if (row.meta?.provider) {
      metaEntries.push(
        <div key={`${row.id}-provider`} className="text-xs text-cyan-100/70">
          来源：{String(row.meta.provider)}
        </div>,
      );
    }
    if (typeof row.meta?.count === 'number') {
      metaEntries.push(
        <div key={`${row.id}-count`} className="text-xs text-cyan-100/70">
          数量：{String(row.meta.count)}
        </div>,
      );
    }
    if (row.meta?.filename) {
      metaEntries.push(
        <div key={`${row.id}-file`} className="text-xs text-cyan-100/70">
          文件：{String(row.meta.filename)}
        </div>,
      );
    }
    if (row.meta?.error) {
      metaEntries.push(
        <div key={`${row.id}-error`} className="text-xs text-rose-300">
          错误：{String(row.meta.error)}
        </div>,
      );
    }
    if (row.meta?.href) {
      metaEntries.push(
        <a
          key={`${row.id}-href`}
          className="text-xs text-cyan-100/80 underline decoration-dotted decoration-cyan-300/60"
          href={String(row.meta.href)}
          target="_blank"
          rel="noreferrer"
        >
          前往接管页面
        </a>,
      );
    }

    return (
      <div key={row.id} className="flex justify-start">
        <div className={`max-w-[88%] rounded-[28px] border px-5 py-4 text-sm leading-7 md:text-[15px] ${variant.border} ${variant.bg} ${variant.shadow}`}>
          <div className="flex items-center justify-between text-[11px] uppercase tracking-[0.16em]">
            <span className="opacity-70">{cardLabel}</span>
            <span className={`text-[11px] uppercase tracking-[0.16em] opacity-70 ${variant.text}`}>{roleLabel}</span>
          </div>
          <div className="mt-2 break-words whitespace-pre-wrap text-cyan-50">{row.content}</div>
          {row.actions?.length ? (
            <div className="mt-3 flex flex-wrap gap-2 text-[11px] uppercase tracking-[0.16em] text-cyan-200/70">
              {row.actions.map((action, index) => (
                <span key={`${row.id}-${index}`} className="rounded-full border border-cyan-400/30 px-2 py-1">
                  {String(action.type || 'action')}
                </span>
              ))}
            </div>
          ) : null}
          {metaEntries.length ? (
            <div className="mt-3 space-y-1 text-xs text-cyan-100/70">
              {metaEntries}
            </div>
          ) : null}
        </div>
      </div>
    );
  };

  const stageLabel = stage ? stage : '待命中';
  const statusWidth = Math.min(Math.max(progress, completionRate), 100);
  const workspaceStageLabel = `控制台阶段 · ${stageLabel}`;
  const workspaceProgressWidth = statusWidth;
  const workspaceStatusBadges = [
    resumeReady ? '简历已就绪' : '等待简历上传',
    session?.id ? `会话 ${session.id.slice(0, 8)}` : '会话未就绪',
    `动作 ${successCount + failedCount} · 成功 ${successCount} / 失败 ${failedCount}`,
  ];
  const guidanceActionLink = guidance.actionUrl || (assistedStatus === 'challenge_required' ? '/challenge-center' : undefined);
  const infoCardBase = 'rounded-[28px] border border-cyan-400/16 bg-black/24 px-5 py-5 shadow-[0_20px_60px_rgba(0,0,0,0.45)] backdrop-blur-3xl';
  const authLockRequired = !token || !session?.id;

  return (
    <div className="min-h-screen bg-[#0d0e13] text-cyan-50">
      <canvas id="agent-chat-canvas" className="pointer-events-none fixed inset-0 z-0 h-full w-full" />
      <div className="pointer-events-none fixed inset-0 z-0 bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.16),transparent_40%),radial-gradient(circle_at_bottom,rgba(96,165,250,0.12),transparent_32%)]" />

      <div className="relative z-10 flex min-h-screen flex-col">
        <header className="sticky top-0 z-20 border-b border-cyan-400/20 bg-[#0d0e13]/60 backdrop-blur-3xl">
          <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-4 py-4 md:px-6">
            <div>
              <div className="font-headline text-2xl font-black uppercase tracking-tight text-cyan-300">AgentHelpJob</div>
              <div className="text-xs uppercase tracking-[0.18em] text-cyan-100/45">对话控制台 / 功能藏在水面之下</div>
            </div>
            <div className="flex items-center gap-3">
              {user ? (
                <>
                  <div className="rounded-full border border-cyan-400/20 bg-black/20 px-4 py-2 text-right">
                    <div className="text-sm font-semibold text-cyan-100">{user.nickname || user.email || 'user'}</div>
                    <div className="text-xs text-cyan-100/50">{user.plan} · 剩余额度 {user.remaining_quota}</div>
                  </div>
                  <button className="rounded-full border border-cyan-400/30 px-4 py-2 text-sm text-cyan-200 transition hover:bg-cyan-400/10" type="button" onClick={handleLogout}>
                    退出
                  </button>
                </>
              ) : (
                <button className="rounded-full bg-cyan-400 px-5 py-2 text-sm font-bold text-[#0d0e13]" type="button" onClick={() => setShowLogin(true)}>
                  登录
                </button>
              )}
            </div>
          </div>
        </header>

        <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-4 pb-8 pt-6 md:px-6">
          <section className="space-y-5">
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/25 bg-cyan-500/8 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-cyan-300">
              <span className="h-2 w-2 animate-pulse rounded-full bg-cyan-300" />
              智能体控制台已就绪
            </div>
            <h1 className="max-w-4xl font-headline text-4xl font-bold tracking-tight text-white md:text-6xl">
              把求职藏进一个对话框，
              <span className="block text-cyan-300">把复杂度埋进冰山下面。</span>
            </h1>
            <p className="max-w-3xl text-base leading-7 text-cyan-100/68 md:text-lg">
              你只描述目标。后台会去做搜索、简历分析、执行推进、Challenge 接管和表单填充。中途你可以像和 GPT 对话一样追加条件。
            </p>
          </section>

          <section className="mt-6">
            <div className={`${infoCardBase} border-cyan-400/25 bg-[#03060f]/80`}>
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <div className="text-[0.65rem] uppercase tracking-[0.28em] text-cyan-200/70">Landing → Workspace</div>
                  <div className="text-2xl font-semibold text-white">{workspaceStageLabel}</div>
                </div>
                <span className="text-[0.65rem] uppercase tracking-[0.35em] text-cyan-100/60">粒子场同步</span>
              </div>
              <div className="mt-4 h-2 w-full rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-cyan-400 via-sky-500 to-blue-500"
                  style={{ width: `${workspaceProgressWidth}%` }}
                />
              </div>
              <p className="mt-3 text-sm text-cyan-100/70">
                当前控制台就是刚才首页光环的延伸。粒子背景、按钮节奏、阶段提示都会跟着这个房间一起振幅。
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {workspaceStatusBadges.map((badge) => (
                  <span key={badge} className="rounded-full border border-cyan-400/30 px-3 py-1 text-[10px] uppercase tracking-[0.25em] text-cyan-100/80">
                    {badge}
                  </span>
                ))}
              </div>
            </div>
          </section>

          <section className="mt-6 flex min-h-[65vh] flex-col overflow-hidden rounded-[32px] border border-cyan-400/25 bg-gradient-to-br from-[#05080d]/70 via-[#03050c]/60 to-[#010308]/80 shadow-[0_20px_80px_rgba(0,0,0,0.45)] backdrop-blur-3xl relative">
            <div className="pointer-events-none absolute inset-0 z-0 bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.16),transparent_55%),radial-gradient(circle_at_bottom,rgba(76,215,246,0.08),transparent_60%)]" />
            <div className="relative z-10 border-b border-cyan-400/12 px-5 py-4 md:px-6">
              <div className="text-sm font-semibold text-cyan-100">对话工作台</div>
              <div className="mt-1 text-sm text-cyan-100/52">
                {running ? '后台正在执行隐藏动作并持续回流结果。' : '用一句自然语言描述目标，其他能力都藏在下面。'}
              </div>
            </div>

            <div className="relative z-10 flex-1 overflow-y-auto px-4 py-5 md:px-6">
              {messages.length === 0 ? (
                <div className="flex h-full flex-col items-center justify-center text-center">
                  <div className="max-w-2xl">
                    <div className="text-2xl font-semibold text-cyan-100">从一句自然语言开始</div>
                    <div className="mt-3 text-cyan-100/55">
                      例如：帮我找深圳 AI 产品实习，并开始执行。或者：先看最近投递记录，再帮我调整下一轮策略。
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

            <div className="relative z-10 border-t border-cyan-400/12 px-4 py-4 md:px-6">
              <div className="mb-3 flex flex-wrap items-center gap-2 text-xs text-cyan-100/48">
                <span className="rounded-full border border-cyan-400/12 px-3 py-1">隐藏能力：搜索 / 执行 / Challenge / 表单填充 / 记录</span>
                {resumeReady ? <span className="rounded-full border border-cyan-400/12 px-3 py-1">简历已就绪</span> : null}
                {latestAssistant?.actions?.length ? <span className="rounded-full border border-cyan-400/12 px-3 py-1">已生成动作建议</span> : null}
                {seedPromptPending ? <span className="rounded-full border border-cyan-400/25 bg-cyan-500/8 px-3 py-1 text-cyan-100/90">已接收 seed_prompt，登录后自动发送</span> : null}
              </div>
              <div className="flex items-end gap-3">
                <button className="rounded-full border border-cyan-400/20 px-4 py-3 text-sm text-cyan-100/75 transition hover:bg-cyan-500/10" type="button" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
                  {uploading ? '上传中...' : '上传简历'}
                </button>
                <div className="flex-1 rounded-[28px] border border-cyan-400/18 bg-black/22 px-4 py-3">
                  <textarea
                    className="min-h-[56px] w-full resize-none bg-transparent text-[15px] leading-7 text-cyan-50 outline-none placeholder:text-cyan-100/32"
                    placeholder="例如：帮我找上海 AI 产品实习，先筛岗位，再开始执行。"
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
                  {sending ? '处理中...' : '发送'}
                </button>
              </div>
              <input ref={fileInputRef} type="file" accept=".pdf,.docx,.txt" className="hidden" onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) void uploadResume(file);
                event.currentTarget.value = '';
              }} />
            </div>
          </section>

          <section className="mt-6 space-y-4">
            <div className={infoCardBase}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs uppercase tracking-[0.18em] text-cyan-300/70">对话状态</div>
                  <div className="mt-1 text-xl font-semibold text-white">{stageLabel}</div>
                </div>
                <div className={`flex items-center gap-2 rounded-full border px-3 py-1 text-xs uppercase tracking-[0.2em] ${running ? 'border-emerald-300/60 bg-emerald-500/10 text-emerald-200' : 'border-cyan-400/40 text-cyan-100/70'}`}>
                  <span className={`h-2 w-2 rounded-full ${running ? 'bg-emerald-400' : 'bg-cyan-400/70'}`} />
                  {running ? '运行中' : '空闲'}
                </div>
              </div>
              <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-white/10">
                <div className="h-full rounded-full bg-gradient-to-r from-cyan-400 via-sky-500 to-blue-500" style={{ width: `${statusWidth}%` }} />
              </div>
              <div className="mt-3 flex flex-wrap gap-4 text-sm text-cyan-100/70">
                <div>成功：<span className="font-semibold text-white">{successCount}</span></div>
                <div>失败：<span className="font-semibold text-white">{failedCount}</span></div>
                <div>完成率：<span className="font-semibold text-white">{completionRate}%</span></div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2 text-[11px] uppercase tracking-[0.2em] text-cyan-100/60">
                <span className="rounded-full border border-cyan-400/40 px-3 py-1">{resumeReady ? '简历已就绪' : '等待简历上传'}</span>
                <span className="rounded-full border border-cyan-400/40 px-3 py-1">{session?.id ? `会话 ${session.id.slice(0, 8)}` : '会话未创建'}</span>
              </div>
            </div>

            <div className={infoCardBase}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs uppercase tracking-[0.18em] text-cyan-300/70">接管指引</div>
                  <div className="mt-1 text-lg font-semibold text-white">{guidance.label}</div>
                </div>
                <div className="text-xs uppercase tracking-[0.18em] text-cyan-100/60">{assistedStatus}</div>
              </div>
              <p className="mt-3 text-sm text-cyan-100/70">{guidance.description}</p>
              {guidance.actionLabel ? (
                <div className="mt-4 flex flex-wrap items-center gap-3 text-sm">
                  {guidanceActionLink ? (
                    <a
                      className="rounded-full border border-cyan-400/40 px-4 py-2 text-xs uppercase tracking-[0.2em] text-cyan-100 transition hover:bg-cyan-400/10"
                      href={guidanceActionLink}
                      target={guidanceActionLink.startsWith('http') ? '_blank' : undefined}
                      rel={guidanceActionLink.startsWith('http') ? 'noreferrer' : undefined}
                    >
                      {guidance.actionLabel}
                    </a>
                  ) : (
                    <span className="rounded-full border border-cyan-400/40 px-4 py-2 text-xs uppercase tracking-[0.2em] text-cyan-100/70">
                      {guidance.actionLabel}
                    </span>
                  )}
                  {guidance.actionHint ? <p className="text-xs text-cyan-200/60">{guidance.actionHint}</p> : null}
                </div>
              ) : null}
            </div>

            <div className={infoCardBase}>
              <div className="text-xs uppercase tracking-[0.18em] text-cyan-300/70">动作层</div>
              <div className="mt-3 space-y-2 text-sm text-cyan-100/70">
                {['搜索与来源过滤', '简历分析与改写准备', '自动执行与回流日志', 'Challenge Center / 表单填充'].map((item) => (
                  <div key={item} className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-cyan-300" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className={infoCardBase}>
              <div className="text-xs uppercase tracking-[0.18em] text-cyan-300/70">快捷入口</div>
              <div className="mt-3 flex flex-col gap-2">
                <a className="rounded-full border border-cyan-400/18 px-4 py-2 text-sm text-cyan-100/80 transition hover:bg-cyan-500/10" href="/challenge-center">Challenge Center</a>
                <a className="rounded-full border border-cyan-400/18 px-4 py-2 text-sm text-cyan-100/80 transition hover:bg-cyan-500/10" href="/dashboard">执行看板</a>
                <a className="rounded-full border border-cyan-400/18 px-4 py-2 text-sm text-cyan-100/80 transition hover:bg-cyan-500/10" href="/records">投递记录</a>
              </div>
            </div>
          </section>
        </main>
      </div>

      {showLogin ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-[#020712]/82 px-4 backdrop-blur-xl">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.18),transparent_42%),radial-gradient(circle_at_bottom,rgba(56,189,248,0.1),transparent_35%)]" />
          <div className="relative w-full max-w-md overflow-hidden rounded-[28px] border border-cyan-400/30 bg-[linear-gradient(155deg,rgba(2,6,23,0.96),rgba(5,15,34,0.94))] p-6 shadow-[0_35px_110px_rgba(0,0,0,0.72)]">
            <div className="absolute inset-x-10 top-0 h-px bg-gradient-to-r from-transparent via-cyan-300/70 to-transparent" />
            <div className="flex items-start justify-between gap-4 border-b border-cyan-400/18 pb-4">
              <div>
                <div className="text-[0.65rem] font-semibold uppercase tracking-[0.22em] text-cyan-300">
                  {authMode === 'login' ? 'Authenticate Workspace' : 'Create Workspace Access'}
                </div>
                <div className="mt-2 text-2xl font-semibold text-white">{authMode === 'login' ? '登录工作台' : '注册工作台'}</div>
                <p className="mt-2 text-sm leading-6 text-cyan-100/68">
                  先完成认证，再让控制台接住你的 Prompt、会话和执行链路。
                </p>
              </div>
              {!authLockRequired ? (
                <button
                  className="rounded-full border border-cyan-400/25 px-3 py-1 text-xs uppercase tracking-[0.18em] text-cyan-100/70 transition hover:bg-cyan-400/10"
                  type="button"
                  onClick={() => setShowLogin(false)}
                >
                  关闭
                </button>
              ) : null}
            </div>

            <div className="mt-5 rounded-2xl border border-cyan-400/14 bg-black/18 p-4">
              <Form layout="vertical" onFinish={handleAuth} requiredMark={false}>
                <Form.Item label={<span className="text-cyan-100/85">邮箱</span>} name="email" rules={[{ required: true, message: '请输入邮箱' }]}>
                  <Input style={{ background: 'rgba(8,21,40,0.66)', borderColor: 'rgba(34,211,238,0.35)', color: '#e0f2fe' }} />
                </Form.Item>
                <Form.Item label={<span className="text-cyan-100/85">密码</span>} name="password" rules={[{ required: true, message: '请输入密码' }]}>
                  <Input.Password style={{ background: 'rgba(8,21,40,0.66)', borderColor: 'rgba(34,211,238,0.35)', color: '#e0f2fe' }} />
                </Form.Item>
                {authMode === 'register' ? (
                  <Form.Item label={<span className="text-cyan-100/85">昵称</span>} name="nickname">
                    <Input style={{ background: 'rgba(8,21,40,0.66)', borderColor: 'rgba(34,211,238,0.35)', color: '#e0f2fe' }} />
                  </Form.Item>
                ) : null}
                <button className="mt-2 w-full rounded-full bg-cyan-400 px-4 py-3 font-bold text-[#0d0e13] shadow-[0_0_30px_rgba(34,211,238,0.28)]" type="submit">
                  {authMode === 'login' ? '登录' : '注册'}
                </button>
              </Form>
              {authLockRequired ? <div className="mt-3 text-center text-xs text-cyan-100/65">需要完成认证并建立会话后才能离开这里。</div> : null}
              <button
                className="mt-4 w-full rounded-full border border-cyan-400/18 px-4 py-3 text-sm text-cyan-100/80 transition hover:bg-cyan-500/10"
                type="button"
                onClick={() => setAuthMode((current) => (current === 'login' ? 'register' : 'login'))}
              >
                {authMode === 'login' ? '没有账号，去注册' : '已有账号，去登录'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default AgentChatWorkspace;
