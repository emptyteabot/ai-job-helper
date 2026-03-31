import React from 'react';
import { Button, Table, Tag, message } from 'antd';
import { authFetch } from '../utils/network';

interface ApplyRecord {
  id: string;
  job_title: string;
  company: string;
  status: string;
  created_at: string;
  source?: string;
}

const statusColor: Record<string, string> = {
  success: 'green',
  failed: 'red',
  pending: 'orange',
};

const Records: React.FC = () => {
  const [records, setRecords] = React.useState<ApplyRecord[]>([]);
  const [loading, setLoading] = React.useState(false);

  const loadRecords = async () => {
    setLoading(true);
    try {
      const response = await authFetch('/api/records?limit=100');
      const result = await response.json();
      if (!response.ok || !result.success) {
        throw new Error(result.detail || result.message || '加载失败');
      }
      setRecords(result.records || []);
    } catch (error: any) {
      message.error(error?.message || '加载记录失败');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    void loadRecords();
  }, []);

  const columns = [
    { title: '岗位名称', dataIndex: 'job_title', key: 'job_title' },
    { title: '公司', dataIndex: 'company', key: 'company' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (value: string) => <Tag color={statusColor[value] || 'default'}>{value}</Tag>,
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      render: (value: string) => value || '-',
    },
    {
      title: '投递时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (value: string) => new Date(value).toLocaleString('zh-CN'),
    },
  ];

  return (
    <div>
      <h1>投递记录</h1>
      <Button onClick={loadRecords} style={{ marginBottom: 16 }} loading={loading}>
        刷新
      </Button>
      <Table dataSource={records} columns={columns} loading={loading} rowKey="id" pagination={{ pageSize: 20 }} />
    </div>
  );
};

export default Records;
