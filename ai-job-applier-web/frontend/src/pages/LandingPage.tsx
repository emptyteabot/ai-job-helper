import React, { FormEvent, useEffect, useState } from 'react';

const typingPhrases = [
  '正在筛选高匹配实习岗位...',
  '正在重构你的简历表达...',
  '正在准备面试追问路径...',
  '正在等待你的下一条目标...',
];

const quickSeedPrompts = [
  '帮我找上海 AI 产品实习，先筛岗位，再开始执行。',
  '先分析我当前简历，指出最该改的三处。',
  '先看最近投递记录，再帮我调整下一轮方向。',
];

const icebergHints = ['搜索 / 简历 / 执行 / Challenge 都藏在这个窗口后面', '不会在未确认前自动投递', '你只负责描述目标'];

const buildSeededAppHref = (prompt: string) => {
  const cleaned = prompt.trim();
  if (!cleaned) return '/app';
  return `/app?seed_prompt=${encodeURIComponent(cleaned)}`;
};

const LandingPage: React.FC = () => {
  const [heroPrompt, setHeroPrompt] = useState('帮我找上海 AI 产品实习，先筛岗位，再开始执行。');

  const onHeroPromptSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    window.location.href = buildSeededAppHref(heroPrompt);
  };

  useEffect(() => {
    const canvas = document.getElementById('stellar-canvas') as HTMLCanvasElement | null;
    const grid = document.getElementById('interactive-grid');
    const typewriterTarget = document.getElementById('typewriter-target');

    if (!canvas) return;
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
    const particleCount = 860;
    const connectionDistance = 96;
    const forceRadius = 185;
    const repulsionStrength = 14;

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
          vx: (Math.random() - 0.5) * 0.92,
          vy: (Math.random() - 0.5) * 0.92,
          size: Math.random() * 1.1 + 0.34,
          baseColor: Math.random() > 0.5 ? '#22D3EE' : '#06B6D4',
          opacity: Math.random() * 0.22 + 0.06,
          glow: 0,
        });
      }
    };

    const onPointer = (e: MouseEvent) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
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
            const opacity = (1 - dist / connectionDistance) * 0.11;
            const combinedGlow = (p1.glow + p2.glow) * 0.5;

            ctx.beginPath();
            ctx.strokeStyle = `rgba(92, 224, 244, ${Math.min(0.4, opacity + combinedGlow * 0.3)})`;
            ctx.lineWidth = 0.46;
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        }
      }
    };

    const animate = () => {
      if (disposed) return;

      ctx.fillStyle = 'rgba(13, 14, 19, 0.18)';
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
          p.glow = force * 0.64;
        } else {
          p.glow *= 0.88;
        }

        const currentOpacity = Math.min(1, p.opacity + p.glow);
        ctx.beginPath();
        ctx.fillStyle = p.baseColor;
        ctx.globalAlpha = currentOpacity;
        ctx.arc(p.x, p.y, p.size + p.glow * 1.45, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1;
      }

      drawLines();

      if (grid) {
        const gridX = (mouse.x / Math.max(width, 1)) * 12 - 6;
        const gridY = (mouse.y / Math.max(height, 1)) * 12 - 6;
        grid.style.transform = `translate(${gridX}px, ${gridY}px)`;
      }

      raf = window.requestAnimationFrame(animate);
    };

    let phraseIndex = 0;
    let charIndex = 0;
    let isDeleting = false;

    const runHeroTypewriter = () => {
      if (disposed || !typewriterTarget) return;
      const phrase = typingPhrases[phraseIndex];

      if (isDeleting) {
        typewriterTarget.textContent = phrase.substring(0, charIndex - 1);
        charIndex -= 1;
      } else {
        typewriterTarget.textContent = phrase.substring(0, charIndex + 1);
        charIndex += 1;
      }

      let delta = isDeleting ? 42 : 86;
      if (!isDeleting && charIndex === phrase.length) {
        isDeleting = true;
        delta = 1600;
      } else if (isDeleting && charIndex === 0) {
        isDeleting = false;
        phraseIndex = (phraseIndex + 1) % typingPhrases.length;
        delta = 420;
      }

      schedule(runHeroTypewriter, delta);
    };

    resize();
    initParticles();
    animate();
    if (typewriterTarget) runHeroTypewriter();

    window.addEventListener('resize', resize);
    window.addEventListener('mousemove', onPointer);

    return () => {
      disposed = true;
      window.cancelAnimationFrame(raf);
      timeoutIds.forEach((id) => window.clearTimeout(id));
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', onPointer);
    };
  }, []);

  return (
    <div className="font-body selection:bg-cyan-500/30 selection:text-white">
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="grid-overlay" id="interactive-grid" />
        <div className="absolute inset-x-0 top-[15vh] mx-auto h-[24rem] w-[24rem] max-w-[74vw] rounded-full bg-[radial-gradient(circle_at_center,rgba(85,236,255,0.16),rgba(16,72,92,0.06)_40%,rgba(7,17,31,0)_78%)] blur-3xl" />
        <div className="glow-radial absolute left-1/2 top-[18vh] h-[30rem] w-[30rem] -translate-x-1/2 opacity-42" />
        <div className="glow-cyan absolute bottom-[-18vh] right-[-10vw] h-[30vw] w-[30vw] opacity-14" />
        <canvas id="stellar-canvas" />
      </div>

      <header className="relative z-20">
        <nav className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-5 md:px-8">
          <a className="font-headline text-2xl font-black uppercase tracking-tighter text-cyan-300" href="/">
            AgentHelpJob
          </a>
          <a className="rounded-full border border-cyan-400/20 bg-cyan-400/10 px-5 py-2 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-400/18" href="/app">
            登录
          </a>
        </nav>
      </header>

      <main className="relative z-10">
        <section className="flex min-h-[calc(100vh-84px)] flex-col items-center justify-center px-4 pb-12 pt-6 md:px-6 md:pb-16">
          <div className="mx-auto w-full max-w-5xl text-center">
            <div className="mb-6 inline-flex items-center space-x-2 rounded-full border border-cyan-400/28 bg-cyan-500/8 px-3 py-1">
              <span className="h-2 w-2 animate-pulse rounded-full bg-cyan-300" />
              <span className="text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-cyan-300">对话控制台 / 功能藏在冰山下</span>
            </div>

            <div className="relative mx-auto max-w-[50rem]">
              <div className="pointer-events-none absolute inset-x-[24%] top-12 h-24 rounded-full bg-[radial-gradient(circle_at_center,rgba(96,232,255,0.18),rgba(22,66,90,0.05)_52%,transparent_88%)] blur-3xl md:h-36" />
              <h1 className="text-glow relative mb-6 bg-gradient-to-b from-white via-[#dffcff] to-cyan-300 bg-clip-text font-headline text-5xl font-bold leading-[0.92] tracking-[-0.06em] text-transparent md:text-[6rem]">
                把复杂度埋进
                <span className="mt-2 block text-cyan-200">冰山下面。</span>
              </h1>
            </div>

            <p className="mx-auto max-w-3xl text-base leading-relaxed text-cyan-50/76 md:text-[1.2rem]">
              你只描述目标。后台会去做搜索、简历分析、执行推进、Challenge 接管和表单填充。中途你可以像和 GPT 对话一样追加条件。
            </p>

            <div className="mx-auto mt-10 w-full max-w-4xl overflow-hidden rounded-[34px] border border-cyan-300/28 bg-[linear-gradient(180deg,rgba(5,10,16,0.92),rgba(4,9,15,0.82))] shadow-[0_24px_80px_rgba(0,0,0,0.34)] backdrop-blur-3xl">
              <div className="border-b border-cyan-200/22 px-6 py-5 text-left">
                <div className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-cyan-300">对话工作台</div>
                <div className="mt-1 text-sm text-cyan-50/72">用一句自然语言描述目标，其他能力都藏在下面。</div>
              </div>

              <div className="px-6 py-10 md:px-10 md:py-14">
                <div className="mx-auto max-w-2xl">
                  <div className="text-2xl font-semibold text-cyan-50 md:text-[2rem]">从一句自然语言开始</div>
                  <p className="mt-4 text-base leading-8 text-cyan-100/50">
                    例如：帮我找深圳 AI 产品实习，并开始执行。或者：先看最近投递记录，再帮我调整下一轮策略。
                  </p>
                  <div className="mt-8 flex flex-wrap justify-center gap-3">
                    {quickSeedPrompts.map((prompt) => (
                      <a
                        key={prompt}
                        className="rounded-full border border-cyan-400/16 bg-cyan-400/6 px-4 py-2 text-sm text-cyan-100/74 transition hover:border-cyan-300/38 hover:bg-cyan-400/12"
                        href={buildSeededAppHref(prompt)}
                      >
                        {prompt}
                      </a>
                    ))}
                  </div>
                </div>
              </div>

              <div className="border-t border-cyan-200/20 px-5 py-4 md:px-6">
                <div className="mb-3 flex flex-wrap items-center gap-2 text-xs text-cyan-100/48">
                  <span className="rounded-full border border-cyan-400/18 px-3 py-1">隐藏能力：搜索 / 执行 / Challenge / 表单填充 / 记录</span>
                  <span className="rounded-full border border-cyan-400/18 px-3 py-1">默认不会在未确认前自动投递</span>
                </div>

                <form className="flex items-end gap-3" onSubmit={onHeroPromptSubmit}>
                  <label className="sr-only" htmlFor="hero-seed-prompt">
                    Seed prompt
                  </label>
                  <div className="flex-1 rounded-[28px] border border-cyan-300/20 bg-black/24 px-4 py-3">
                    <textarea
                      className="min-h-[56px] w-full resize-none bg-transparent text-[15px] leading-7 text-cyan-50 outline-none placeholder:text-cyan-100/32"
                      id="hero-seed-prompt"
                      onChange={(event) => setHeroPrompt(event.target.value)}
                      placeholder="例如：帮我找上海 AI 产品实习，先筛岗位，再开始执行。"
                      value={heroPrompt}
                    />
                    <div className="mt-2 flex items-center justify-between gap-3 text-left">
                      <span className="text-[0.6rem] uppercase tracking-[0.2em] text-cyan-100/48">Prompt stream</span>
                      <span className="text-xs text-cyan-200/78">
                        &gt; <span id="typewriter-target" />
                      </span>
                    </div>
                  </div>
                  <button
                    className="inline-flex h-14 shrink-0 items-center justify-center rounded-full bg-gradient-to-r from-cyan-400 to-sky-500 px-6 text-sm font-bold text-[#0d0e13] shadow-[0_0_30px_rgba(34,211,238,0.22)] transition hover:-translate-y-[1px]"
                    type="submit"
                  >
                    发送
                  </button>
                </form>

                <div className="mt-4 grid gap-2 text-left md:grid-cols-3">
                  {icebergHints.map((hint) => (
                    <div key={hint} className="rounded-2xl border border-cyan-400/12 bg-white/3 px-4 py-3 text-xs leading-6 text-cyan-100/58">
                      {hint}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default LandingPage;
