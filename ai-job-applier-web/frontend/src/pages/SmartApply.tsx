import React, { useEffect, useMemo, useState } from 'react';
import { Form, Input, Modal, message } from 'antd';
import { apiUrl, authHeaders, wsUrl } from '../lib/api';
import { assistedGuidance, AssistedStatus, deriveAssistedStatus } from './assistedGuidance';

interface User {
  id: string;
  email?: string;
  nickname?: string;
  plan: string;
  remaining_quota: number;
}

interface ApplyLog {
  job: string;
  company: string;
  greeting: string;
  success: boolean;
}

interface LoginFormValues {
  email: string;
  password: string;
  nickname?: string;
}

interface PasswordFormValues {
  currentPassword?: string;
  nextPassword: string;
  confirmPassword: string;
}

interface ApplyFormValues {
  keyword: string;
  city?: string;
  max_count?: number | string;
}

interface ChatMessage {
  id: string;
  role: 'assistant' | 'user' | 'system';
  text: string;
  tone?: 'info' | 'success' | 'warning';
}

const defaultFeed = [
  {
    id: 'feed-ready',
    title: '等待输入今天这轮目标',
    text: '先把岗位关键词、城市和简历版本给清楚，后面的重写、筛选和执行才不会跑偏。',
    meta: 'READY',
    tone: 'info',
  },
  {
    id: 'feed-source',
    title: '来源判断会被直接回流',
    text: '系统不会堆一大屏无效说明，只回传真正影响你判断的结果。',
    meta: 'SOURCE',
    tone: 'info',
  },
  {
    id: 'feed-handoff',
    title: '验证码会被暴露为接管点',
    text: '阻塞步骤会明确暂停，而不是被伪装成所谓全自动成功。',
    meta: 'HANDOFF',
    tone: 'warning',
  },
] as const;

const planMap: Record<string, string> = {
  free: '免费版',
  basic: '基础版',
  pro: '专业版',
  yearly: '年付版',
};

const planOptions = [
  {
    key: 'basic',
    name: '基础版',
    price: '轻量试用',
    description: '先验证这条链路是否适合你的求职节奏。',
  },
  {
    key: 'pro',
    name: '专业版',
    price: '高频执行',
    description: '适合需要持续重写、批量筛选和高频推进的人。',
    featured: true,
  },
  {
    key: 'yearly',
    name: '年付版',
    price: '长期使用',
    description: '适合确定会把它作为长期工作流的人。',
  },
] as const;

const SmartApply: React.FC = () => {
  const [passwordForm] = Form.useForm<PasswordFormValues>();
  const [token, setToken] = useState('');
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState('');
  const [logs, setLogs] = useState<ApplyLog[]>([]);
  const [stats, setStats] = useState({ success: 0, failed: 0 });
  const [resumeText, setResumeText] = useState('');
  const [keyword, setKeyword] = useState('');
  const [city, setCity] = useState('');
  const [maxCount, setMaxCount] = useState('10');
  const [assistedStatus, setAssistedStatus] = useState<AssistedStatus>('standby');
  const [showLogin, setShowLogin] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showUpgrade, setShowUpgrade] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [passwordSubmitting, setPasswordSubmitting] = useState(false);

  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    if (savedToken) {
      setToken(savedToken);
      void loadUserInfo(savedToken);
      return;
    }
    setShowLogin(true);
  }, []);

  useEffect(() => {
    const topNav = document.getElementById('workspace-top-nav');
    const particles = document.getElementById('workspace-particles');
    const grid = document.getElementById('workspace-interactive-grid');
    const glowOrb1 = document.getElementById('workspace-glow-orb-1');
    const glowOrb2 = document.getElementById('workspace-glow-orb-2');
    const mainHighlight = document.getElementById('workspace-highlight');
    const heroContent = document.getElementById('workspace-hero-content');
    const canvas = document.getElementById('workspace-stellar-canvas') as HTMLCanvasElement | null;

    if (!canvas) {
      return undefined;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) {
      return undefined;
    }

    let width = window.innerWidth;
    let height = window.innerHeight;
    let raf = 0;
    const mouse = { x: -1000, y: -1000 };
    const nodes: Array<{ x: number; y: number; vx: number; vy: number; size: number; opacity: number; glow: number }> = [];
    const particleCount = 720;
    const connectionDistance = 90;
    const forceRadius = 220;

    const resize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width;
      canvas.height = height;
    };

    const seedParticles = () => {
      nodes.length = 0;
      for (let i = 0; i < particleCount; i += 1) {
        nodes.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * 1.05,
          vy: (Math.random() - 0.5) * 1.05,
          size: Math.random() * 1.25 + 0.35,
          opacity: Math.random() * 0.34 + 0.08,
          glow: 0,
        });
      }
    };

    const drawLines = () => {
      for (let i = 0; i < nodes.length; i += 1) {
        const a = nodes[i];
        for (let j = i + 1; j < i + 12 && j < nodes.length; j += 1) {
          const b = nodes[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const d2 = dx * dx + dy * dy;
          if (d2 < connectionDistance * connectionDistance) {
            const d = Math.sqrt(d2);
            const alpha = (1 - d / connectionDistance) * 0.12 + (a.glow + b.glow) * 0.18;
            ctx.beginPath();
            ctx.strokeStyle = `rgba(34, 211, 238, ${Math.min(alpha, 0.35)})`;
            ctx.lineWidth = 0.6;
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
      ctx.fillStyle = 'rgba(13, 14, 19, 0.18)';
      ctx.fillRect(0, 0, width, height);

      for (let i = 0; i < nodes.length; i += 1) {
        const point = nodes[i];
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
          point.x -= Math.cos(angle) * force * 15;
          point.y -= Math.sin(angle) * force * 15;
          point.glow = force * 0.8;
        } else {
          point.glow *= 0.9;
        }

        ctx.beginPath();
        ctx.fillStyle = '#22D3EE';
        ctx.globalAlpha = Math.min(1, point.opacity + point.glow);
        ctx.arc(point.x, point.y, point.size + point.glow * 1.7, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1;
      }

      drawLines();
      raf = window.requestAnimationFrame(animate);
    };

    const handleScroll = () => {
      const scrollPos = window.scrollY;
      const denominator = document.documentElement.scrollHeight - window.innerHeight;
      const scrollPercent = denominator > 0 ? Math.min(scrollPos / denominator, 1) : 0;

      if (topNav) {
        topNav.classList.toggle('nav-scrolled', scrollPos > 50);
      }

      const hueRotate = scrollPercent * 48;
      if (particles) particles.style.filter = `hue-rotate(${hueRotate}deg)`;
      if (glowOrb1) glowOrb1.style.filter = `hue-rotate(${hueRotate}deg)`;
      if (glowOrb2) glowOrb2.style.filter = `hue-rotate(${hueRotate}deg)`;
      if (grid) {
        const gx = (mouse.x / Math.max(width, 1)) * 20 - 10;
        const gy = (mouse.y / Math.max(height, 1)) * 20 - 10;
        grid.style.transform = `translate(${gx}px, ${gy}px)`;
      }

      if (mainHighlight) {
        if (scrollPercent > 0.1) {
          mainHighlight.style.textShadow = '0 0 10px rgba(109, 59, 215, 0.8), 0 0 20px rgba(109, 59, 215, 0.4)';
          mainHighlight.style.color = '#c0c1ff';
        } else {
          mainHighlight.style.textShadow = '';
          mainHighlight.style.color = '';
        }
      }

      if (heroContent) {
        heroContent.style.transform = `translateY(${scrollPos * 0.18}px)`;
      }
    };

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('active');
          }
        });
      },
      {
        threshold: 0.12,
        rootMargin: '0px 0px -40px 0px',
      },
    );

    document.querySelectorAll('.reveal').forEach((element) => observer.observe(element));
    resize();
    seedParticles();
    animate();
    window.addEventListener('scroll', handleScroll);
    window.addEventListener('resize', resize);
    window.addEventListener('mousemove', onPointer);
    handleScroll();

    return () => {
      observer.disconnect();
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', onPointer);
      window.cancelAnimationFrame(raf);
    };
  }, []);

  const scrollToExecution = () => {
    document.getElementById('workspace-execution')?.scrollIntoView({
      behavior: 'smooth',
      block: 'start',
    });
  };

  const loadUserInfo = async (authToken: string) => {
    try {
      const response = await fetch(apiUrl('/api/user/info'), {
        headers: authHeaders({ Authorization: `Bearer ${authToken}` }),
      });
      const data = await response.json();
      if (data.success) {
        setUser(data.user);
      }
    } catch (error) {
      console.error('获取用户信息失败', error);
    }
  };

  const handleLogin = async (values: LoginFormValues) => {
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

      const data = await response.json();
      if (data.success) {
        setToken(data.token);
        localStorage.setItem('token', data.token);
        setUser(data.user);
        setShowLogin(false);
        setAuthMode('login');
        message.success(authMode === 'login' ? '登录成功' : '注册成功');
        return;
      }

      message.error(data.detail || data.message || '登录失败');
    } catch (error) {
      message.error('登录失败，请重试');
    }
  };

  const handleUpgrade = async (plan: string) => {
    try {
      const response = await fetch(apiUrl('/api/user/upgrade'), {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ plan }),
      });
      const data = await response.json();
      if (data.success) {
        setUser(data.user);
        setShowUpgrade(false);
        message.success(data.message || '方案已更新');
        return;
      }

      message.error(data.detail || data.message || '方案更新失败');
    } catch (error) {
      message.error('方案更新失败');
    }
  };
  const closePasswordModal = () => {
    setShowPassword(false);
    passwordForm.resetFields();
  };

  const handlePasswordChange = async (values: PasswordFormValues) => {
    if (!user?.email) {
      message.error('当前账号没有可用邮箱，无法修改密码');
      return;
    }

    setPasswordSubmitting(true);
    try {
      if (values.currentPassword === values.nextPassword) {
        message.warning('新密码不能与旧密码相同');
        return;
      }

      const response = await fetch(apiUrl('/api/auth/change-password'), {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({
          current_password: values.currentPassword || '',
          new_password: values.nextPassword,
        }),
      });
      const data = await response.json();
      if (data.success) {
        message.success(data.message || '密码已更新');
        closePasswordModal();
        return;
      }
      message.error(data.detail || data.message || '修改密码失败');
    } catch (error) {
      message.error('修改密码失败，请重试');
    } finally {
      setPasswordSubmitting(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken('');
    setUser(null);
    setShowLogin(true);
    message.success('已退出登录');
  };

  const onSubmit = async (values: ApplyFormValues) => {
    if (!user) {
      setShowLogin(true);
      return;
    }

    if (!resumeText.trim()) {
      message.warning('先补充简历内容');
      return;
    }

    setLoading(true);
    setProgress(0);
    setStage('');
    setLogs([]);
    setStats({ success: 0, failed: 0 });
    setAssistedStatus('standby');

    try {
      const ws = new WebSocket(wsUrl('/api/apply/ws'));

      ws.onopen = () => {
        ws.send(
          JSON.stringify({
            token,
            keyword: values.keyword,
            city: values.city || '全国',
            max_count: Number(values.max_count) || 10,
            resume_text: resumeText,
          }),
        );
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const nextStatus = deriveAssistedStatus({
          assisted_status: data.assisted_status,
          stage: data.stage,
        });
        setAssistedStatus(nextStatus);

        if (data.error) {
          message.error(data.message || '执行失败');
          setLoading(false);
          setAssistedStatus('failed');
          ws.close();
          return;
        }

        if (data.stage) {
          setStage(data.message || data.stage);
          setProgress(Math.round((data.progress || 0) * 100));
        }

        if (typeof data.success_count === 'number' || typeof data.failed_count === 'number') {
          setStats((current) => ({
            success: typeof data.success_count === 'number' ? data.success_count : current.success,
            failed: typeof data.failed_count === 'number' ? data.failed_count : current.failed,
          }));
        }

        if (typeof data.remaining_quota === 'number') {
          setUser((current) => (current ? { ...current, remaining_quota: data.remaining_quota } : current));
        }

        if (data.job) {
          setLogs((prev) => [
            ...prev,
            {
              job: data.job,
              company: data.company,
              greeting: data.greeting,
              success: Boolean(data.success),
            },
          ]);
        }

        if (data.stage === 'completed') {
          setLoading(false);
          setAssistedStatus('resumed');
          message.success(data.message || '执行完成');
          ws.close();
        }
      };

      ws.onerror = () => {
        setLoading(false);
        setAssistedStatus('failed');
        message.error('连接异常');
      };

      ws.onclose = () => {
        setLoading(false);
      };
    } catch (error) {
      setLoading(false);
      setAssistedStatus('failed');
      message.error('执行失败');
    }
  };

  const handleExecutionSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void onSubmit({ keyword, city, max_count: maxCount });
  };

  const feedItems = useMemo(() => {
    if (logs.length === 0) {
      return defaultFeed;
    }

    return logs.map((log, index) => ({
      id: `${log.company}-${log.job}-${index}`,
      title: `${log.company} · ${log.job}`,
      text: log.greeting,
      meta: log.success ? 'SUCCESS' : 'WARNING',
      tone: log.success ? 'success' : 'warning',
    }));
  }, [logs]);

  const assistance = assistedGuidance[assistedStatus];
  const latestLog = logs.length ? logs[logs.length - 1] : null;
  const completionRate = logs.length ? Math.round((stats.success / logs.length) * 100) : 0;
  const stageLabel = stage || (loading ? '执行链路正在推进' : '等待启动');
  const accountName = user?.nickname || user?.email || 'Guest';
  const accountInitial = accountName.slice(0, 1).toUpperCase();

  const insightCards = [
    {
      title: '当前阶段',
      value: stageLabel,
      detail: '执行状态实时回流',
      icon: 'deployed_code',
    },
    {
      title: '剩余额度',
      value: user ? `${user.remaining_quota} 次` : '--',
      detail: user ? `${planMap[user.plan] || user.plan}` : '登录后可见',
      icon: 'bolt',
    },
    {
      title: '本轮完成率',
      value: `${completionRate}%`,
      detail: `成功 ${stats.success} / 失败 ${stats.failed}`,
      icon: 'monitoring',
    },
  ];

  const [chatDraft, setChatDraft] = useState('');
  const [toolPanelOpen, setToolPanelOpen] = useState(false);
  const [userMessages, setUserMessages] = useState<ChatMessage[]>([]);

  const formatRoleLabel = (role: ChatMessage['role']) => {
    if (role === 'user') return 'YOU';
    if (role === 'assistant') return 'AGENT';
    return 'SYSTEM';
  };

  const conversationEntries = useMemo<ChatMessage[]>(() => {
    const assistantHistory = feedItems.map((item) => ({
      id: item.id,
      role: 'assistant' as const,
      text: `${item.meta}: ${item.title} · ${item.text}`,
      tone: item.tone,
    }));
    const logHistory = logs.map((log, index) => ({
      id: `${log.company}-${log.job}-${index}-${log.success}`,
      role: 'assistant' as const,
      text: `${log.company} · ${log.job} · ${log.greeting}`,
      tone: log.success ? 'success' : 'warning',
    }));
    const systemMessage: ChatMessage = {
      id: 'system-status',
      role: 'system',
      text: `阶段: ${stageLabel} · ${assistance.label}`,
    };
    return [...assistantHistory, ...logHistory, systemMessage, ...userMessages];
  }, [feedItems, logs, stageLabel, assistance.label, userMessages]);

  const handleConversationSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = chatDraft.trim();
    if (!trimmed) {
      return;
    }
    setUserMessages((current) => [
      ...current,
      {
        id: `user-${Date.now()}`,
        role: 'user',
        text: trimmed,
      },
    ]);
    setChatDraft('');
    setToolPanelOpen(true);
    scrollToExecution();
  };

  return (
    <div className="font-body text-cyan-100 selection:bg-cyan-500/30">
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="grid-overlay" id="workspace-interactive-grid" />
        <div className="absolute -top-1/4 -left-1/4 w-[80vw] h-[80vw] glow-radial opacity-60" />
        <div className="absolute -bottom-1/4 -right-1/4 w-[70vw] h-[70vw] glow-cyan opacity-40" />
        <div className="particle-bg absolute inset-0 opacity-40" id="workspace-particles" />
        <canvas id="workspace-stellar-canvas" />
      </div>

      <main className="relative z-10">
      <nav className="fixed top-0 z-50 w-full border-b border-transparent bg-transparent transition-all duration-500" id="workspace-top-nav">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-8 py-4">
          <a className="font-headline text-2xl font-bold tracking-tighter text-[#D0BCFF] drop-shadow-[0_0_8px_rgba(208,188,255,0.5)]" href="/">
            AgentHelpJob
          </a>
          <div className="hidden items-center gap-8 md:flex">
            <a className="border-b-2 border-[#4CD7F6] pb-1 font-headline tracking-tighter text-[#4CD7F6]" href="#workspace-hero">工作台</a>
            <a className="font-headline tracking-tighter text-cyan-100/70 transition-colors hover:text-cyan-200" href="#workspace-execution">执行区</a>
            <a className="font-headline tracking-tighter text-cyan-100/70 transition-colors hover:text-cyan-200" href="#workspace-logs">回流日志</a>
            <a className="font-headline tracking-tighter text-cyan-100/70 transition-colors hover:text-cyan-200" href="/challenge-center">Challenge Center</a>
            <a className="font-headline tracking-tighter text-cyan-100/70 transition-colors hover:text-cyan-200" href="#workspace-account">账号</a>
          </div>
          {user ? (
            <button className="rounded-full bg-cyan-400 px-6 py-2 font-bold text-[#0d0e13] shadow-[0_0_20px_rgba(34,211,238,0.35)] transition-all duration-300 ease-out hover:scale-[1.02]" type="button" onClick={handleLogout}>
              退出
            </button>
          ) : (
            <button className="rounded-full bg-cyan-400 px-6 py-2 font-bold text-[#0d0e13] shadow-[0_0_20px_rgba(34,211,238,0.35)] transition-all duration-300 ease-out hover:scale-[1.02]" type="button" onClick={() => setShowLogin(true)}>
              登录
            </button>
          )}
        </div>
      </nav>

      <header className="relative flex min-h-[90vh] flex-col items-center justify-center overflow-hidden px-6 pt-20 pb-32" id="workspace-hero">
        <div className="absolute inset-0 z-0 bg-gradient-to-b from-transparent via-[#0d0e13]/50 to-[#0d0e13]" />
        <div className="absolute top-1/4 -left-20 h-96 w-96 rounded-full bg-cyan-400/12 blur-[120px] transition-all duration-1000" id="workspace-glow-orb-1" />
        <div className="absolute bottom-1/4 -right-20 h-[500px] w-[500px] rounded-full bg-cyan-400/5 blur-[150px] transition-all duration-1000" id="workspace-glow-orb-2" />
        <div className="parallax-target relative z-10 mx-auto max-w-5xl text-center" id="workspace-hero-content">
          <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-cyan-400/40 bg-cyan-500/10 px-3 py-1">
            <span className="h-2 w-2 animate-pulse rounded-full bg-cyan-300 shadow-[0_0_8px_#4CD7F6]" />
            <span className="font-label text-[0.6875rem] uppercase tracking-[0.2em] text-cyan-300">Workspace Status: Active // APPLY_READY</span>
          </div>
          <h1 className="mb-8 font-headline text-5xl font-bold tracking-tighter leading-tight text-glow bg-clip-text text-transparent bg-gradient-to-b from-white to-cyan-300 md:text-8xl">
            让 <span className="italic text-cyan-200" id="workspace-highlight">执行流</span>
            <br />
            接管重复投递
          </h1>
          <p className="mx-auto max-w-3xl text-xl md:text-2xl text-cyan-50/80 font-light tracking-wide terminal-glow">
            真实岗位、定制简历、本机投递、回流日志和人工接管，都在这一块工作台里推进。
          </p>

          <div className="w-full max-w-3xl px-4 mt-12 mx-auto">
            <div className="glass-panel p-6 rounded-xl border border-cyan-300/40 shadow-[0_0_50px_rgba(34,211,238,0.2)] relative group text-left">
              <div className="absolute -top-3 left-6 px-3 bg-[#0d0e13] text-[0.6rem] font-mono tracking-widest text-cyan-300 border border-cyan-300/40 rounded uppercase">
                Execution_Prompt::Terminal
              </div>
              <div className="flex items-center gap-4">
                <span className="material-symbols-outlined text-cyan-300 text-2xl">terminal</span>
                <div className="flex-1 font-mono text-lg text-cyan-100 border-r-2 border-cyan-400 pr-1 w-fit cursor-blink">
                  {keyword || '正在准备今天这轮执行任务...'}
                </div>
              </div>
              <div className="mt-4 flex justify-between items-center text-[0.65rem] font-mono text-cyan-200/50 uppercase tracking-tighter">
                <span>{loading ? 'AI agent is executing...' : 'Shift + Enter to Execute'}</span>
                <span>{assistance.label}</span>
              </div>
            </div>
            <div className="mt-8 flex justify-center gap-4 flex-col sm:flex-row">
              <button className="bg-cyan-400 text-slate-950 font-bold px-10 py-4 rounded-full shadow-[0_0_30px_rgba(34,211,238,0.4)] hover:shadow-[0_0_50px_rgba(34,211,238,0.6)] transition-all transform hover:-translate-y-1 btn-glow" type="button" onClick={user ? scrollToExecution : () => setShowLogin(true)}>
                {user ? '开启这一轮执行' : '登录并开启'}
              </button>
              <button className="glass-panel px-10 py-4 rounded-full text-cyan-200 font-medium border border-cyan-400/30 hover:bg-cyan-400/10 transition-all" type="button" onClick={() => document.getElementById('workspace-logs')?.scrollIntoView({ behavior: 'smooth' })}>
                查看 AI 执行记录
              </button>
              <button className="glass-panel px-10 py-4 rounded-full text-cyan-200 font-medium border border-cyan-400/30 hover:bg-cyan-400/10 transition-all" type="button" onClick={() => { const qs = new URLSearchParams({ provider: 'boss', autostart: '1', keyword: keyword || 'python', city: city || '全国', max_count: maxCount || '10' }); const lastBossSessionId = window.localStorage.getItem('last_boss_session_id') || ''; if (lastBossSessionId) qs.set('session_id', lastBossSessionId); window.location.href = `/challenge-center?${qs.toString()}`; }}>
                前往 Challenge Center
              </button>
            </div>
          </div>
        </div>
      </header>
      <section className="template-section-anchor reveal mx-auto max-w-7xl px-8 py-24" id="workspace-execution">
        <div className="mb-16 flex flex-col items-end justify-between gap-4 md:flex-row">
          <div>
            <span className="mb-2 block font-label text-sm uppercase tracking-widest text-cyan-300">Execution</span>
            <h2 className="font-headline text-4xl font-bold tracking-tight text-cyan-100">执行输入与当前状态</h2>
          </div>
          <div className="max-w-xs text-right font-light text-cyan-100/70">
            一次把目标、边界和简历内容讲清楚，后面的重写、来源校验和投递才不会持续跑偏。
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-12">
          <div className="glass-panel relative overflow-hidden rounded-full p-8 md:col-span-8">
            <div className="absolute top-0 right-0 h-64 w-64 rounded-full bg-cyan-400/12 blur-3xl" />
            <div className="relative">
              <div className="mb-6">
                <span className="material-symbols-outlined mb-4 text-4xl text-cyan-300">search_spark</span>
                <h3 className="mb-4 font-headline text-3xl font-bold text-cyan-100">发起一轮执行</h3>
                <p className="max-w-2xl text-cyan-100/70">
                  输入岗位关键词、城市边界和简历内容。系统会先重写、再筛来源、再推进本机执行，必要时把你拉到人工接管点。
                </p>
              </div>

              <form className="space-y-5" onSubmit={handleExecutionSubmit}>
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  <label className="block">
                    <span className="mb-2 block text-sm font-medium text-cyan-100">目标岗位关键词</span>
                    <input className="w-full rounded-xl border border-cyan-400/30 bg-black/30 px-4 py-3 text-cyan-100 outline-none transition focus:border-cyan-300" placeholder="例如：AI 产品经理 / Python 后端 / 增长分析" value={keyword} onChange={(event) => setKeyword(event.target.value)} />
                  </label>
                  <label className="block">
                    <span className="mb-2 block text-sm font-medium text-cyan-100">城市</span>
                    <input className="w-full rounded-xl border border-cyan-400/30 bg-black/30 px-4 py-3 text-cyan-100 outline-none transition focus:border-cyan-300" placeholder="例如：上海、深圳、杭州、全国" value={city} onChange={(event) => setCity(event.target.value)} />
                  </label>
                </div>

                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-cyan-100">最大投递数</span>
                  <input className="w-full rounded-xl border border-cyan-400/30 bg-black/30 px-4 py-3 text-cyan-100 outline-none transition focus:border-cyan-300" type="number" min="1" max="50" value={maxCount} onChange={(event) => setMaxCount(event.target.value)} />
                </label>

                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-cyan-100">简历内容</span>
                  <textarea className="min-h-[220px] w-full rounded-2xl border border-cyan-400/30 bg-black/30 px-4 py-4 text-cyan-100 outline-none transition focus:border-cyan-300" placeholder="粘贴本轮执行使用的简历内容。经历、技能、项目与行业越清楚，生成结果越有针对性。" value={resumeText} onChange={(event) => setResumeText(event.target.value)} />
                </label>

                <div className="flex flex-col items-start justify-between gap-4 border-t border-cyan-400/20 pt-4 md:flex-row md:items-center">
                  <p className="max-w-xl text-sm text-cyan-100/70">验证码、身份确认或异常阻塞会被直接暴露为人工接管点，不会被伪装成“已经自动完成”。</p>
                  <button className="rounded-xl bg-gradient-to-r from-cyan-400 to-cyan-300 px-10 py-4 font-bold text-[#0d0e13] shadow-[0_20px_40px_rgba(34,211,238,0.22)] transition-all hover:scale-105 disabled:cursor-not-allowed disabled:opacity-60" type="submit" disabled={loading}>
                    {loading ? '执行中...' : '开始执行'}
                  </button>
                </div>
              </form>
            </div>
          </div>

          <div className="glass-panel rounded-full p-8 md:col-span-4" id="workspace-account">
            <div className="mb-6 flex items-start justify-between gap-4">
              <div>
                <span className="mb-2 block font-label text-sm uppercase tracking-widest text-cyan-300">Account</span>
                <h3 className="font-headline text-2xl font-bold text-cyan-100">{user ? '账号已接入' : '账号未接入'}</h3>
              </div>
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-400/20 text-xl font-bold text-cyan-200">{accountInitial}</div>
            </div>
            <div className="mb-6 text-cyan-100/70">
              <div className="mb-1 text-lg font-semibold text-cyan-100">{accountName}</div>
              <div>{user?.email || '登录后同步账号与套餐状态'}</div>
            </div>

            <div className="space-y-4">
              <div className="rounded-2xl bg-black/30 p-4"><div className="mb-1 text-xs uppercase tracking-widest text-cyan-100/70">当前方案</div><div className="text-lg font-bold text-cyan-100">{user ? planMap[user.plan] || user.plan : '未登录'}</div></div>
              <div className="rounded-2xl bg-black/30 p-4"><div className="mb-1 text-xs uppercase tracking-widest text-cyan-100/70">剩余额度</div><div className="text-lg font-bold text-cyan-300">{user ? `${user.remaining_quota} 次` : '--'}</div></div>
              <div className="rounded-2xl bg-black/30 p-4"><div className="mb-1 text-xs uppercase tracking-widest text-cyan-100/70">人工接管</div><div className="text-lg font-bold text-cyan-100">{assistance.label}</div></div>
            </div>

            <div className="mt-6 flex flex-col gap-3">
              {user ? (
                <>
                  <button className="rounded-xl bg-cyan-400 px-5 py-3 text-sm font-bold text-[#0d0e13] transition hover:scale-[1.01]" type="button" onClick={() => setShowPassword(true)}>修改密码</button>
                  <button className="glass-panel rounded-xl px-5 py-3 text-sm font-medium text-cyan-300" type="button" onClick={() => setShowUpgrade(true)}>查看方案</button>
                </>
              ) : (
                <>
                  <button className="rounded-xl bg-cyan-400 px-5 py-3 text-sm font-bold text-[#0d0e13] transition hover:scale-[1.01]" type="button" onClick={() => setShowLogin(true)}>登录账号</button>
                  <button className="glass-panel rounded-xl px-5 py-3 text-sm font-medium text-cyan-300" type="button" onClick={scrollToExecution}>查看执行区</button>
                </>
              )}
            </div>
          </div>

          {insightCards.map((card) => (
            <div className="rounded-full border border-transparent bg-black/30 p-8 transition-all hover:border-cyan-400/30 md:col-span-4" key={card.title}>
              <span className="material-symbols-outlined mb-4 text-cyan-300">{card.icon}</span>
              <h4 className="mb-2 font-headline text-xl font-bold text-cyan-100">{card.title}</h4>
              <div className="mb-2 text-2xl font-bold text-cyan-100">{card.value}</div>
              <p className="text-sm text-cyan-100/70">{card.detail}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-8 py-32 template-section-anchor reveal" id="workspace-logs">
        <div className="bg-[#000000] border border-cyan-400/30 rounded-xl overflow-hidden shadow-2xl relative shadow-[0_0_30px_rgba(34,211,238,0.15)]">
          <div className="bg-cyan-900/40 px-6 py-3 border-b border-cyan-400/30 flex items-center justify-between">
            <div className="flex space-x-2">
              <div className="w-3 h-3 rounded-full bg-red-500/60"></div>
              <div className="w-3 h-3 rounded-full bg-yellow-500/60"></div>
              <div className="w-3 h-3 rounded-full bg-green-500/60"></div>
            </div>
            <div className="text-[0.65rem] font-mono tracking-widest text-cyan-300 uppercase">
              WORKSPACE_CORE::EXECUTION_STREAM_V4.0
            </div>
            <div className="flex items-center space-x-2">
              <span className="material-symbols-outlined text-[1rem] text-cyan-300">terminal</span>
            </div>
          </div>

          <div className="p-8 font-mono text-sm leading-relaxed h-80 overflow-y-auto custom-scrollbar terminal-content bg-black/40 terminal-glow">
            <div className="space-y-2">
              {feedItems.map((item, index) => (
                <div className="flex space-x-3 tracking-tight" key={item.id}>
                  <span className="text-cyan-900/60 font-mono">[{`${String(index + 1).padStart(2, '0')}:${String(index + 3).padStart(2, '0')}:${String(index + 7).padStart(2, '0')}`}]</span>
                  <span className={`font-mono ${item.tone === 'success' ? 'text-cyan-300' : item.tone === 'warning' ? 'text-cyan-200' : 'text-[#4CD7F6]'}`}>
                    {item.meta}: {item.title} :: {item.text}
                  </span>
                </div>
              ))}
              <div className="flex space-x-3 tracking-tight">
                <span className="text-cyan-900/60 font-mono">[RT:LIVE]</span>
                <span className="text-[#4CD7F6] font-mono">
                  STAGE: {stageLabel} :: ASSISTED: {assistance.label} :: QUOTA: {user ? user.remaining_quota : '--'}
                </span>
              </div>
              <div className="text-cyan-300 mt-4 animate-pulse">_</div>
            </div>
          </div>
        </div>
      </section>

      <section className="relative py-32 reveal">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <h2 className="mb-10 font-headline text-4xl font-bold leading-tight text-cyan-100 md:text-6xl">
            把重复劳动交给系统
            <br />
            把判断力留给 <span className="text-cyan-300 neon-glow-cyan">你自己</span>
          </h2>
          <div className="flex justify-center">
            <button className="rounded-full bg-cyan-400 px-12 py-5 text-xl font-bold text-[#0d0e13] shadow-[0_20px_40px_rgba(34,211,238,0.25)] transition-transform hover:scale-105" type="button" onClick={user ? scrollToExecution : () => setShowLogin(true)}>
              {user ? '继续今天这轮执行' : '登录进入工作台'}
            </button>
          </div>
          <p className="mt-8 font-label text-xs uppercase tracking-widest text-cyan-100/60">LOCAL EXECUTION · VERIFIED SOURCES · HUMAN CHECKPOINTS</p>
        </div>
      </section>

      <footer className="w-full border-t border-[#34343A]/30 bg-[#0D0E13] py-12">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-6 px-12 md:flex-row">
          <div className="font-headline text-lg font-bold text-[#D0BCFF]">AgentHelpJob</div>
          <div className="font-body text-xs uppercase tracking-widest text-cyan-100/60">© 2026 AgentHelpJob. Cinematic AI Workspace for Job Execution.</div>
          <div className="flex gap-8">
            <a className="font-body text-xs uppercase tracking-widest text-cyan-100/60 transition-colors hover:text-[#4CD7F6]" href="/">首页</a>
            <a className="font-body text-xs uppercase tracking-widest text-cyan-100/60 transition-colors hover:text-[#4CD7F6]" href="#workspace-execution">执行区</a>
            <a className="font-body text-xs uppercase tracking-widest text-cyan-100/60 transition-colors hover:text-[#4CD7F6]" href="#workspace-logs">日志</a>
          </div>
        </div>
      </footer>
      </main>
      <Modal
        title={authMode === 'login' ? '登录工作台' : '创建本地账号'}
        open={showLogin}
        footer={null}
        onCancel={() => {
          setShowLogin(false);
          setAuthMode('login');
        }}
      >
        <Form onFinish={handleLogin} layout="vertical">
          <Form.Item label="邮箱" name="email" rules={[{ required: true, message: '请输入邮箱' }, { type: 'email', message: '请输入有效邮箱' }]}>
            <Input placeholder="请输入常用邮箱" size="large" />
          </Form.Item>
          {authMode === 'register' ? (
            <Form.Item label="昵称" name="nickname">
              <Input placeholder="可选，不填则默认使用邮箱前缀" size="large" />
            </Form.Item>
          ) : null}
          <Form.Item label="密码" name="password" rules={[{ required: true, message: '请输入密码' }, { min: 8, message: '密码至少 8 位' }]}>
            <Input.Password placeholder="请输入至少 8 位密码" size="large" />
          </Form.Item>
          <Form.Item>
            <button className="w-full rounded-xl bg-cyan-400 px-5 py-3 font-bold text-[#0d0e13] transition hover:scale-[1.01]" type="submit">
              {authMode === 'login' ? '登录' : '注册'}
            </button>
          </Form.Item>
          <button className="w-full rounded-xl border border-cyan-400/30 bg-black/30 px-5 py-3 text-sm text-cyan-200 transition" type="button" onClick={() => setAuthMode((current) => (current === 'login' ? 'register' : 'login'))}>
            {authMode === 'login' ? '没有账号？去注册' : '已有账号？去登录'}
          </button>
        </Form>
      </Modal>

      <Modal title="修改密码" open={showPassword} footer={null} onCancel={closePasswordModal}>
        {user?.email ? (
          <Form form={passwordForm} onFinish={handlePasswordChange} layout="vertical">
            <p className="mb-4 text-sm text-cyan-100/70">如果这是历史无密码账号，可以直接设置新密码；如果已经设置过本地密码，需要先输入旧密码。</p>
            <Form.Item label="当前邮箱">
              <Input value={user.email} disabled size="large" />
            </Form.Item>
            <Form.Item label="旧密码" name="currentPassword">
              <Input.Password placeholder="如果已有密码，请先输入旧密码" size="large" />
            </Form.Item>
            <Form.Item label="新密码" name="nextPassword" rules={[{ required: true, message: '请输入新密码' }, { min: 8, message: '密码至少 8 位' }]}>
              <Input.Password placeholder="请输入至少 8 位新密码" size="large" />
            </Form.Item>
            <Form.Item
              label="确认新密码"
              name="confirmPassword"
              dependencies={['nextPassword']}
              rules={[
                { required: true, message: '请再次输入新密码' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('nextPassword') === value) {
                      return Promise.resolve();
                    }
                    return Promise.reject(new Error('两次输入的新密码不一致'));
                  },
                }),
              ]}
            >
              <Input.Password placeholder="请再次输入新密码" size="large" />
            </Form.Item>
            <Form.Item>
              <button className="w-full rounded-xl bg-cyan-400 px-5 py-3 font-bold text-[#0d0e13] transition hover:scale-[1.01]" type="submit" disabled={passwordSubmitting}>
                {passwordSubmitting ? '提交中...' : '提交修改'}
              </button>
            </Form.Item>
          </Form>
        ) : (
          <>
            <p className="mb-4 text-sm text-cyan-100/70">当前账号没有邮箱，无法修改本地密码。</p>
            <button className="w-full rounded-xl bg-cyan-400 px-5 py-3 font-bold text-[#0d0e13] transition hover:scale-[1.01]" type="button" onClick={closePasswordModal}>
              关闭
            </button>
          </>
        )}
      </Modal>

      <Modal title="方案列表" open={showUpgrade} footer={null} onCancel={() => setShowUpgrade(false)}>
        <div className="grid gap-4">
          {planOptions.map((plan) => (
            <article className={`rounded-2xl border p-5 ${plan.featured ? 'border-cyan-400/30 bg-cyan-400/12' : 'border-cyan-400/30 bg-black/30'}`} key={plan.key}>
              <strong className="mb-1 block text-lg text-cyan-100">{plan.name}</strong>
              <span className="mb-2 block text-sm uppercase tracking-widest text-cyan-300">{plan.price}</span>
              <p className="mb-4 text-sm text-cyan-100/70">{plan.description}</p>
              <button className="rounded-xl bg-cyan-400 px-4 py-2 text-sm font-bold text-[#0d0e13] transition hover:scale-[1.01]" type="button" onClick={() => handleUpgrade(plan.key)}>
                选择方案
              </button>
            </article>
          ))}
        </div>
      </Modal>
    </div>
  );
};

export default SmartApply;


