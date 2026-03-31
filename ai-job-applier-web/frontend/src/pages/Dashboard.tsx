import React, { useEffect, useState } from 'react';
import { Card, Col, Row, Spin, Statistic, Table, Tag, message } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined, SendOutlined } from '@ant-design/icons';
import { apiUrl, authFetch } from '../utils/network';

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
  created_at: string;
}

interface FunnelKpi {
  leads_total: number;
  events_total: number;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<Stats>({ total: 0, success: 0, failed: 0, pending: 0, success_rate: 0 });
  const [recentRecords, setRecentRecords] = useState<RecordItem[]>([]);
  const [funnelKpi, setFunnelKpi] = useState<FunnelKpi>({ leads_total: 0, events_total: 0 });
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsResp, recordsResp, kpiResp] = await Promise.all([
        authFetch('/api/records/stats'),
        authFetch('/api/records?limit=5'),
        fetch(apiUrl('/api/kpi/summary')),
      ]);

      const statsData = await statsResp.json();
      const recordsData = await recordsResp.json();
      const kpiData = await kpiResp.json();

      if (!statsResp.ok || !statsData.success) {
        throw new Error(statsData.detail || statsData.message || '统计加载失败');
      }
      if (!recordsResp.ok || !recordsData.success) {
        throw new Error(recordsData.detail || recordsData.message || '记录加载失败');
      }

      setStats(statsData.stats || statsData);
      setRecentRecords(recordsData.records || []);
      if (kpiResp.ok && kpiData?.success && kpiData?.kpi) {
        setFunnelKpi({
          leads_total: Number(kpiData.kpi.leads_total || 0),
          events_total: Number(kpiData.kpi.events_total || 0),
        });
      }
    } catch (error: any) {
      message.error(error?.message || '仪表盘加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadData();
  }, []);

  const columns = [
    { title: '岗位', dataIndex: 'job_title', key: 'job_title' },
    { title: '公司', dataIndex: 'company', key: 'company' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colorMap: Record<string, string> = { success: 'green', failed: 'red', pending: 'orange' };
        const textMap: Record<string, string> = { success: '成功', failed: '失败', pending: '待处理' };
        return <Tag color={colorMap[status]}>{textMap[status] || status}</Tag>;
      },
    },
    {
      title: '投递时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => new Date(time).toLocaleString('zh-CN'),
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  return (
    <div>
      <h1>仪表盘</h1>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="总投递数" value={stats.total} prefix={<SendOutlined />} valueStyle={{ color: '#1890ff' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="成功投递" value={stats.success} prefix={<CheckCircleOutlined />} valueStyle={{ color: '#52c41a' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="失败投递" value={stats.failed} prefix={<CloseCircleOutlined />} valueStyle={{ color: '#ff4d4f' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="成功率"
              value={stats.success_rate}
              suffix="%"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card>
            <Statistic title="留资总数" value={funnelKpi.leads_total} valueStyle={{ color: '#2563eb' }} />
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <Statistic title="事件总数" value={funnelKpi.events_total} valueStyle={{ color: '#7c3aed' }} />
          </Card>
        </Col>
      </Row>

      <Card title="最近投递记录" style={{ marginTop: 24 }}>
        <Table dataSource={recentRecords} columns={columns} rowKey="id" pagination={false} />
      </Card>
    </div>
  );
};

export default Dashboard;
