import React, { useEffect, useState } from 'react';
import { Alert, Badge, Button, Card, Checkbox, Form, Input, List, Space, Tag, message } from 'antd';
import { DollarOutlined, EnvironmentOutlined, SearchOutlined, ThunderboltOutlined } from '@ant-design/icons';
import CinematicLegacyShell from '../components/CinematicLegacyShell';
import { apiUrl } from '../lib/api';

interface Job {
  job_id: string;
  title: string;
  company: string;
  salary: string;
  location: string;
  experience: string;
  education: string;
  description: string;
  skills: string[];
  welfare: string[];
}

const OpenClawSearch: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedJobs, setSelectedJobs] = useState<string[]>([]);
  const [openclawAvailable, setOpenclawAvailable] = useState(false);
  const [source, setSource] = useState('');

  useEffect(() => {
    checkOpenClawStatus();
  }, []);

  const checkOpenClawStatus = async () => {
    try {
      const response = await fetch(apiUrl('/api/openclaw/status'));
      const result = await response.json();
      setOpenclawAvailable(result.available);
    } catch (error) {
      console.error('检查 OpenClaw 状态失败', error);
    }
  };

  const onSearch = async (values: any) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('keywords', values.keywords || '');
      params.set('location', values.location || '全国');
      params.set('salary_min', String(values.salary_min || 0));
      params.set('limit', String(values.limit || 50));
      const response = await fetch(apiUrl(`/api/openclaw/search?${params.toString()}`));
      const result = await response.json();
      setJobs(result.jobs || []);
      setSource(result.source || result.provider || '');
      setSelectedJobs([]);

      if (result.jobs && result.jobs.length > 0) {
        message.success(`找到 ${result.jobs.length} 个岗位`);
      } else {
        message.info('未找到匹配的岗位');
      }
    } catch (error) {
      console.error('搜索失败', error);
      message.error('搜索失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectJob = (jobId: string, checked: boolean) => {
    if (checked) {
      setSelectedJobs([...selectedJobs, jobId]);
    } else {
      setSelectedJobs(selectedJobs.filter((id) => id !== jobId));
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedJobs(jobs.map((job) => job.job_id));
    } else {
      setSelectedJobs([]);
    }
  };

  return (
    <CinematicLegacyShell
      sectionId="openclaw"
      title="OpenClaw 搜索"
      highlight="真实页面抓取"
      subtitle="这里优先走 OpenClaw 和真实页面读取，不再只是静态搜索框。你看到的是可执行的岗位源，不是假的看板。"
      terminalLabel="OpenClaw_Search::Terminal"
      terminalPrompt={openclawAvailable ? '正在连接真实岗位页面与浏览器会话...' : 'OpenClaw 未连接，等待接入真实环境...'}
      primaryCta="刷新 OpenClaw 状态"
      onPrimaryClick={checkOpenClawStatus}
      terminalLines={[
        { time: '11:06:01', level: 'CHECK', text: 'Checking OpenClaw extension and browser bridge...' },
        { time: '11:06:04', level: 'SOURCE', text: openclawAvailable ? 'Real page source available.' : 'Fallback or simulated source likely.' },
        { time: '11:06:09', level: 'READY', text: 'Search surface ready for operator input.' },
      ]}
    >
      <div className="space-y-6">
        <Alert
          message={openclawAvailable ? 'OpenClaw 已连接' : 'OpenClaw 未连接'}
          description={openclawAvailable ? '当前可优先读取真实岗位页面。' : '当前可能回退到模拟或非 OpenClaw 数据源。'}
          type={openclawAvailable ? 'success' : 'warning'}
          showIcon
          style={{ background: 'rgba(34,211,238,0.08)', borderColor: 'rgba(34,211,238,0.25)', color: '#e0f2fe' }}
        />

        <Card className="glass-panel" styles={{ body: { padding: 24 } }}>
          <Form layout="inline" onFinish={onSearch}>
            <Form.Item name="keywords" label="关键词" rules={[{ required: true, message: '请输入关键词' }]}>
              <Input placeholder="例如：Python 工程师" prefix={<SearchOutlined />} style={{ width: 220 }} />
            </Form.Item>
            <Form.Item name="location" label="地点" initialValue="全国">
              <Input placeholder="例如：北京" prefix={<EnvironmentOutlined />} style={{ width: 150 }} />
            </Form.Item>
            <Form.Item name="salary_min" label="最低薪资">
              <Input placeholder="例如：15" prefix={<DollarOutlined />} suffix="K" type="number" style={{ width: 120 }} />
            </Form.Item>
            <Form.Item name="limit" label="数量" initialValue={50}>
              <Input type="number" style={{ width: 80 }} />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading}>搜索</Button>
            </Form.Item>
          </Form>
        </Card>

        {jobs.length > 0 ? (
          <>
            <Card className="glass-panel" styles={{ body: { padding: 20 } }}>
              <Space>
                <Checkbox checked={selectedJobs.length === jobs.length} indeterminate={selectedJobs.length > 0 && selectedJobs.length < jobs.length} onChange={(e) => handleSelectAll(e.target.checked)}>
                  全选
                </Checkbox>
                <Button type="primary" icon={<ThunderboltOutlined />} disabled={selectedJobs.length === 0} onClick={() => { const selectedPayload = jobs.filter((job) => selectedJobs.includes(job.job_id)); localStorage.setItem('selectedJobs', JSON.stringify(selectedPayload)); message.info('请前往工作台继续批量执行'); window.location.href = '/auto-apply'; }}>
                  批量投递 ({selectedJobs.length})
                </Button>
                {source ? <Tag color={source === 'openclaw' ? 'green' : 'orange'}>{source}</Tag> : null}
                <Badge count={openclawAvailable ? '可用' : '未连接'} style={{ backgroundColor: openclawAvailable ? '#22c55e' : '#ef4444' }} />
              </Space>
            </Card>

            <List
              dataSource={jobs}
              renderItem={(job) => (
                <List.Item>
                  <Card className="glass-panel w-full" hoverable extra={<Checkbox checked={selectedJobs.includes(job.job_id)} onChange={(e) => handleSelectJob(job.job_id, e.target.checked)} />}>
                    <h3>{job.title}</h3>
                    <Space size="large" style={{ marginBottom: 8 }}>
                      <span>{job.company}</span>
                      <Tag color="blue">{job.salary}</Tag>
                      <Tag icon={<EnvironmentOutlined />}>{job.location}</Tag>
                    </Space>
                    <div style={{ marginTop: 8 }}>
                      <Tag>{job.experience}</Tag>
                      <Tag>{job.education}</Tag>
                      {job.skills.map((skill, i) => <Tag key={i} color="cyan">{skill}</Tag>)}
                    </div>
                    {job.welfare.length > 0 ? <div style={{ marginTop: 8 }}>{job.welfare.map((w, i) => <Tag key={i} color="green">{w}</Tag>)}</div> : null}
                    <p style={{ marginTop: 12, color: '#cfefff' }}>{job.description.substring(0, 150)}...</p>
                  </Card>
                </List.Item>
              )}
            />
          </>
        ) : null}
      </div>
    </CinematicLegacyShell>
  );
};

export default OpenClawSearch;

