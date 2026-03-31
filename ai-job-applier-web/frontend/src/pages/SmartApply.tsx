import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Col,
  Form,
  Input,
  List,
  message,
  Modal,
  Progress,
  Row,
  Statistic,
  Tag,
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  CrownOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { apiUrl, authFetch, getToken, wsUrl } from '../utils/network';

interface UserInfo {
  id: string;
  phone: string;
  nickname: string;
  plan: string;
  remaining_quota: number;
}

interface ApplyLog {
  job: string;
  company: string;
  greeting: string;
  success: boolean;
}

const planNameMap: Record<string, string> = {
  free: '免费版',
  basic: '基础版',
  pro: '专业版',
  yearly: '年费版',
};

const SmartApply: React.FC = () => {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState('');
  const [logs, setLogs] = useState<ApplyLog[]>([]);
  const [stats, setStats] = useState({ success: 0, failed: 0 });
  const [showLogin, setShowLogin] = useState(false);
  const [showUpgrade, setShowUpgrade] = useState(false);
  const [resumeText, setResumeText] = useState('');

  const [loginForm] = Form.useForm();

  useEffect(() => {
    const saved = getToken();
    if (saved) {
      setToken(saved);
      void loadUserInfo(saved);
    } else {
      setShowLogin(true);
    }
  }, []);

  const planText = useMemo(() => (user ? planNameMap[user.plan] || user.plan : '-'), [user]);

  const loadUserInfo = async (authToken: string) => {
    try {
      const response = await fetch(apiUrl('/api/user/info'), {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      const data = await response.json();
      if (response.ok && data.success) {
        setUser(data.user);
      } else {
        localStorage.removeItem('token');
        setToken('');
        setShowLogin(true);
      }
    } catch {
      setShowLogin(true);
    }
  };

  const handleLogin = async (values: { phone: string; code?: string }) => {
    try {
      await fetch(`${apiUrl('/api/auth/send-code')}?phone=${encodeURIComponent(values.phone)}`, { method: 'POST' });

      const loginResp = await fetch(apiUrl('/api/auth/login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: values.phone, code: values.code || '123456' }),
      });

      const loginData = await loginResp.json();
      if (loginResp.ok && loginData.success) {
        localStorage.setItem('token', loginData.token);
        setToken(loginData.token);
        setUser(loginData.user);
        setShowLogin(false);
        message.success('登录成功');
        return;
      }

      const registerResp = await fetch(apiUrl('/api/auth/register'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: values.phone, code: values.code || '123456', nickname: values.phone }),
      });
      const registerData = await registerResp.json();
      if (!registerResp.ok || !registerData.success) {
        throw new Error(registerData.detail || registerData.message || '登录失败');
      }

      localStorage.setItem('token', registerData.token);
      setToken(registerData.token);
      setUser(registerData.user);
      setShowLogin(false);
      message.success('注册成功，已赠送免费额度');
    } catch (error: any) {
      message.error(error?.message || '登录失败');
    }
  };

  const handleUpgrade = async (plan: string) => {
    try {
      const response = await authFetch('/api/user/upgrade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan }),
      });
      const data = await response.json();
      if (!response.ok || !data.success) {
        throw new Error(data.detail || data.message || '升级失败');
      }
      setUser(data.user);
      setShowUpgrade(false);
      message.success(data.message || '升级成功');
    } catch (error: any) {
      message.error(error?.message || '升级失败');
    }
  };

  const onSubmit = async (values: any) => {
    if (!user) {
      setShowLogin(true);
      return;
    }
    if (user.remaining_quota <= 0) {
      setShowUpgrade(true);
      return;
    }
    if (!resumeText.trim()) {
      message.warning('请先填写简历内容');
      return;
    }

    setLoading(true);
    setProgress(0);
    setStage('准备中...');
    setLogs([]);
    setStats({ success: 0, failed: 0 });

    try {
      const ws = new WebSocket(wsUrl('/api/apply/ws'));

      ws.onopen = () => {
        ws.send(
          JSON.stringify({
            token,
            keyword: values.keyword,
            city: values.city || '全国',
            max_count: values.max_count || 5,
            resume_text: resumeText,
          })
        );
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.error) {
          message.error(data.message || '投递失败');
          setLoading(false);
          ws.close();
          return;
        }

        if (data.stage) {
          setStage(data.message || data.stage);
          const raw = typeof data.progress === 'number' ? data.progress : 0;
          const normalized = raw > 1 ? raw : raw * 100;
          setProgress(Math.round(normalized));
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
          setStats({ success: data.success_count || 0, failed: data.failed_count || 0 });
          setUser((prev) => (prev ? { ...prev, remaining_quota: data.remaining_quota ?? prev.remaining_quota } : prev));
        }

        if (data.stage === 'completed') {
          setLoading(false);
          setProgress(100);
          message.success(data.message || '投递完成');
          ws.close();
        }
      };

      ws.onerror = () => {
        message.error('连接失败，请稍后重试');
        setLoading(false);
      };

      ws.onclose = () => {
        setLoading(false);
      };
    } catch (error: any) {
      message.error(error?.message || '投递失败');
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: 20 }}>
      {user && (
        <Card style={{ marginBottom: 16, background: 'linear-gradient(135deg, #1d4ed8 0%, #0f766e 100%)' }}>
          <Row gutter={16}>
            <Col span={6}>
              <Statistic title={<span style={{ color: '#fff' }}>当前套餐</span>} value={planText} prefix={<CrownOutlined />} valueStyle={{ color: '#fff' }} />
            </Col>
            <Col span={6}>
              <Statistic title={<span style={{ color: '#fff' }}>剩余次数</span>} value={user.remaining_quota} suffix="次" valueStyle={{ color: '#fff' }} />
            </Col>
            <Col span={6}>
              <Statistic title={<span style={{ color: '#fff' }}>本次成功</span>} value={stats.success} suffix="个" valueStyle={{ color: '#86efac' }} />
            </Col>
            <Col span={6}>
              <Button type="primary" size="large" onClick={() => setShowUpgrade(true)} style={{ marginTop: 20 }}>
                升级套餐
              </Button>
            </Col>
          </Row>
        </Card>
      )}

      <h1 style={{ fontSize: 28, marginBottom: 8 }}>AI 智能投递</h1>
      <p style={{ color: '#64748b', marginBottom: 24 }}>输入关键词与简历内容，系统自动搜索岗位、生成沟通语并批量投递。</p>

      <Alert
        message="使用说明"
        description="每次投递会消耗额度。建议先在岗位搜索页筛一遍岗位，再回到这里做全自动投递。"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Card style={{ marginBottom: 16 }}>
        <Form layout="vertical" onFinish={onSubmit} initialValues={{ max_count: 5 }}>
          <Form.Item label="搜索关键词" name="keyword" rules={[{ required: true, message: '请输入搜索关键词' }]}>
            <Input placeholder="例如：Python 后端 / 前端开发 / 产品经理" size="large" />
          </Form.Item>

          <Form.Item label="城市" name="city">
            <Input placeholder="例如：北京、上海、全国" size="large" />
          </Form.Item>

          <Form.Item label="投递数量" name="max_count">
            <Input type="number" min={1} max={30} size="large" />
          </Form.Item>

          <Form.Item label="简历内容" required>
            <Input.TextArea
              rows={7}
              placeholder="粘贴你的简历内容（项目经历、技能栈、目标岗位等）"
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
            />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<ThunderboltOutlined />} loading={loading} size="large" block>
              {loading ? '投递中...' : '开始自动投递'}
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {(loading || progress > 0) && (
        <Card style={{ marginBottom: 16 }}>
          <Progress percent={progress} status={loading ? 'active' : 'normal'} />
          <div style={{ textAlign: 'center', marginTop: 8, color: '#64748b' }}>{stage}</div>
          <div style={{ textAlign: 'center', marginTop: 8 }}>
            <Tag color="green">成功 {stats.success}</Tag>
            <Tag color="red">失败 {stats.failed}</Tag>
          </div>
        </Card>
      )}

      {logs.length > 0 && (
        <Card title="投递日志">
          <List
            dataSource={logs}
            renderItem={(log) => (
              <List.Item>
                <List.Item.Meta
                  avatar={
                    log.success ? (
                      <CheckCircleOutlined style={{ color: '#16a34a', fontSize: 20 }} />
                    ) : (
                      <CloseCircleOutlined style={{ color: '#ef4444', fontSize: 20 }} />
                    )
                  }
                  title={`${log.job} - ${log.company}`}
                  description={
                    <>
                      <div style={{ color: '#64748b', marginTop: 4 }}>沟通语：{log.greeting}</div>
                      <Tag color={log.success ? 'success' : 'error'} style={{ marginTop: 4 }}>
                        {log.success ? '投递成功' : '投递失败'}
                      </Tag>
                    </>
                  }
                />
              </List.Item>
            )}
          />
        </Card>
      )}

      <Modal title="登录 / 注册" open={showLogin} footer={null} onCancel={() => setShowLogin(false)}>
        <Form form={loginForm} onFinish={handleLogin} layout="vertical">
          <Form.Item label="手机号" name="phone" rules={[{ required: true, message: '请输入手机号' }]}> 
            <Input placeholder="请输入手机号" size="large" />
          </Form.Item>
          <Form.Item label="验证码" name="code">
            <Input placeholder="默认 123456" size="large" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" size="large" block>
              登录 / 注册
            </Button>
          </Form.Item>
          <Alert message="开发环境提示" description="验证码默认 123456" type="info" showIcon />
        </Form>
      </Modal>

      <Modal title="升级套餐" open={showUpgrade} footer={null} onCancel={() => setShowUpgrade(false)} width={860}>
        <Row gutter={16}>
          <Col span={8}>
            <Card hoverable onClick={() => handleUpgrade('basic')} style={{ textAlign: 'center' }}>
              <h3>基础版</h3>
              <div style={{ fontSize: 30, color: '#2563eb', margin: '18px 0' }}>¥19.9<span style={{ fontSize: 14 }}>/月</span></div>
              <div>每天 30 次投递</div>
              <div>AI 沟通语生成</div>
              <Button type="primary" style={{ marginTop: 16 }}>立即升级</Button>
            </Card>
          </Col>
          <Col span={8}>
            <Card hoverable onClick={() => handleUpgrade('pro')} style={{ textAlign: 'center', borderColor: '#2563eb' }}>
              <Tag color="blue">推荐</Tag>
              <h3>专业版</h3>
              <div style={{ fontSize: 30, color: '#2563eb', margin: '18px 0' }}>¥39.9<span style={{ fontSize: 14 }}>/月</span></div>
              <div>每天 100 次投递</div>
              <div>优先处理 + 数据统计</div>
              <Button type="primary" style={{ marginTop: 16 }}>立即升级</Button>
            </Card>
          </Col>
          <Col span={8}>
            <Card hoverable onClick={() => handleUpgrade('yearly')} style={{ textAlign: 'center' }}>
              <Tag color="gold">超值</Tag>
              <h3>年费版</h3>
              <div style={{ fontSize: 30, color: '#2563eb', margin: '18px 0' }}>¥199<span style={{ fontSize: 14 }}>/年</span></div>
              <div>近似无限额度</div>
              <div>优先支持</div>
              <Button type="primary" style={{ marginTop: 16 }}>立即升级</Button>
            </Card>
          </Col>
        </Row>
      </Modal>
    </div>
  );
};

export default SmartApply;
