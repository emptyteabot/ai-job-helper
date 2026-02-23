import React, { useState, useEffect } from 'react';
import { Card, Form, Input, InputNumber, Button, Steps, Alert, message, Space, Tag, List, Progress } from 'antd';
import { ThunderboltOutlined, CheckCircleOutlined, CloseCircleOutlined, PhoneOutlined, SafetyOutlined } from '@ant-design/icons';

const { Step } = Steps;
const { TextArea } = Input;

interface ApplyLog {
  job: string;
  company: string;
  success: boolean;
  message: string;
}

const BossAutoApply: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);
  const [codeLoading, setCodeLoading] = useState(false);
  const [applyLoading, setApplyLoading] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  
  const [keyword, setKeyword] = useState('');
  const [city, setCity] = useState('北京');
  const [maxCount, setMaxCount] = useState(10);
  
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState<ApplyLog[]>([]);
  const [stats, setStats] = useState({ success: 0, failed: 0 });

  // 检查登录状态
  useEffect(() => {
    const savedPhone = localStorage.getItem('boss_phone');
    if (savedPhone) {
      setPhone(savedPhone);
      checkLoginStatus(savedPhone);
    }
  }, []);

  const checkLoginStatus = async (phoneNumber: string) => {
    try {
      const response = await fetch(`http://localhost:8765/api/simple-apply/status/${phoneNumber}`);
      const data = await response.json();
      if (data.logged_in) {
        setIsLoggedIn(true);
        setCurrentStep(2);
        message.success('已登录');
      }
    } catch (error) {
      console.error('检查登录状态失败', error);
    }
  };

  // 步骤1：初始化登录（自动填写手机号并获取验证码）
  const handleInitLogin = async () => {
    if (!phone || phone.length !== 11) {
      message.error('请输入正确的手机号');
      return;
    }

    setLoginLoading(true);
    try {
      const response = await fetch('http://localhost:8765/api/simple-apply/init-login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        message.success(data.message);
        localStorage.setItem('boss_phone', phone);
        setCurrentStep(1);
      } else {
        message.error(data.detail || '初始化登录失败');
      }
    } catch (error) {
      console.error('初始化登录失败', error);
      message.error('服务器连接失败，请确保后端已启动');
    } finally {
      setLoginLoading(false);
    }
  };

  // 步骤2：提交验证码
  const handleVerifyCode = async () => {
    if (!code || code.length !== 6) {
      message.error('请输入6位验证码');
      return;
    }

    setCodeLoading(true);
    try {
      const response = await fetch('http://localhost:8765/api/simple-apply/verify-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, code })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        message.success(data.message);
        setIsLoggedIn(true);
        setCurrentStep(2);
      } else {
        message.error(data.detail || '验证码错误');
      }
    } catch (error) {
      console.error('验证码提交失败', error);
      message.error('验证码提交失败');
    } finally {
      setCodeLoading(false);
    }
  };

  // 步骤3：开始投递
  const handleStartApply = async () => {
    if (!keyword || !city) {
      message.error('请填写岗位关键词和城市');
      return;
    }

    // 获取简历
    let resumeText = '';
    try {
      const resumeResult = await fetch('http://localhost:8765/api/resume/list', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const resumeData = await resumeResult.json();

      if (!resumeData.resumes || resumeData.resumes.length === 0) {
        message.error('请先上传简历');
        return;
      }

      const firstResume = resumeData.resumes[0];
      const textResult = await fetch(`http://localhost:8765/api/resume/text/${firstResume.filename}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const textData = await textResult.json();
      resumeText = textData.text;
    } catch (error) {
      console.error('获取简历失败', error);
      message.error('获取简历失败');
      return;
    }

    setApplyLoading(true);
    setProgress(0);
    setLogs([]);
    setStats({ success: 0, failed: 0 });

    try {
      const response = await fetch('http://localhost:8765/api/simple-apply/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone,
          resume_text: resumeText,
          job_keyword: keyword,
          city,
          count: maxCount
        })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        message.success(data.message);
        setStats({
          success: data.success_count,
          failed: data.failed_count
        });
        
        // 转换日志格式
        if (data.details) {
          const formattedLogs = data.details.map((detail: any) => ({
            job: detail.job_title || '未知岗位',
            company: detail.company || '未知公司',
            success: detail.success,
            message: detail.success ? '投递成功' : '投递失败'
          }));
          setLogs(formattedLogs);
        }
        
        setProgress(100);
      } else {
        message.error(data.detail || data.message || '投递失败');
      }
    } catch (error) {
      console.error('投递失败', error);
      message.error('投递失败');
    } finally {
      setApplyLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '20px' }}>
      <h1 style={{ fontSize: 28, marginBottom: 8 }}>🚀 Boss 直聘自动投递</h1>
      <p style={{ color: '#666', marginBottom: 24 }}>
        后端保持浏览器打开 → 自动获取验证码 → 只需输入手机号和验证码
      </p>

      <Card style={{ marginBottom: 24 }}>
        <Steps current={currentStep}>
          <Step title="输入手机号" icon={<PhoneOutlined />} />
          <Step title="输入验证码" icon={<SafetyOutlined />} />
          <Step title="开始投递" icon={<ThunderboltOutlined />} />
        </Steps>
      </Card>

      {/* 步骤1：输入手机号 */}
      {currentStep === 0 && (
        <Card>
          <Alert
            message="第一步：输入手机号"
            description="后端会自动打开浏览器、填写手机号并获取验证码，您只需等待短信即可"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          <Space direction="vertical" style={{ width: '100%' }}>
            <Input
              size="large"
              placeholder="请输入手机号"
              prefix={<PhoneOutlined />}
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              maxLength={11}
            />
            <Button
              type="primary"
              size="large"
              block
              loading={loginLoading}
              onClick={handleInitLogin}
            >
              {loginLoading ? '正在获取验证码...' : '获取验证码'}
            </Button>
          </Space>
        </Card>
      )}

      {/* 步骤2：输入验证码 */}
      {currentStep === 1 && (
        <Card>
          <Alert
            message="第二步：输入验证码"
            description={`验证码已发送到 ${phone}，请查收短信并输入验证码`}
            type="success"
            showIcon
            style={{ marginBottom: 16 }}
          />
          <Space direction="vertical" style={{ width: '100%' }}>
            <Input
              size="large"
              placeholder="请输入6位验证码"
              prefix={<SafetyOutlined />}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              maxLength={6}
            />
            <Space style={{ width: '100%' }}>
              <Button onClick={() => setCurrentStep(0)}>返回</Button>
              <Button
                type="primary"
                size="large"
                style={{ flex: 1 }}
                loading={codeLoading}
                onClick={handleVerifyCode}
              >
                {codeLoading ? '登录中...' : '确认登录'}
              </Button>
            </Space>
          </Space>
        </Card>
      )}

      {/* 步骤3：开始投递 */}
      {currentStep === 2 && (
        <>
          <Card style={{ marginBottom: 16 }}>
            <Alert
              message="登录成功！"
              description={`已登录账号：${phone}`}
              type="success"
              showIcon
              style={{ marginBottom: 16 }}
            />
            
            <Form layout="vertical">
              <Form.Item label="搜索关键词" required>
                <Input
                  size="large"
                  placeholder="例如：Python工程师"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </Form.Item>

              <Form.Item label="城市" required>
                <Input
                  size="large"
                  placeholder="例如：北京、上海、深圳"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                />
              </Form.Item>

              <Form.Item label="投递数量">
                <InputNumber
                  size="large"
                  min={1}
                  max={50}
                  value={maxCount}
                  onChange={(val) => setMaxCount(val || 10)}
                  style={{ width: '100%' }}
                />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  size="large"
                  block
                  icon={<ThunderboltOutlined />}
                  loading={applyLoading}
                  onClick={handleStartApply}
                >
                  {applyLoading ? '投递中...' : '开始自动投递'}
                </Button>
              </Form.Item>
            </Form>
          </Card>

          {applyLoading && (
            <Card style={{ marginBottom: 16 }}>
              <Progress percent={Math.round(progress)} status="active" />
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
                          <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 20 }} />
                        ) : (
                          <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 20 }} />
                        )
                      }
                      title={log.job}
                      description={`${log.company} - ${log.message}`}
                    />
                  </List.Item>
                )}
              />
            </Card>
          )}
        </>
      )}
    </div>
  );
};

export default BossAutoApply;
