import React, { useEffect, useState } from 'react';
import { Alert, Badge, Button, Card, Checkbox, Form, Input, List, Space, Tag, message } from 'antd';
import { DollarOutlined, EnvironmentOutlined, SearchOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { authFetch } from '../utils/network';

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
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedJobs, setSelectedJobs] = useState<string[]>([]);
  const [openclawAvailable, setOpenclawAvailable] = useState(false);
  const [source, setSource] = useState('mock');

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const response = await authFetch('/api/openclaw/status');
        const result = await response.json();
        setOpenclawAvailable(Boolean(result.available));
      } catch {
        setOpenclawAvailable(false);
      }
    };
    void loadStatus();
  }, []);

  const onSearch = async (values: any) => {
    setLoading(true);
    try {
      const response = await authFetch('/api/openclaw/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      });
      const result = await response.json();
      if (!response.ok || !result.success) {
        throw new Error(result.detail || result.message || '搜索失败');
      }

      setJobs(result.jobs || []);
      setSource(result.source || 'mock');
      setSelectedJobs([]);
      message.success(`找到 ${(result.jobs || []).length} 个岗位（${result.source === 'openclaw' ? '真实数据' : '模拟数据'}）`);
    } catch (error: any) {
      message.error(error?.message || 'OpenClaw 搜索失败');
    } finally {
      setLoading(false);
    }
  };

  const toggleJob = (jobId: string, checked: boolean) => {
    setSelectedJobs((prev) => (checked ? [...prev, jobId] : prev.filter((id) => id !== jobId)));
  };

  const selectAll = (checked: boolean) => {
    setSelectedJobs(checked ? jobs.map((job) => job.job_id) : []);
  };

  const toApply = () => {
    localStorage.setItem('selectedJobs', JSON.stringify(selectedJobs));
    message.success(`已带入 ${selectedJobs.length} 个岗位到批量投递`);
    navigate('/auto-apply');
  };

  return (
    <div>
      <h1>
        OpenClaw 岗位搜索
        <Badge
          count={openclawAvailable ? '可用' : '不可用'}
          style={{ backgroundColor: openclawAvailable ? '#16a34a' : '#ef4444', marginLeft: 12 }}
        />
      </h1>

      <Alert
        message={openclawAvailable ? 'OpenClaw 已连接' : 'OpenClaw 未连接'}
        description={
          openclawAvailable
            ? '当前将优先使用真实岗位抓取结果。'
            : '当前返回模拟数据。部署真实抓取器后可切换为真实数据。'
        }
        type={openclawAvailable ? 'success' : 'warning'}
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Card style={{ marginBottom: 16 }}>
        <Form layout="inline" onFinish={onSearch} initialValues={{ location: '全国', limit: 50 }}>
          <Form.Item name="keywords" label="关键词" rules={[{ required: true, message: '请输入关键词' }]}>
            <Input placeholder="例如：Python工程师" prefix={<SearchOutlined />} style={{ width: 220 }} />
          </Form.Item>
          <Form.Item name="location" label="地点">
            <Input placeholder="例如：北京" prefix={<EnvironmentOutlined />} style={{ width: 140 }} />
          </Form.Item>
          <Form.Item name="salary_min" label="最低薪资(K)">
            <Input placeholder="例如：15" prefix={<DollarOutlined />} type="number" style={{ width: 120 }} />
          </Form.Item>
          <Form.Item name="limit" label="数量">
            <Input type="number" style={{ width: 90 }} min={1} max={100} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>搜索</Button>
          </Form.Item>
        </Form>
      </Card>

      {jobs.length > 0 && (
        <Card style={{ marginBottom: 16 }}>
          <Space>
            <Checkbox
              checked={selectedJobs.length === jobs.length}
              indeterminate={selectedJobs.length > 0 && selectedJobs.length < jobs.length}
              onChange={(e) => selectAll(e.target.checked)}
            >
              全选
            </Checkbox>
            <Button type="primary" icon={<ThunderboltOutlined />} disabled={!selectedJobs.length} onClick={toApply}>
              批量投递 ({selectedJobs.length})
            </Button>
            <Tag color={source === 'openclaw' ? 'green' : 'orange'}>
              {source === 'openclaw' ? '真实数据' : '模拟数据'}
            </Tag>
          </Space>
        </Card>
      )}

      <List
        dataSource={jobs}
        renderItem={(job) => (
          <List.Item>
            <Card
              style={{ width: '100%' }}
              hoverable
              extra={<Checkbox checked={selectedJobs.includes(job.job_id)} onChange={(e) => toggleJob(job.job_id, e.target.checked)} />}
            >
              <h3>{job.title}</h3>
              <Space size="large" style={{ marginBottom: 8 }}>
                <span>{job.company}</span>
                <Tag color="blue">{job.salary}</Tag>
                <Tag icon={<EnvironmentOutlined />}>{job.location}</Tag>
              </Space>
              <Space size={[4, 8]} wrap>
                <Tag>{job.experience}</Tag>
                <Tag>{job.education}</Tag>
                {(job.skills || []).map((skill) => (
                  <Tag key={skill} color="cyan">{skill}</Tag>
                ))}
                {(job.welfare || []).map((w) => (
                  <Tag key={w} color="green">{w}</Tag>
                ))}
              </Space>
              <p style={{ marginTop: 12, color: '#64748b' }}>{job.description.substring(0, 150)}...</p>
            </Card>
          </List.Item>
        )}
      />
    </div>
  );
};

export default OpenClawSearch;
