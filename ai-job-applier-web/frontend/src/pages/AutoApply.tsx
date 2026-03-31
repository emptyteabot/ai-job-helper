import React from 'react';
import { Button, Card, Input, Progress, Space, Switch, message } from 'antd';
import { getToken, wsUrl } from '../utils/network';

const { TextArea } = Input;

const AutoApply: React.FC = () => {
  const [progress, setProgress] = React.useState(0);
  const [logs, setLogs] = React.useState<string[]>([]);
  const [isRunning, setIsRunning] = React.useState(false);
  const [resumeText, setResumeText] = React.useState('');
  const [useAI, setUseAI] = React.useState(true);
  const [selectedJobs, setSelectedJobs] = React.useState<string[]>([]);

  React.useEffect(() => {
    const jobs = localStorage.getItem('selectedJobs');
    if (jobs) {
      try {
        setSelectedJobs(JSON.parse(jobs));
      } catch {
        setSelectedJobs([]);
      }
    }
  }, []);

  const startApply = async () => {
    if (selectedJobs.length === 0) {
      message.warning('请先在岗位搜索页面选择岗位');
      return;
    }
    if (!resumeText.trim()) {
      message.warning('请输入简历内容');
      return;
    }

    setIsRunning(true);
    setProgress(0);
    setLogs([]);

    try {
      const ws = new WebSocket(wsUrl('/api/apply/ws/apply'));

      ws.onopen = () => {
        ws.send(
          JSON.stringify({
            token: getToken(),
            job_ids: selectedJobs,
            resume_text: resumeText,
            use_ai_cover_letter: useAI,
          })
        );
        setLogs((prev) => [...prev, '开始批量投递...']);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.error) {
          message.error(data.message || '投递失败');
          setLogs((prev) => [...prev, `错误: ${data.message || '未知错误'}`]);
          setIsRunning(false);
          ws.close();
          return;
        }

        if (data.completed || data.stage === 'completed') {
          message.success(data.message || '投递完成');
          setLogs((prev) => [...prev, `完成: ${data.message || '投递结束'}`]);
          setProgress(100);
          setIsRunning(false);
          localStorage.removeItem('selectedJobs');
          ws.close();
          return;
        }

        if (typeof data.progress === 'number') {
          const raw = data.progress > 1 ? data.progress : data.progress * 100;
          setProgress(Math.min(100, Math.max(0, Math.round(raw))));
        }

        if (data.job) {
          const status = data.success ? '成功' : '失败';
          setLogs((prev) => [...prev, `[${data.current}/${data.total}] ${data.company} - ${data.job} ${status}`]);
        } else if (data.message) {
          setLogs((prev) => [...prev, data.message]);
        }
      };

      ws.onerror = () => {
        message.error('连接失败，请稍后重试');
        setIsRunning(false);
        setLogs((prev) => [...prev, '错误: WebSocket 连接失败']);
      };

      ws.onclose = () => {
        setIsRunning(false);
      };
    } catch (error: any) {
      message.error(error?.message || '投递失败');
      setIsRunning(false);
    }
  };

  return (
    <div>
      <h1>批量自动投递</h1>

      <Card style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <strong>已选岗位:</strong> {selectedJobs.length} 个
          </div>

          <div>
            <strong>简历内容:</strong>
            <TextArea
              rows={6}
              placeholder="粘贴简历内容，用于生成个性化沟通语"
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              disabled={isRunning}
            />
          </div>

          <Space>
            <strong>使用 AI 生成求职信:</strong>
            <Switch checked={useAI} onChange={setUseAI} disabled={isRunning} />
          </Space>
        </Space>
      </Card>

      <Card style={{ marginBottom: 16 }}>
        <Progress percent={progress} status={isRunning ? 'active' : 'normal'} />
        <Button
          type="primary"
          onClick={startApply}
          disabled={isRunning || selectedJobs.length === 0}
          style={{ marginTop: 16 }}
          size="large"
        >
          {isRunning ? '投递中...' : `开始投递 (${selectedJobs.length} 个岗位)`}
        </Button>
      </Card>

      <Card title="投递日志">
        <div style={{ maxHeight: 400, overflow: 'auto', fontFamily: 'monospace' }}>
          {logs.length === 0 ? (
            <div style={{ color: '#94a3b8' }}>暂无日志</div>
          ) : (
            logs.map((log, index) => (
              <div key={index} style={{ padding: '4px 0' }}>
                {log}
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
};

export default AutoApply;
