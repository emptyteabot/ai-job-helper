import React from 'react';

interface NavItem {
  href: string;
  label: string;
}

interface TerminalLine {
  time: string;
  level: string;
  text: string;
}

interface CinematicLegacyShellProps {
  sectionId: string;
  title: string;
  highlight?: string;
  subtitle: string;
  terminalLabel: string;
  terminalPrompt: string;
  primaryCta: string;
  secondaryCta?: string;
  onPrimaryClick?: () => void;
  onSecondaryClick?: () => void;
  navItems?: NavItem[];
  terminalLines?: TerminalLine[];
  children: React.ReactNode;
}

const defaultNavItems: NavItem[] = [
  { href: '#hero', label: '首页' },
  { href: '#workspace', label: '功能区' },
  { href: '#stream', label: '执行记录' },
  { href: '#footer', label: '页脚' },
];

const CinematicLegacyShell: React.FC<CinematicLegacyShellProps> = ({
  sectionId,
  title,
  highlight,
  subtitle,
  terminalLabel,
  terminalPrompt,
  primaryCta,
  secondaryCta,
  onPrimaryClick,
  onSecondaryClick,
  navItems = defaultNavItems,
  terminalLines = [],
  children,
}) => {
  const lines = terminalLines.length
    ? terminalLines
    : [{ time: '00:00:00', level: 'INFO', text: 'This page is active under the cinematic legacy shell.' }];

  return (
    <div className="font-body text-cyan-100 selection:bg-cyan-500/30 selection:text-white">
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="grid-overlay" />
        <div className="absolute -left-1/4 -top-1/4 h-[80vw] w-[80vw] glow-radial opacity-60" />
        <div className="absolute -bottom-1/4 -right-1/4 h-[70vw] w-[70vw] glow-cyan opacity-40" />
        <div className="particle-bg absolute inset-0 opacity-40" />
      </div>

      <main className="relative z-10">
        <header className="sticky top-0 z-50 w-full border-b border-cyan-400/30 bg-[#0d0e13]/40 backdrop-blur-3xl shadow-[0px_20px_40px_rgba(34,211,238,0.2)]">
          <nav className="mx-auto flex w-full max-w-screen-2xl items-center justify-between gap-4 px-6 py-4 md:px-8">
            <a className="font-headline text-2xl font-black uppercase tracking-tighter text-cyan-300" href="/">
              AgentHelpJob
            </a>
            <div className="hidden items-center space-x-10 md:flex">
              {navItems.map((item, index) => (
                <a
                  key={`${item.href}-${item.label}`}
                  className={
                    index === 0
                      ? "border-b-2 border-cyan-400 pb-1 font-['Space_Grotesk'] tracking-tight text-cyan-200"
                      : "font-['Space_Grotesk'] tracking-tight text-cyan-100/70 transition-colors hover:text-cyan-200"
                  }
                  href={item.href}
                >
                  {item.label}
                </a>
              ))}
            </div>
            <button
              className="btn-glow rounded-full bg-gradient-to-r from-cyan-400 to-cyan-300 px-5 py-2.5 font-bold text-[#0d0e13] transition-all duration-300 shadow-lg shadow-cyan-400/30 hover:scale-105 active:scale-95 md:px-6"
              type="button"
              onClick={onPrimaryClick}
            >
              {primaryCta}
            </button>
          </nav>
        </header>

        <section className="flex min-h-[70vh] flex-col items-center justify-center px-6 pb-20 pt-20" id="hero">
          <div className="mx-auto mb-12 max-w-5xl text-center">
            <div className="mb-8 inline-flex items-center space-x-2 rounded-full border border-cyan-400/40 bg-cyan-500/10 px-3 py-1">
              <span className="h-2 w-2 animate-ping rounded-full bg-cyan-300" />
              <span className="text-[0.6875rem] font-bold uppercase tracking-[0.2em] text-cyan-300">
                System Status: Active // Unified Shell
              </span>
            </div>
            <h1 className="text-glow mb-8 bg-gradient-to-b from-white to-cyan-300 bg-clip-text font-headline text-5xl font-bold leading-tight tracking-tighter text-transparent md:text-8xl">
              {title}
              {highlight ? (
                <>
                  <br />
                  <span className="italic text-cyan-200">{highlight}</span>
                </>
              ) : null}
            </h1>
            <p className="mx-auto max-w-3xl text-xl leading-relaxed text-cyan-50/80 md:text-2xl">{subtitle}</p>
          </div>

          <div className="w-full max-w-2xl px-4">
            <div className="glass-panel relative rounded-xl border border-cyan-300/40 p-6 shadow-[0_0_50px_rgba(34,211,238,0.2)]">
              <div className="absolute -top-3 left-6 rounded border border-cyan-300/40 bg-[#0d0e13] px-3 text-[0.6rem] font-mono uppercase tracking-widest text-cyan-300">
                {terminalLabel}
              </div>
              <div className="flex items-start gap-4">
                <span className="material-symbols-outlined text-2xl text-cyan-300">terminal</span>
                <div className="min-w-0 flex-1 break-words whitespace-normal border-r-2 border-cyan-400 pr-1 font-mono text-lg text-cyan-100">
                  {terminalPrompt}
                </div>
              </div>
              <div className="mt-4 flex items-center justify-between gap-4 text-[0.65rem] font-mono uppercase tracking-tighter text-cyan-200/50">
                <span className="min-w-0 flex-1 break-words whitespace-normal">legacy page is now under the same cinematic shell</span>
                <span>{sectionId}</span>
              </div>
            </div>
            {secondaryCta ? (
              <div className="mt-8 flex justify-center">
                <button
                  className="glass-panel rounded-full border border-cyan-400/30 px-8 py-3 text-cyan-200 transition-colors hover:bg-cyan-400/10"
                  type="button"
                  onClick={onSecondaryClick}
                >
                  {secondaryCta}
                </button>
              </div>
            ) : null}
          </div>
        </section>

        <section className="template-section-anchor mx-auto max-w-7xl px-6 py-20 md:px-8" id="workspace">
          {children}
        </section>

        <section className="template-section-anchor mx-auto max-w-6xl px-6 py-20 md:px-8" id="stream">
          <div className="relative overflow-hidden rounded-xl border border-cyan-400/30 bg-[#000000] shadow-2xl shadow-[0_0_30px_rgba(34,211,238,0.15)]">
            <div className="flex items-center justify-between border-b border-cyan-400/30 bg-cyan-900/40 px-6 py-3">
              <div className="flex space-x-2">
                <div className="h-3 w-3 rounded-full bg-red-500/60" />
                <div className="h-3 w-3 rounded-full bg-yellow-500/60" />
                <div className="h-3 w-3 rounded-full bg-green-500/60" />
              </div>
              <div className="text-[0.65rem] font-mono uppercase tracking-widest text-cyan-300">
                LEGACY_CORE::{sectionId.toUpperCase()}
              </div>
              <span className="material-symbols-outlined text-cyan-300">terminal</span>
            </div>
            <div className="custom-scrollbar terminal-content terminal-glow h-72 overflow-x-auto overflow-y-auto bg-black/40 p-6 font-mono text-sm leading-relaxed md:p-8">
              {lines.map((line, index) => (
                <div className="mb-2 flex min-w-0 space-x-3 tracking-tight" key={`${line.time}-${index}`}>
                  <span className="font-mono text-cyan-900/60">[{line.time}]</span>
                  <span className="min-w-0 break-words whitespace-normal font-mono text-[#4CD7F6]">
                    {line.level}: {line.text}
                  </span>
                </div>
              ))}
              <div className="mt-4 animate-pulse text-cyan-300">_</div>
            </div>
          </div>
        </section>

        <section className="relative px-6 py-24 text-center">
          <h2 className="mb-8 font-headline text-4xl font-bold leading-tight text-cyan-100 md:text-6xl">
            让旧页面也进入
            <br />
            <span className="neon-glow-cyan text-cyan-300">统一母版系统</span>
          </h2>
          <button
            className="btn-glow rounded-full bg-cyan-400 px-10 py-4 font-bold text-[#0d0e13] shadow-[0_0_30px_rgba(34,211,238,0.4)] transition-all hover:-translate-y-1 hover:shadow-[0_0_50px_rgba(34,211,238,0.6)]"
            type="button"
            onClick={onPrimaryClick}
          >
            {primaryCta}
          </button>
        </section>

        <footer className="relative z-20 border-t border-cyan-900/50 bg-[#0D0E13]" id="footer">
          <div className="mx-auto grid max-w-screen-2xl grid-cols-1 gap-12 px-8 py-16 md:grid-cols-4 md:px-12">
            <div>
              <div className="mb-6 font-headline text-lg font-bold uppercase tracking-tighter text-cyan-300">
                AgentHelpJob
              </div>
              <p className="text-[0.6875rem] uppercase tracking-[0.1em] leading-loose text-cyan-100/60">
                Cinematic intelligence for the future of job execution.
              </p>
            </div>
            <div>
              <h4 className="mb-6 text-[0.6875rem] font-bold uppercase tracking-[0.1em] text-cyan-300">产品</h4>
              <ul className="space-y-4 text-[0.6875rem] uppercase tracking-[0.1em] text-cyan-100/50">
                <li>核心看板</li>
                <li>AI 引擎</li>
                <li>价格计划</li>
              </ul>
            </div>
            <div>
              <h4 className="mb-6 text-[0.6875rem] font-bold uppercase tracking-[0.1em] text-cyan-300">资源</h4>
              <ul className="space-y-4 text-[0.6875rem] uppercase tracking-[0.1em] text-cyan-100/50">
                <li>开发文档</li>
                <li>API 状态</li>
                <li>社群</li>
              </ul>
            </div>
            <div>
              <h4 className="mb-6 text-[0.6875rem] font-bold uppercase tracking-[0.1em] text-cyan-300">法律</h4>
              <ul className="space-y-4 text-[0.6875rem] uppercase tracking-[0.1em] text-cyan-100/50">
                <li>隐私协议</li>
                <li>服务条款</li>
              </ul>
            </div>
          </div>
        </footer>
      </main>
    </div>
  );
};

export default CinematicLegacyShell;
