import React, { useEffect, useState } from 'react';
import { Button, Card, Form, Input, List, message } from 'antd';
import CinematicLegacyShell from '../components/CinematicLegacyShell';
import { apiUrl, authHeaders } from '../lib/api';

interface ChallengeSession {
  id: string;
  title?: string;
  provider?: string;
  state?: string;
  message?: string;
  current_url?: string;
  target_url?: string;
  screenshot_path?: string;
  updated_at?: string;
  metadata?: Record<string, any>;
}

const ChallengeCenter: React.FC = () => {
  const [sessions, setSessions] = useState<ChallengeSession[]>([]);
  const [active, setActive] = useState<ChallengeSession | null>(null);
  const [starting, setStarting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [resuming, setResuming] = useState(false);
  const [interacting, setInteracting] = useState(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number } | null>(null);

  const loadSessions = async () => {
    try {
      const response = await fetch(apiUrl('/api/challenges'), {
        headers: authHeaders(),
      });
      const payload = await response.json();
      const rows = payload.sessions || [];
      setSessions(rows);
      if (!active && rows.length) setActive(rows[0]);
    } catch (error) {
      console.error('load challenge sessions failed', error);
    }
  };

  const refreshSession = async (sessionId: string) => {
    const response = await fetch(apiUrl(`/api/challenges/${sessionId}/refresh`), {
      method: 'POST',
      headers: authHeaders(),
    });
    const payload = await response.json();
    if (payload.session) {
      setActive(payload.session);
      await loadSessions();
    }
  };

  const startBossSession = async (payload?: { keyword?: string; city?: string; max_count?: string | number }) => {
    setStarting(true);
    try {
      const keyword = payload?.keyword || 'python';
      const city = payload?.city || '全国';
      const maxCount = Number(payload?.max_count || 10);
      const response = await fetch(apiUrl(`/api/boss/challenge/start?keyword=${encodeURIComponent(keyword)}&city=${encodeURIComponent(city)}&max_count=${maxCount}`), {
        method: 'POST',
        headers: authHeaders(),
      });
      const payload = await response.json();
      if (payload.session) {
        setActive(payload.session);
        await loadSessions();
        message.success('Challenge 会话已创建');
      } else {
        message.error(payload.detail || payload.message || '创建 challenge 会话失败');
      }
    } catch (error) {
      message.error('创建 challenge 会话失败');
    } finally {
      setStarting(false);
    }
  };

  const submitCode = async (values: { code: string }) => {
    if (!active?.id) return;
    setSubmitting(true);
    try {
      const response = await fetch(apiUrl(`/api/challenges/${active.id}/submit`), {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ code: values.code }),
      });
      const payload = await response.json();
      if (payload.session) {
        setActive(payload.session);
        await loadSessions();
        message.success('验证码已提交');
      } else {
        message.error(payload.detail || payload.message || '提交失败');
      }
    } catch (error) {
      message.error('提交失败');
    } finally {
      setSubmitting(false);
    }
  };

  const sendClick = async (x: number, y: number, imageWidth: number, imageHeight: number) => {
    if (!active?.id) return;
    setInteracting(true);
    try {
      const response = await fetch(apiUrl(`/api/challenges/${active.id}/click`), {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ x, y, image_width: imageWidth, image_height: imageHeight }),
      });
      const payload = await response.json();
      if (payload.session) {
        setActive(payload.session);
        await loadSessions();
      }
    } finally {
      setInteracting(false);
    }
  };

  const sendDrag = async (
    fromX: number,
    fromY: number,
    toX: number,
    toY: number,
    imageWidth: number,
    imageHeight: number,
  ) => {
    if (!active?.id) return;
    setInteracting(true);
    try {
      const response = await fetch(apiUrl(`/api/challenges/${active.id}/drag`), {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({
          from_x: fromX,
          from_y: fromY,
          to_x: toX,
          to_y: toY,
          image_width: imageWidth,
          image_height: imageHeight,
          steps: 20,
        }),
      });
      const payload = await response.json();
      if (payload.session) {
        setActive(payload.session);
        await loadSessions();
      }
    } finally {
      setInteracting(false);
    }
  };

  const closeSession = async () => {
    if (!active?.id) return;
    try {
      const response = await fetch(apiUrl(`/api/challenges/${active.id}/close`), {
        method: 'POST',
        headers: authHeaders(),
      });
      const payload = await response.json();
      if (payload.session) {
        setActive(payload.session);
        await loadSessions();
        message.success('会话已关闭');
      }
    } catch (error) {
      message.error('关闭会话失败');
    }
  };

  const resumeBossSession = async () => {
    if (!active?.id) return;
    setResuming(true);
    try {
      const response = await fetch(apiUrl(`/api/boss/challenge/${active.id}/resume`), {
        method: 'POST',
        headers: authHeaders(),
      });
      const payload = await response.json();
      if (payload.result) {
        message.success(payload.result.message || 'Boss 执行已恢复');
        await loadSessions();
      } else {
        message.error(payload.detail || payload.message || '恢复执行失败');
      }
    } catch (error) {
      message.error('恢复执行失败');
    } finally {
      setResuming(false);
    }
  };

  useEffect(() => {
    void loadSessions();
  }, []);

  useEffect(() => {
    const search = new URLSearchParams(window.location.search);
    if (search.get('provider') === 'boss' && search.get('autostart') === '1') {
      void startBossSession({
        keyword: search.get('keyword') || 'python',
        city: search.get('city') || '全国',
        max_count: search.get('max_count') || '10',
      });
    }
  }, []);

  useEffect(() => {
    if (!active?.id) return;
    const timer = window.setInterval(() => {
      void refreshSession(active.id);
    }, 4000);
    return () => window.clearInterval(timer);
  }, [active?.id]);

  const getRelativePoint = (
    event: React.MouseEvent<HTMLImageElement>,
  ): { x: number; y: number; width: number; height: number } => {
    const rect = event.currentTarget.getBoundingClientRect();
    return {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
      width: rect.width,
      height: rect.height,
    };
  };

  return (
    <CinematicLegacyShell
      sectionId="challenge-center"
      title="Challenge Center"
      highlight="人工接管控制台"
      subtitle="云端 Playwright 会话在这里暂停、截图、等待验证码输入，然后恢复执行。这里不是说明页，而是接管中心。"
      terminalLabel="Challenge_Center::Terminal"
      terminalPrompt={active ? `当前会话状态：${active.state || 'unknown'}` : '暂无 challenge 会话，等待创建...'}
      primaryCta={starting ? '创建中...' : '新建 Boss Challenge 会话'}
      onPrimaryClick={() => void startBossSession()}
      terminalLines={[
        { time: '11:30:01', level: 'STATE', text: active?.state || 'idle' },
        { time: '11:30:05', level: 'URL', text: active?.current_url || active?.target_url || 'no active url' },
        { time: '11:30:09', level: 'MESSAGE', text: active?.message || 'waiting for challenge session' },
      ]}
    >
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <Card className="glass-panel" styles={{ body: { padding: 24 } }}>
          <div className="mb-4 text-cyan-100 text-xl font-bold">会话列表</div>
          <List
            dataSource={sessions}
            locale={{ emptyText: '暂无 challenge 会话' }}
            renderItem={(item) => (
              <List.Item
                style={{ cursor: 'pointer' }}
                onClick={() => setActive(item)}
              >
                <div className="w-full">
                  <div className="font-bold text-cyan-100">{item.title || item.id}</div>
                  <div className="text-cyan-100/60 text-sm">{item.state} · {item.updated_at || ''}</div>
                </div>
              </List.Item>
            )}
          />
        </Card>

        <div className="space-y-6">
          <Card className="glass-panel" styles={{ body: { padding: 24 } }}>
            <div className="mb-4 flex items-center justify-between">
              <div>
                <div className="text-cyan-100 text-xl font-bold">{active?.title || '未选择会话'}</div>
                <div className="text-cyan-100/60 text-sm">{active?.message || '请选择或新建一个 challenge 会话'}</div>
              </div>
              {active?.id ? (
                <div className="flex gap-3">
                  {active.provider?.includes('boss') && ['ready', 'resumed'].includes(active.state || '') ? (
                    <Button type="primary" loading={resuming} onClick={resumeBossSession}>恢复 Boss 执行</Button>
                  ) : null}
                  <Button onClick={() => refreshSession(active.id)}>刷新</Button>
                  <Button danger onClick={closeSession}>关闭</Button>
                </div>
              ) : null}
            </div>
            {active?.id ? (
              <img
                alt="challenge screenshot"
                className="w-full rounded-xl border border-cyan-400/20 cursor-crosshair"
                src={apiUrl(`/api/challenges/${active.id}/screenshot`)}
                onMouseDown={(event) => {
                  const point = getRelativePoint(event);
                  setDragStart({ x: point.x, y: point.y });
                }}
                onMouseUp={async (event) => {
                  const point = getRelativePoint(event);
                  const moved = dragStart && (Math.abs(point.x - dragStart.x) > 12 || Math.abs(point.y - dragStart.y) > 12);
                  if (dragStart && moved) {
                    await sendDrag(dragStart.x, dragStart.y, point.x, point.y, point.width, point.height);
                  } else {
                    await sendClick(point.x, point.y, point.width, point.height);
                  }
                  setDragStart(null);
                }}
              />
            ) : (
              <div className="rounded-xl border border-dashed border-cyan-400/20 p-10 text-center text-cyan-100/50">
                暂无截图
              </div>
            )}
            {active?.id ? (
              <div className="mt-3 text-sm text-cyan-100/60">
                提示：点击截图可触发点击；按住后拖动可用于滑块验证。{interacting ? ' 正在发送交互...' : ''}
              </div>
            ) : null}
          </Card>

          <Card className="glass-panel" styles={{ body: { padding: 24 } }}>
            <div className="mb-4 text-cyan-100 text-lg font-bold">输入验证码 / 人工确认</div>
            <Form onFinish={submitCode} layout="vertical">
              <Form.Item
                label={<span className="text-cyan-100">验证码</span>}
                name="code"
                rules={[{ required: true, message: '请输入验证码' }]}
              >
                <Input placeholder="输入用户在 challenge 中看到的验证码" size="large" />
              </Form.Item>
              <Button type="primary" htmlType="submit" loading={submitting} disabled={!active?.id}>
                提交并恢复会话
              </Button>
            </Form>
          </Card>
        </div>
      </div>
    </CinematicLegacyShell>
  );
};

export default ChallengeCenter;
