import React, { useMemo, useState } from 'react';
import { Alert, Button, Card, Form, Input, message, Space, Tag } from 'antd';
import { LoginOutlined, LogoutOutlined, PhoneOutlined } from '@ant-design/icons';
import { apiUrl, getToken } from '../utils/network';

interface UserInfo {
  id: string;
  phone: string;
  nickname: string;
  plan: string;
  remaining_quota: number;
}

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState<UserInfo | null>(null);

  const hasToken = useMemo(() => Boolean(getToken()), []);

  const onLogin = async (values: { phone: string; code?: string }) => {
    setLoading(true);
    try {
      await fetch(`${apiUrl('/api/auth/send-code')}?phone=${encodeURIComponent(values.phone)}`, {
        method: 'POST',
      });

      const loginResp = await fetch(apiUrl('/api/auth/login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: values.phone, code: values.code || '123456' }),
      });

      let loginData: any = null;
      try {
        loginData = await loginResp.json();
      } catch {
        loginData = null;
      }

      if (!loginResp.ok) {
        const registerResp = await fetch(apiUrl('/api/auth/register'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            phone: values.phone,
            code: values.code || '123456',
            nickname: values.phone,
          }),
        });
        const registerData = await registerResp.json();
        if (!registerResp.ok || !registerData.success) {
          throw new Error(registerData.detail || registerData.message || '登录失败');
        }
        localStorage.setItem('token', registerData.token);
        setUser(registerData.user);
        message.success('注册并登录成功');
        return;
      }

      if (!loginData?.success) {
        throw new Error(loginData?.detail || loginData?.message || '登录失败');
      }

      localStorage.setItem('token', loginData.token);
      setUser(loginData.user);
      message.success('登录成功');
    } catch (error: any) {
      message.error(error?.message || '登录失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const onLogout = async () => {
    const token = getToken();
    if (token) {
      try {
        await fetch(apiUrl('/api/auth/logout'), {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch {
        // ignore network error on local cleanup
      }
    }

    localStorage.removeItem('token');
    setUser(null);
    message.success('已退出登录');
  };

  return (
    <div style={{ maxWidth: 560, margin: '24px auto' }}>
      <Card title="账号登录" bordered>
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Alert
            type="info"
            showIcon
            message="登录说明"
            description="开发环境验证码固定为 123456。登录后可解锁简历管理、分析、批量投递和统计。"
          />

          {hasToken && !user && <Tag color="processing">检测到本地已有 token，可直接使用功能页</Tag>}

          {user && (
            <Alert
              type="success"
              showIcon
              message="已登录"
              description={`手机号：${user.phone} ｜ 套餐：${user.plan} ｜ 剩余额度：${user.remaining_quota}`}
            />
          )}

          {!user ? (
            <Form layout="vertical" onFinish={onLogin}>
              <Form.Item
                name="phone"
                label="手机号"
                rules={[
                  { required: true, message: '请输入手机号' },
                  { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确' },
                ]}
              >
                <Input size="large" prefix={<PhoneOutlined />} placeholder="请输入手机号" />
              </Form.Item>

              <Form.Item name="code" label="验证码（默认 123456）">
                <Input size="large" placeholder="不填则默认 123456" />
              </Form.Item>

              <Button type="primary" htmlType="submit" size="large" icon={<LoginOutlined />} loading={loading} block>
                登录 / 注册
              </Button>
            </Form>
          ) : (
            <Button danger size="large" icon={<LogoutOutlined />} onClick={onLogout} block>
              退出登录
            </Button>
          )}
        </Space>
      </Card>
    </div>
  );
};

export default Login;
