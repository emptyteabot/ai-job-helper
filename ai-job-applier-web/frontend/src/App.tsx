import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

const LandingPage = lazy(() => import('./pages/LandingPage'));
const AgentChatWorkspace = lazy(() => import('./pages/AgentChatWorkspace'));
const SmartApply = lazy(() => import('./pages/SmartApply'));
const AutoApply = lazy(() => import('./pages/AutoApply'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const JobSearch = lazy(() => import('./pages/JobSearch'));
const Login = lazy(() => import('./pages/Login'));
const OpenClawSearch = lazy(() => import('./pages/OpenClawSearch'));
const Records = lazy(() => import('./pages/Records'));
const ResumeAnalysis = lazy(() => import('./pages/ResumeAnalysis'));
const ResumeUpload = lazy(() => import('./pages/ResumeUpload'));
const ResumeUploadSimple = lazy(() => import('./pages/ResumeUploadSimple'));
const ChallengeCenter = lazy(() => import('./pages/ChallengeCenter'));

const RouteFallback: React.FC = () => (
  <div
    style={{
      minHeight: '100vh',
      display: 'grid',
      placeItems: 'center',
      background: '#121318',
      color: '#d0bcff',
      fontSize: '14px',
      letterSpacing: '0.04em',
      textTransform: 'uppercase',
      fontFamily: "'Space Grotesk', 'Inter', sans-serif",
    }}
  >
    Loading system...
  </div>
);

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Suspense fallback={<RouteFallback />}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/landing-legacy" element={<LandingPage />} />
          <Route path="/app" element={<AgentChatWorkspace />} />
          <Route path="/app-legacy" element={<SmartApply />} />
          <Route path="/auto-apply" element={<AutoApply />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/job-search" element={<JobSearch />} />
          <Route path="/login" element={<Login />} />
          <Route path="/openclaw-search" element={<OpenClawSearch />} />
          <Route path="/records" element={<Records />} />
          <Route path="/resume-analysis" element={<ResumeAnalysis />} />
          <Route path="/resume-upload" element={<ResumeUpload />} />
          <Route path="/resume-upload-simple" element={<ResumeUploadSimple />} />
          <Route path="/challenge-center" element={<ChallengeCenter />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
};

export default App;
