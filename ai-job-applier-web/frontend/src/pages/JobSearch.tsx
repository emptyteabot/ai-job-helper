import React, { useState } from 'react';
import { Button, Card, Checkbox, Empty, Form, Input, List, Space, Tag, message } from 'antd';
import { DollarOutlined, EnvironmentOutlined, SearchOutlined } from '@ant-design/icons';
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
  url: string;
}

const JobSearch: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedJobs, setSelectedJobs] = useState<string[]>([]);

  const onSearch = async (values: any) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('keyword', values.keywords || '');
      params.set('city', values.location || '全国');
      params.set('max_count', String(values.limit || 20));
      const response = await fetch(apiUrl(`/api/jobs/search?${params.toString()}`));
      const result = await response.json();
      setJobs(result.jobs || []);
      setSelectedJobs([]);
      if (result.jobs && result.jobs.length > 0) {
        message.success(`找到 ${result.jobs.length} 个岗位`);
      } else {
        message.info('未找到匹配的岗位');
      }
    } catch (error) {
      console.error('搜索失败', error);
      message.error('搜索失败，请检查是否已登录');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectJob = (jobId: string, checked: boolean) => {
    if (checked) setSelectedJobs([...selectedJobs, jobId]);
    else setSelectedJobs(selectedJobs.filter((id) => id !== jobId));
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) setSelectedJobs(jobs.map((job) => job.job_id));
    else setSelectedJobs([]);
  };

  const handleBatchApply = () => {
    if (selectedJobs.length === 0) {
      message.warning('请先选择要投递的岗位');
      return;
    }
    const selectedPayload = jobs.filter((job) => selectedJobs.includes(job.job_id));
    localStorage.setItem('selectedJobs', JSON.stringify(selectedPayload));
    message.success(`已选择 ${selectedJobs.length} 个岗位`);
    window.location.href = '/auto-apply';
  };

  return (
    <CinematicLegacyShell
      sectionId="jobsearch"
      title="岗位搜索"
      highlight="批量筛选入口"
      subtitle="旧搜索页也必须进入同一套终端母版里：先搜、再选、再批量推进，不再像后台表单页。"
      terminalLabel="JobSearch::Terminal"
      terminalPrompt={loading ? '正在扫描岗位来源与匹配条件...' : '输入关键词，开始一轮岗位扫描...'}
      primaryCta="开始搜索"
      terminalLines={[
        { time: '10:21:01', level: 'QUERY', text: 'Waiting for keywords, location and salary filters...' },
        { time: '10:21:05', level: 'SCAN', text: `Current selected jobs: ${selectedJobs.length}` },
        { time: '10:21:09', level: 'READY', text: 'Search surface is ready.' },
      ]}
    >
      <div className="space-y-6">
        <Card className="glass-panel" styles={{ body: { padding: 24 } }}>
          <Form layout="inline" onFinish={onSearch}>
            <Form.Item name="keywords" label="关键词" rules={[{ required: true, message: '请输入关键词' }]}>
              <Input placeholder="例如：Python 实习" prefix={<SearchOutlined />} style={{ width: 220 }} />
            </Form.Item>
            <Form.Item name="location" label="地点">
              <Input placeholder="例如：北京" prefix={<EnvironmentOutlined />} style={{ width: 150 }} />
            </Form.Item>
            <Form.Item name="salary_min" label="最低薪资">
              <Input placeholder="例如：5000" prefix={<DollarOutlined />} type="number" style={{ width: 120 }} />
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
                <Button type="primary" disabled={selectedJobs.length === 0} onClick={handleBatchApply}>
                  批量投递 ({selectedJobs.length})
                </Button>
              </Space>
            </Card>
            <List dataSource={jobs} renderItem={(job) => (
              <List.Item>
                <Card className="glass-panel w-full" hoverable extra={<Checkbox checked={selectedJobs.includes(job.job_id)} onChange={(e) => handleSelectJob(job.job_id, e.target.checked)} />}>
                  <h3>{job.title}</h3>
                  <Space size="large" style={{ marginBottom: 8 }}>
                    <span>{job.company}</span>
                    <Tag color="blue">{job.salary}</Tag>
                    <Tag icon={<EnvironmentOutlined />}>{job.location}</Tag>
                  </Space>
                  <div style={{ marginTop: 8 }}><Tag>{job.experience}</Tag><Tag>{job.education}</Tag></div>
                  <p style={{ marginTop: 12, color: '#cfefff' }}>{job.description.substring(0, 100)}...</p>
                </Card>
              </List.Item>
            )} />
          </>
        ) : <Empty description="暂无搜索结果" />}
      </div>
    </CinematicLegacyShell>
  );
};

export default JobSearch;

