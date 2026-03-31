import React, { Suspense, lazy, useMemo } from 'react';
import { BrowserRouter, Link, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import PrivacyPage from './pages/PrivacyPage';
import TermsPage from './pages/TermsPage';

const SmartApply = lazy(() => import('./pages/SmartApply'));
const ResumeUpload = lazy(() => import('./pages/ResumeUpload'));
const ResumeAnalysis = lazy(() => import('./pages/ResumeAnalysis'));
const JobSearch = lazy(() => import('./pages/JobSearch'));
const OpenClawSearch = lazy(() => import('./pages/OpenClawSearch'));
const AutoApply = lazy(() => import('./pages/AutoApply'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Records = lazy(() => import('./pages/Records'));
const Login = lazy(() => import('./pages/Login'));

const LoadingView: React.FC = () => (
  <div style={{ minHeight: '50vh', display: 'grid', placeItems: 'center', color: '#475569' }}>
    页面加载中...
  </div>
);

const navItems = [
  { key: '/', label: '首页' },
  { key: '/smart-apply', label: '智能投递' },
  { key: '/resume-upload', label: '简历管理' },
  { key: '/resume-analysis', label: 'Agent 分析' },
  { key: '/job-search', label: '岗位搜索' },
  { key: '/openclaw-search', label: 'OpenClaw 搜索' },
  { key: '/auto-apply', label: '批量投递' },
  { key: '/dashboard', label: '仪表盘' },
  { key: '/records', label: '投递记录' },
  { key: '/login', label: '登录' },
];

const resolveSelectedKey = (pathname: string) => {
  if (pathname === '/app') {
    return '/smart-apply';
  }
  const matched = navItems.find((item) => pathname === item.key || pathname.startsWith(`${item.key}/`));
  return matched?.key || '/';
};

const AppShell: React.FC = () => {
  const location = useLocation();
  const selectedKey = useMemo(() => resolveSelectedKey(location.pathname), [location.pathname]);
  const isMarketingPage = location.pathname === '/' || location.pathname === '/privacy' || location.pathname === '/terms';

  return (
    <div style={{ minHeight: '100vh', background: '#f1f5f9' }}>
      {!isMarketingPage && (
        <header
          style={{
            position: 'sticky',
            top: 0,
            zIndex: 20,
            background: '#0f172a',
            borderBottom: '1px solid rgba(255,255,255,0.08)',
          }}
        >
          <div
            style={{
              maxWidth: 1280,
              margin: '0 auto',
              padding: '10px 12px',
              display: 'flex',
              gap: 8,
              flexWrap: 'wrap',
              alignItems: 'center',
            }}
          >
            {navItems.map((item) => {
              const active = selectedKey === item.key;
              return (
                <Link
                  key={item.key}
                  to={item.key}
                  style={{
                    textDecoration: 'none',
                    color: '#e2e8f0',
                    fontSize: 14,
                    padding: '6px 10px',
                    borderRadius: 8,
                    background: active ? '#2563eb' : 'transparent',
                    border: active ? '1px solid #1d4ed8' : '1px solid transparent',
                  }}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        </header>
      )}

      <main style={isMarketingPage ? {} : { padding: 20, maxWidth: 1280, width: '100%', margin: '0 auto' }}>
        <Suspense fallback={<LoadingView />}>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/app" element={<Navigate to="/smart-apply" replace />} />
            <Route path="/smart-apply" element={<SmartApply />} />
            <Route path="/resume-upload" element={<ResumeUpload />} />
            <Route path="/resume-analysis" element={<ResumeAnalysis />} />
            <Route path="/job-search" element={<JobSearch />} />
            <Route path="/openclaw-search" element={<OpenClawSearch />} />
            <Route path="/auto-apply" element={<AutoApply />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/records" element={<Records />} />
            <Route path="/login" element={<Login />} />
            <Route path="/privacy" element={<PrivacyPage />} />
            <Route path="/terms" element={<TermsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  );
};

export default App;
