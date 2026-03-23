import React, { useEffect, useState } from 'react';
import { Card, Spin, Statistic, Table, Tag } from 'antd';
import { CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined, SendOutlined } from '@ant-design/icons';
import CinematicLegacyShell from '../components/CinematicLegacyShell';
import { apiUrl, authHeaders } from '../lib/api';

interface Stats {
  total: number;
  success: number;
  failed: number;
  pending: number;
  success_rate: number;
}

interface RecordItem {
  id: string;
  job_title: string;
  company: string;
  status: string;
  applied_at: string;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<Stats>({ total: 0, success: 0, failed: 0, pending: 0, success_rate: 0 });
  const [recentRecords, setRecentRecords] = useState<RecordItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const statsResponse = await fetch(apiUrl('/api/records/stats'), { headers: authHeaders() });
      const statsResult = await statsResponse.json();
      setStats({
        total: Number(statsResult.total || 0),
        success: Number(statsResult.success || 0),
        failed: Number(statsResult.failed || 0),
        pending: Number(statsResult.pending || 0),
        success_rate: Number(statsResult.success_rate || 0),
      });
      const recordsResponse = await fetch(apiUrl('/api/records?limit=5'), { headers: authHeaders() });
      const recordsResult = await recordsResponse.json();
      setRecentRecords(recordsResult.records || []);
    } catch (error) {
      console.error('加载数据失败', error);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: '岗位', dataIndex: 'job_title', key: 'job_title' },
    { title: '公司', dataIndex: 'company', key: 'company' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colorMap: any = { success: 'green', failed: 'red', pending: 'orange' };
        const textMap: any = { success: '成功', failed: '失败', pending: '待处理' };
        return <Tag color={colorMap[status]}>{textMap[status]}</Tag>;
      },
    },
    { title: '投递时间', dataIndex: 'applied_at', key: 'applied_at', render: (time: string) => new Date(time).toLocaleString('zh-CN') },
  ];

  return (
    <CinematicLegacyShell
      sectionId="dashboard"
      title="执行看板"
      highlight="全局统计"
      subtitle="这页不该只是老式表格，它应该把总投递、成功率和最近执行记录一起拉成一个可读的运行态面板。"
      terminalLabel="Dashboard::Terminal"
      terminalPrompt={loading ? '正在拉取统计数据与最近记录...' : '统计面板已同步，可继续查看最近结果'}
      primaryCta="刷新看板"
      onPrimaryClick={loadData}
      terminalLines={[
        { time: '10:11:01', level: 'LOAD', text: 'Loading record stats and recent applications...' },
        { time: '10:11:05', level: 'SYNC', text: `Current total applications: ${stats.total}` },
        { time: '10:11:09', level: 'READY', text: 'Dashboard render completed.' },
      ]}
    >
      {loading ? (
        <div className="text-center py-20"><Spin size="large" tip="加载中..." /></div>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card className="glass-panel"><Statistic title="总投递数" value={stats.total} prefix={<SendOutlined />} valueStyle={{ color: '#67e8f9' }} /></Card>
            <Card className="glass-panel"><Statistic title="成功投递" value={stats.success} prefix={<CheckCircleOutlined />} valueStyle={{ color: '#22c55e' }} /></Card>
            <Card className="glass-panel"><Statistic title="失败投递" value={stats.failed} prefix={<CloseCircleOutlined />} valueStyle={{ color: '#f87171' }} /></Card>
            <Card className="glass-panel"><Statistic title="成功率" value={stats.success_rate} suffix="%" prefix={<ClockCircleOutlined />} valueStyle={{ color: '#facc15' }} /></Card>
          </div>
          <Card className="glass-panel" title="最近投递记录" styles={{ header: { color: '#67e8f9' }, body: { padding: 24 } }}>
            <Table dataSource={recentRecords} columns={columns} rowKey="id" pagination={false} scroll={{ x: 'max-content' }} />
          </Card>
        </div>
      )}
    </CinematicLegacyShell>
  );
};

export default Dashboard;

