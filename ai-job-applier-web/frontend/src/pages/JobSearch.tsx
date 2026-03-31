import React, { useState } from 'react';
import { Button, Card, Checkbox, Empty, Form, Input, List, Space, Tag, message } from 'antd';
import { DollarOutlined, EnvironmentOutlined, SearchOutlined } from '@ant-design/icons';
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
  url?: string;
}

const JobSearch: React.FC = () => {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedJobs, setSelectedJobs] = useState<string[]>([]);

  const onSearch = async (values: any) => {
    setLoading(true);
    try {
      const response = await authFetch('/api/jobs/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      });
      const result = await response.json();
      if (!response.ok || !result.success) {
        throw new Error(result.detail || result.message || '搜索失败');
      }

      const nextJobs = result.jobs || [];
      setJobs(nextJobs);
      setSelectedJobs([]);

      if (nextJobs.length > 0) {
        message.success(`找到 ${nextJobs.length} 个岗位`);
      } else {
        message.info('未找到匹配岗位，请调整关键词');
      }
    } catch (error: any) {
      message.error(error?.message || '岗位搜索失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectJob = (jobId: string, checked: boolean) => {
    setSelectedJobs((prev) => (checked ? [...prev, jobId] : prev.filter((id) => id !== jobId)));
  };

  const handleSelectAll = (checked: boolean) => {
    setSelectedJobs(checked ? jobs.map((job) => job.job_id) : []);
  };

  const handleBatchApply = () => {
    if (!selectedJobs.length) {
      message.warning('请先选择要投递的岗位');
      return;
    }
    localStorage.setItem('selectedJobs', JSON.stringify(selectedJobs));
    message.success(`已选择 ${selectedJobs.length} 个岗位，进入批量投递`);
    navigate('/auto-apply');
  };

  return (
    <div>
      <h1>岗位搜索</h1>

      <Card style={{ marginBottom: 16 }}>
        <Form layout="inline" onFinish={onSearch} initialValues={{ location: '全国', limit: 20 }}>
          <Form.Item name="keywords" label="关键词" rules={[{ required: true, message: '请输入关键词' }]}>
            <Input placeholder="例如：Python实习" prefix={<SearchOutlined />} style={{ width: 220 }} />
          </Form.Item>
          <Form.Item name="location" label="地点">
            <Input placeholder="例如：北京" prefix={<EnvironmentOutlined />} style={{ width: 150 }} />
          </Form.Item>
          <Form.Item name="salary_min" label="最低薪资(K)">
            <Input placeholder="例如：15" prefix={<DollarOutlined />} type="number" style={{ width: 130 }} />
          </Form.Item>
          <Form.Item name="limit" label="数量">
            <Input type="number" min={1} max={100} style={{ width: 100 }} />
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
              onChange={(e) => handleSelectAll(e.target.checked)}
            >
              全选
            </Checkbox>
            <Button type="primary" disabled={!selectedJobs.length} onClick={handleBatchApply}>
              批量投递 ({selectedJobs.length})
            </Button>
          </Space>
        </Card>
      )}

      {jobs.length === 0 ? (
        <Empty description="暂无搜索结果" />
      ) : (
        <List
          dataSource={jobs}
          renderItem={(job) => (
            <List.Item>
              <Card
                style={{ width: '100%' }}
                hoverable
                extra={
                  <Checkbox
                    checked={selectedJobs.includes(job.job_id)}
                    onChange={(e) => handleSelectJob(job.job_id, e.target.checked)}
                  />
                }
              >
                <h3>{job.title}</h3>
                <Space size="large" style={{ marginBottom: 8 }}>
                  <span>{job.company}</span>
                  <Tag color="blue">{job.salary}</Tag>
                  <Tag icon={<EnvironmentOutlined />}>{job.location}</Tag>
                </Space>
                <div style={{ marginTop: 8 }}>
                  <Tag>{job.experience}</Tag>
                  <Tag>{job.education}</Tag>
                </div>
                <p style={{ marginTop: 12, color: '#64748b' }}>{job.description.substring(0, 140)}...</p>
                {job.url && (
                  <a href={job.url} target="_blank" rel="noreferrer">
                    查看原始链接
                  </a>
                )}
              </Card>
            </List.Item>
          )}
        />
      )}
    </div>
  );
};

export default JobSearch;
