import React from 'react';
import { HashRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  FileTextOutlined,
  SearchOutlined,
  HistoryOutlined,
  LoginOutlined,
  RobotOutlined,
  CloudOutlined,
  RocketOutlined,
} from '@ant-design/icons';
import Dashboard from './pages/Dashboard';
import ResumeUploadSimple from './pages/ResumeUploadSimple';
import JobSearch from './pages/JobSearch';
import Records from './pages/Records';
import Login from './pages/Login';
import ResumeAnalysis from './pages/ResumeAnalysis';
import OpenClawSearch from './pages/OpenClawSearch';
import BossAutoApply from './pages/BossAutoApply';

const { Header, Sider, Content } = Layout;

const AppContent: React.FC = () => {
  const [collapsed, setCollapsed] = React.useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { key: '/', icon: <DashboardOutlined />, label: '仪表盘' },
    { key: '/login', icon: <LoginOutlined />, label: '登录' },
    {
      key: 'resume-group',
      icon: <FileTextOutlined />,
      label: '简历',
      children: [
        { key: '/resume', label: '简历管理' },
        { key: '/resume-analysis', icon: <RobotOutlined />, label: 'AI 分析' },
      ]
    },
    {
      key: 'job-group',
      icon: <SearchOutlined />,
      label: '岗位搜索',
      children: [
        { key: '/search', label: 'Boss直聘' },
        { key: '/openclaw-search', icon: <CloudOutlined />, label: 'OpenClaw' },
      ]
    },
    { key: '/boss-auto-apply', icon: <RocketOutlined />, label: '自动投递' },
    { key: '/records', icon: <HistoryOutlined />, label: '投递记录' },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed} width={220}>
        <div
          style={{
            height: 64,
            margin: 16,
            background: 'rgba(255, 255, 255, 0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: 18,
            fontWeight: 'bold'
          }}
        >
          {!collapsed && '🤖 AI 求职'}
        </div>
        <Menu
          theme="dark"
          selectedKeys={[location.pathname]}
          mode="inline"
          items={menuItems}
          onClick={({ key }) => {
            if (!key.includes('group')) {
              navigate(key);
            }
          }}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: 0, background: '#fff', paddingLeft: 24 }}>
          <h2 style={{ margin: 0 }}>AI 求职助手 v2.0 - 全功能集成版</h2>
        </Header>
        <Content style={{ margin: '24px 16px', padding: 24, background: '#fff', minHeight: 280, overflow: 'auto' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/login" element={<Login />} />
            <Route path="/resume" element={<ResumeUploadSimple />} />
            <Route path="/resume-analysis" element={<ResumeAnalysis />} />
            <Route path="/search" element={<JobSearch />} />
            <Route path="/openclaw-search" element={<OpenClawSearch />} />
            <Route path="/boss-auto-apply" element={<BossAutoApply />} />
            <Route path="/records" element={<Records />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
};

const App: React.FC = () => {
  return (
    <HashRouter>
      <AppContent />
    </HashRouter>
  );
};

export default App;
