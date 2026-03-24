import React, { useEffect } from 'react';

const showcaseCards = [
  {
    icon: 'rocket_launch',
    title: '海量大厂实习一键触达',
    text: '直连字节、腾讯、阿里、美团等主流大厂招聘入口，持续发现高匹配实习岗位。',
  },
  {
    icon: 'explore',
    title: 'AI 面试实时助攻',
    text: '围绕目标岗位给出追问思路与表达建议，让你在真实面试里保持稳定输出。',
  },
  {
    icon: 'description',
    title: '自动化网申执行引擎',
    text: '按 JD 自动重写简历与自荐内容，并推进投递动作，减少机械重复劳动。',
  },
];

const footerColumns = [
  {
    title: '产品',
    links: ['核心看板', 'AI 引擎', '价格计划'],
  },
  {
    title: '资源',
    links: ['开发文档', 'API 状态', '社群'],
  },
  {
    title: '法律',
    links: ['隐私协议', '服务条款'],
  },
];

const typingPhrases = [
  '正在寻找字节跳动的暑期产品实习生岗位...',
  '正在寻找腾讯的日常实习岗位...',
  '正在优化你的求职简历...',
  '正在生成大厂面试真题...',
];

const terminalTemplates = [
  'INFO: 正在全域扫描 字节跳动、腾讯、阿里 2026 春招实习岗位...',
  'MATCH: 发现高匹配机会 @ByteDance - 商业化产品经理 - 匹配度 98%',
  'EXEC: 正在根据 JD 实时重构简历画像，对齐核心竞争力...',
  'SUCCESS: 已成功投递至 12 个内推加密通道...',
  'MONITOR: 正在实时监控面试邀请信号...',
  'STATUS: AI 智能管家已就绪，等待下一步指令...',
];

const LandingPage: React.FC = () => {
  useEffect(() => {
    const canvas = document.getElementById('stellar-canvas') as HTMLCanvasElement | null;
    const grid = document.getElementById('interactive-grid');
    const topNav = document.getElementById('top-nav');
    const typewriterTarget = document.getElementById('typewriter-target');
    const terminalContainer = document.getElementById('terminal-typewriter-container');
    const terminalCursor = document.getElementById('terminal-cursor');
    const terminalWrapper = terminalContainer?.parentElement ?? null;

    if (!canvas || !typewriterTarget || !terminalContainer || !terminalCursor || !terminalWrapper) {
      return;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = window.innerWidth;
    let height = window.innerHeight;
    let raf = 0;
    let disposed = false;

    const timeoutIds: number[] = [];
    const schedule = (fn: () => void, ms: number) => {
      const id = window.setTimeout(() => {
        if (!disposed) fn();
      }, ms);
      timeoutIds.push(id);
    };

    const mouse = { x: -1000, y: -1000 };
    const particleCount = 1000;
    const connectionDistance = 100;
    const forceRadius = 200;
    const repulsionStrength = 15;

    type Particle = {
      x: number;
      y: number;
      vx: number;
      vy: number;
      size: number;
      opacity: number;
      glow: number;
      baseColor: string;
    };

    const particles: Particle[] = [];

    const resize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width;
      canvas.height = height;
    };

    const initParticles = () => {
      particles.length = 0;
      for (let i = 0; i < particleCount; i += 1) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * 1.2,
          vy: (Math.random() - 0.5) * 1.2,
          size: Math.random() * 1.5 + 0.5,
          baseColor: Math.random() > 0.5 ? '#22D3EE' : '#06B6D4',
          opacity: Math.random() * 0.4 + 0.1,
          glow: 0,
        });
      }
    };

    const onPointer = (e: MouseEvent) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    };

    const onScroll = () => {
      if (topNav) {
        topNav.classList.toggle('nav-scrolled', window.scrollY > 50);
      }
    };

    const drawLines = () => {
      const stride = 2;
      for (let i = 0; i < particles.length; i += stride) {
        for (let j = i + 1; j < i + 10 && j < particles.length; j += 1) {
          const p1 = particles[i];
          const p2 = particles[j];
          const dx = p1.x - p2.x;
          const dy = p1.y - p2.y;
          const distSq = dx * dx + dy * dy;

          if (distSq < connectionDistance * connectionDistance) {
            const dist = Math.sqrt(distSq);
            const opacity = (1 - dist / connectionDistance) * 0.15;
            const combinedGlow = (p1.glow + p2.glow) * 0.5;

            ctx.beginPath();
            ctx.strokeStyle = `rgba(34, 211, 238, ${opacity + combinedGlow * 0.4})`;
            ctx.lineWidth = 0.5;
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        }
      }
    };

    const animate = () => {
      if (disposed) return;
      ctx.fillStyle = 'rgba(13, 14, 19, 0.2)';
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
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < forceRadius) {
          const force = (forceRadius - distance) / forceRadius;
          const angle = Math.atan2(dy, dx);
          p.x -= Math.cos(angle) * force * repulsionStrength;
          p.y -= Math.sin(angle) * force * repulsionStrength;
          p.glow = force * 0.8;
        } else {
          p.glow *= 0.9;
        }

        const currentOpacity = Math.min(1, p.opacity + p.glow);
        ctx.beginPath();
        ctx.fillStyle = p.baseColor;
        ctx.globalAlpha = currentOpacity;
        ctx.arc(p.x, p.y, p.size + p.glow * 2, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1;
      }

      drawLines();

      const gridX = (mouse.x / Math.max(width, 1)) * 20 - 10;
      const gridY = (mouse.y / Math.max(height, 1)) * 20 - 10;
      if (grid) {
        grid.style.transform = `translate(${gridX}px, ${gridY}px)`;
      }

      raf = window.requestAnimationFrame(animate);
    };

    let phraseIndex = 0;
    let charIndex = 0;
    let isDeleting = false;
    const typeSpeed = 100;
    const deleteSpeed = 50;
    const pauseTime = 2000;

    const runHeroTypewriter = () => {
      if (disposed) return;
      const phrase = typingPhrases[phraseIndex];
      if (isDeleting) {
        typewriterTarget.textContent = phrase.substring(0, charIndex - 1);
        charIndex -= 1;
      } else {
        typewriterTarget.textContent = phrase.substring(0, charIndex + 1);
        charIndex += 1;
      }

      let delta = isDeleting ? deleteSpeed : typeSpeed;
      if (!isDeleting && charIndex === phrase.length) {
        isDeleting = true;
        delta = pauseTime;
      } else if (isDeleting && charIndex === 0) {
        isDeleting = false;
        phraseIndex = (phraseIndex + 1) % typingPhrases.length;
        delta = 500;
      }

      schedule(runHeroTypewriter, delta);
    };

    const createTimestamp = () => {
      const now = new Date();
      return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
    };

    let logIndex = 0;
    let logCharIndex = 0;
    let activeLine: HTMLSpanElement | null = null;

    const runTerminalTypewriter = () => {
      if (disposed) return;

      if (logIndex >= terminalTemplates.length) {
        schedule(() => {
          terminalContainer.innerHTML = '';
          terminalContainer.appendChild(terminalCursor);
          logIndex = 0;
          logCharIndex = 0;
          activeLine = null;
          runTerminalTypewriter();
        }, 6000);
        return;
      }

      const current = terminalTemplates[logIndex];

      if (logCharIndex === 0) {
        const line = document.createElement('div');
        line.className = 'flex space-x-3 mb-2 terminal-glow tracking-tight';

        const stamp = document.createElement('span');
        stamp.className = 'text-cyan-900/60 font-mono';
        stamp.textContent = `[${createTimestamp()}]`;

        const content = document.createElement('span');
        content.className = 'text-[#4CD7F6] font-mono typewriter-line';
        content.textContent = '';

        line.appendChild(stamp);
        line.appendChild(content);
        terminalContainer.appendChild(line);
        activeLine = content;
      }

      if (!activeLine) return;

      if (logCharIndex < current.length) {
        activeLine.textContent += current.charAt(logCharIndex);
        logCharIndex += 1;
        activeLine.after(terminalCursor);
        terminalWrapper.scrollTop = terminalWrapper.scrollHeight;
        schedule(runTerminalTypewriter, 15 + Math.random() * 30);
      } else {
        logIndex += 1;
        logCharIndex = 0;
        schedule(runTerminalTypewriter, 1500);
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
      { threshold: 0.1, rootMargin: '0px 0px -50px 0px' },
    );
    document.querySelectorAll('.reveal').forEach((el) => observer.observe(el));

    resize();
    initParticles();
    animate();
    onScroll();
    runHeroTypewriter();
    runTerminalTypewriter();

    window.addEventListener('resize', resize);
    window.addEventListener('mousemove', onPointer);
    window.addEventListener('scroll', onScroll);

    return () => {
      disposed = true;
      window.cancelAnimationFrame(raf);
      timeoutIds.forEach((id) => window.clearTimeout(id));
      observer.disconnect();
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', onPointer);
      window.removeEventListener('scroll', onScroll);
    };
  }, []);

  return (
    <div className="font-body selection:bg-cyan-500/30 selection:text-white">
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="grid-overlay" id="interactive-grid" />
        <div className="absolute -top-1/4 -left-1/4 w-[80vw] h-[80vw] glow-radial opacity-60" />
        <div className="absolute -bottom-1/4 -right-1/4 w-[70vw] h-[70vw] glow-cyan opacity-40" />
        <canvas id="stellar-canvas" />
      </div>

      <header className="docked full-width top-0 sticky z-50 bg-[#0d0e13]/40 backdrop-blur-3xl border-b border-cyan-400/30 shadow-[0px_20px_40px_rgba(34,211,238,0.2)]" id="top-nav">
        <nav className="flex justify-between items-center w-full px-8 py-4 max-w-screen-2xl mx-auto">
          <a className="text-2xl font-black tracking-tighter text-cyan-300 font-headline uppercase" href="/">
            AgentHelpJob
          </a>
          <div className="hidden md:flex items-center space-x-10">
            <a className="text-cyan-200 border-b-2 border-cyan-400 pb-1 font-['Space_Grotesk'] tracking-tight" href="#hero">
              首页
            </a>
            <a className="text-cyan-100/70 hover:text-cyan-200 transition-colors font-['Space_Grotesk'] tracking-tight" href="#showcase">
              产品功能
            </a>
            <a className="text-cyan-100/70 hover:text-cyan-200 transition-colors font-['Space_Grotesk'] tracking-tight" href="#workspace">
              工作台
            </a>
            <a className="text-cyan-100/70 hover:text-cyan-200 transition-colors font-['Space_Grotesk'] tracking-tight" href="#footer">
              加入社群
            </a>
          </div>
          <a className="bg-gradient-to-r from-cyan-400 to-cyan-300 text-[#0d0e13] px-6 py-2.5 rounded-full font-bold hover:scale-105 active:scale-95 transition-all duration-300 shadow-lg shadow-cyan-400/30 btn-glow" href="/app">
            立即使用
          </a>
        </nav>
      </header>

      <main className="relative z-10">
        <section className="min-h-[90vh] flex flex-col items-center justify-center px-6 pt-20 pb-12" id="hero">
          <div className="text-center max-w-5xl mx-auto mb-16">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full border border-cyan-400/40 bg-cyan-500/10 mb-8">
              <span className="w-2 h-2 rounded-full bg-cyan-300 animate-ping" />
              <span className="text-[0.6875rem] uppercase tracking-[0.2em] text-cyan-300 font-bold">System Status: Active // v3.0.1</span>
            </div>
            <h1 className="font-headline text-5xl md:text-8xl font-bold tracking-tighter leading-tight text-glow mb-8 bg-clip-text text-transparent bg-gradient-to-b from-white to-cyan-300">
              让 AI 助你斩获
              <br />
              <span className="text-cyan-200 italic" style={{ textShadow: '0 0 15px rgba(76, 215, 246, 0.9), 0 0 30px rgba(76, 215, 246, 0.6)' }}>
                心仪大厂实习
              </span>
            </h1>
            <p className="text-xl md:text-2xl max-w-3xl mx-auto leading-relaxed font-['Space_Grotesk'] font-light tracking-wide terminal-glow text-cyan-50/80">
              AgentHelpJob：大学生专属 AI 求职管家。自动筛选、智能简历重构、自动化投递，你的第一个 Offer，由 AI 护航。
            </p>
            <div className="mt-10 flex flex-wrap justify-center gap-4">
              <a
                className="inline-flex items-center justify-center rounded-full border border-transparent bg-gradient-to-r from-cyan-400 to-cyan-300 px-6 py-3 text-sm font-semibold text-[#0d0e13] transition hover:shadow-[0_10px_30px_rgba(6,182,212,0.45)]"
                href="/app"
              >
                立即进入工作台
              </a>
              <a
                className="inline-flex items-center justify-center rounded-full border border-cyan-400/40 bg-transparent px-6 py-3 text-sm font-semibold text-cyan-100 transition hover:border-cyan-300 hover:text-cyan-200"
                href="#showcase"
              >
                探索产品能力
              </a>
            </div>
          </div>
        </section>

        <section className="px-4 pb-24" id="workspace">
          <div className="w-full max-w-7xl mx-auto">
            <div className="rounded-[32px] border border-cyan-400/25 bg-[#05080d]/70 backdrop-blur-2xl shadow-[0_30px_120px_rgba(0,0,0,0.45)] overflow-hidden">
              <div className="flex flex-col gap-3 border-b border-cyan-400/15 px-6 py-5 md:flex-row md:items-center md:justify-between md:px-8 text-left">
                <div>
                  <div className="text-[0.72rem] font-mono uppercase tracking-[0.22em] text-cyan-300/80">
                    AI Job Cockpit
                  </div>
                  <h2 className="mt-2 font-headline text-2xl font-bold text-cyan-50 md:text-3xl">
                    ????????
                  </h2>
                  <p className="mt-2 max-w-3xl text-sm leading-6 text-cyan-100/65 md:text-base">
                    ??????????Challenge ????????????
                  </p>
                </div>
                <a className="inline-flex items-center justify-center rounded-full border border-cyan-400/25 bg-cyan-400/10 px-5 py-3 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-400/18" href="/app">
                  ???????
                </a>
              </div>

              <div className="relative h-[900px] w-full bg-[#04070c] md:h-[1020px]">
                <iframe src="/app" title="AgentHelpJob Workspace" className="h-full w-full border-0 bg-[#04070c]" loading="lazy" />
              </div>
            </div>
          </div>
        </section>

        <section className="max-w-7xl mx-auto px-8 py-24 reveal" id="showcase">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {showcaseCards.map((card) => (
              <div className="glass-panel p-6 rounded-xl border border-cyan-400/20 shadow-[0_0_50px_rgba(34,211,238,0.05)] relative group hover:border-cyan-400/60 transition-all duration-500" key={card.title}>
                <div className="mb-8 w-14 h-14 rounded-xl bg-cyan-400/20 flex items-center justify-center border border-cyan-400/30 group-hover:scale-110 transition-all">
                  <span className="material-symbols-outlined text-cyan-300 text-3xl">{card.icon}</span>
                </div>
                <h3 className="font-headline text-2xl font-bold mb-4 text-cyan-300">{card.title}</h3>
                <p className="text-cyan-50 leading-relaxed">{card.text}</p>
              </div>
            ))}
          </div>
        </section>

      </main>

      <footer className="bg-[#0D0E13] border-t border-cyan-900/50 relative z-20" id="footer">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 px-12 py-20 w-full max-w-screen-2xl mx-auto">
          <div className="col-span-1 md:col-span-1">
            <div className="text-2xl font-black text-cyan-300 mb-8 font-headline tracking-tighter uppercase terminal-glow">
              AgentHelpJob
            </div>
            <p className="text-[0.75rem] text-cyan-100/80 uppercase tracking-[0.15em] leading-relaxed font-['Space_Grotesk']">
              Cinematic Intelligence for the future of work.
              <br />
              Designed for the digital nomad.
            </p>
          </div>

          {footerColumns.map((col) => (
            <div key={col.title}>
              <h4 className="text-cyan-300 text-[0.75rem] uppercase tracking-[0.2em] font-bold mb-8 font-['Space_Grotesk'] border-b border-cyan-400/30 pb-2 w-fit">
                {col.title}
              </h4>
              <ul className="space-y-4">
                {col.links.map((link) => (
                  <li key={link}>
                    <a className="text-cyan-100/70 hover:text-cyan-300 transition-colors text-[0.75rem] uppercase tracking-[0.15em] font-['Space_Grotesk']" href="#">
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
              {col.title === '法律' ? (
                <div className="flex space-x-6 mt-10">
                  <span className="material-symbols-outlined text-cyan-300 hover:text-cyan-100 transition-colors cursor-pointer text-xl">terminal</span>
                  <span className="material-symbols-outlined text-cyan-300 hover:text-cyan-100 transition-colors cursor-pointer text-xl">code</span>
                </div>
              ) : null}
            </div>
          ))}
        </div>
        <div className="px-12 py-10 border-t border-cyan-900/30 text-center">
          <p className="text-[0.6875rem] uppercase tracking-[0.2em] text-cyan-100/40 font-['Space_Grotesk']">
            © 2026 AgentHelpJob. Cinematic Intelligence.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
