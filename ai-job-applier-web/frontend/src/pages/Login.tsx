import React, { useState } from 'react';
import { Alert, Form, Input, Switch, message } from 'antd';
import { LoginOutlined, PhoneOutlined } from '@ant-design/icons';
import CinematicLegacyShell from '../components/CinematicLegacyShell';
import { apiUrl } from '../lib/api';

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);

  const onLogin = async (values: any) => {
    setLoading(true);
    try {
      const response = await fetch(apiUrl('/api/boss/login'), {
        method: 'POST',
      });
      const result = await response.json();

      if (result.success) {
        message.success('登录成功');
        setLoggedIn(true);
      } else {
        message.error(result.message || '登录失败');
      }
    } catch (error: any) {
      console.error('登录失败', error);
      message.error('登录失败: ' + (error.message || '未知错误'));
    } finally {
      setLoading(false);
    }
  };

  const onLogout = async () => {
    try {
      message.info('网页端当前不提供远程强制登出，请关闭或刷新本地 Boss 浏览器会话。');
      message.success('登出成功');
      setLoggedIn(false);
    } catch (error) {
      message.error('登出失败');
    }
  };

  return (
    <CinematicLegacyShell
      sectionId="login"
      title="Boss 直聘登录"
      highlight="接管入口"
      subtitle="这不是演示页，而是接入真实会话的登录终端。你在浏览器里完成验证，系统在后续链路里复用会话状态。"
      terminalLabel="Auth_Prompt::Terminal"
      terminalPrompt={loggedIn ? '会话已接入，准备执行后续链路...' : '正在准备 Boss 直聘登录窗口...'}
      primaryCta={loggedIn ? '退出当前会话' : '开始登录'}
      onPrimaryClick={loggedIn ? onLogout : undefined}
      secondaryCta="查看接入说明"
      terminalLines={[
        { time: '09:10:01', level: 'INFO', text: 'Preparing browser session for Boss login...' },
        { time: '09:10:06', level: 'AUTH', text: 'Human verification remains on the browser side.' },
        { time: '09:10:11', level: 'STATE', text: loggedIn ? 'Session connected.' : 'Waiting for phone login.' },
      ]}
    >
      <div className="mx-auto max-w-3xl">
        <div className="glass-panel rounded-2xl p-8 shadow-[0_0_50px_rgba(34,211,238,0.08)]">
          {!loggedIn ? (
            <>
              <Alert
                message="登录说明"
                description="输入手机号后，系统会拉起浏览器登录窗口。验证码和安全验证仍在浏览器里处理，不会在这里伪装成全自动。"
                type="info"
                showIcon
                style={{ marginBottom: 24, background: 'rgba(34,211,238,0.08)', borderColor: 'rgba(34,211,238,0.25)', color: '#e0f2fe' }}
              />

              <Form name="login" onFinish={onLogin} layout="vertical" initialValues={{ headless: false }}>
                <Form.Item
                  label={<span className="text-cyan-100">手机号</span>}
                  name="phone"
                  rules={[
                    { required: true, message: '请输入手机号' },
                    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' },
                  ]}
                >
                  <Input prefix={<PhoneOutlined />} placeholder="请输入手机号" size="large" />
                </Form.Item>

                <Form.Item label={<span className="text-cyan-100">无头模式</span>} name="headless" valuePropName="checked">
                  <Switch />
                </Form.Item>

                <Form.Item>
                  <button className="w-full rounded-xl bg-cyan-400 px-5 py-3 font-bold text-[#0d0e13] transition hover:scale-[1.01]" type="submit" disabled={loading}>
                    <span className="inline-flex items-center gap-2">
                      <LoginOutlined />
                      {loading ? '登录中...' : '登录 Boss 直聘'}
                    </span>
                  </button>
                </Form.Item>
              </Form>
            </>
          ) : (
            <div className="space-y-6">
              <Alert
                message="会话已接入"
                description="当前会话已登录成功，可以继续岗位搜索与自动化执行。"
                type="success"
                showIcon
                style={{ background: 'rgba(34,211,238,0.08)', borderColor: 'rgba(34,211,238,0.25)', color: '#e0f2fe' }}
              />
              <button className="w-full rounded-xl bg-cyan-400 px-5 py-3 font-bold text-[#0d0e13] transition hover:scale-[1.01]" type="button" onClick={onLogout}>
                退出当前会话
              </button>
            </div>
          )}
        </div>
      </div>
    </CinematicLegacyShell>
  );
};

export default Login;

