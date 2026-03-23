import React from 'react';
import { Button, Table } from 'antd';
import CinematicLegacyShell from '../components/CinematicLegacyShell';
import { apiUrl, authHeaders } from '../lib/api';

const Records: React.FC = () => {
  const [records, setRecords] = React.useState([]);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    loadRecords();
  }, []);

  const loadRecords = async () => {
    setLoading(true);
    try {
      const response = await fetch(apiUrl('/api/records'), { headers: authHeaders() });
      const result = await response.json();
      setRecords(result.records);
    } catch (error) {
      console.error('加载记录失败', error);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: '岗位名称', dataIndex: 'job_title', key: 'job_title' },
    { title: '公司', dataIndex: 'company', key: 'company' },
    { title: '状态', dataIndex: 'status', key: 'status' },
    { title: '投递时间', dataIndex: 'created_at', key: 'created_at' },
  ];

  return (
    <CinematicLegacyShell
      sectionId="records"
      title="投递记录"
      highlight="回流数据库"
      subtitle="所有执行动作最终都要回流成记录。这里不展示营销词，只展示真实发生过的投递轨迹。"
      terminalLabel="Records_Stream::Terminal"
      terminalPrompt="正在同步最近一轮投递与状态变化..."
      primaryCta="刷新记录"
      onPrimaryClick={loadRecords}
      terminalLines={[
        { time: '10:02:01', level: 'LOAD', text: 'Loading application records from local store...' },
        { time: '10:02:04', level: 'SYNC', text: 'Normalizing company, role and created_at fields...' },
        { time: '10:02:09', level: 'READY', text: 'Record table is available for review.' },
      ]}
    >
      <div className="glass-panel rounded-2xl p-8 shadow-[0_0_50px_rgba(34,211,238,0.08)]">
        <div className="mb-6 flex justify-between items-center">
          <div>
            <h3 className="text-2xl font-headline font-bold text-cyan-100">最近执行记录</h3>
            <p className="text-cyan-100/60 mt-2">刷新后可查看最新的岗位、公司、状态和投递时间。</p>
          </div>
          <Button onClick={loadRecords}>刷新</Button>
        </div>
        <Table dataSource={records} columns={columns} loading={loading} rowKey="id" pagination={{ pageSize: 8 }} scroll={{ x: 'max-content' }} />
      </div>
    </CinematicLegacyShell>
  );
};

export default Records;

