import React, { useEffect, useMemo, useState } from 'react';
import { Button, Card, Form, Input, List, message, Space, Tag } from 'antd';
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
  updated_at?: string;
  metadata?: Record<string, any>;
}

interface FormField {
  field_id: string;
  tag?: string;
  type?: string;
  label?: string;
  name?: string;
  placeholder?: string;
  required?: boolean;
  selector?: string;
  profile_key?: string | null;
  suggested_value?: string;
  status?: string;
  confidence?: number;
}

interface FormPayload {
  fields?: FormField[];
  profile?: Record<string, any>;
  summary?: Record<string, number>;
  filled?: Array<Record<string, any>>;
  skipped?: Array<Record<string, any>>;
}

const ChallengeCenter: React.FC = () => {
  const [sessions, setSessions] = useState<ChallengeSession[]>([]);
  const [active, setActive] = useState<ChallengeSession | null>(null);
  const [autostartHandled, setAutostartHandled] = useState(false);
  const [startingBoss, setStartingBoss] = useState(false);
  const [startingGeneric, setStartingGeneric] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [resuming, setResuming] = useState(false);
  const [interacting, setInteracting] = useState(false);
  const [scanningFields, setScanningFields] = useState(false);
  const [autofilling, setAutofilling] = useState(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number } | null>(null);
  const [code, setCode] = useState('');
  const [genericUrl, setGenericUrl] = useState('');
  const [genericTitle, setGenericTitle] = useState('');
  const [fields, setFields] = useState<FormField[]>([]);
  const [profile, setProfile] = useState<Record<string, any>>({});
  const [fieldSummary, setFieldSummary] = useState<Record<string, number>>({});

  const loadSessions = async () => {
    try {
      const response = await fetch(apiUrl('/api/challenges'), {
        headers: authHeaders(),
      });
      const payload = await response.json();
      const rows = payload.sessions || [];
      setSessions(rows);
      setActive((current) => {
        if (current) {
          const matched = rows.find((item: ChallengeSession) => item.id === current.id);
          return matched || current;
        }
        return rows[0] || null;
      });
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

  const inspectFormFields = async (sessionId: string) => {
    setScanningFields(true);
    try {
      const response = await fetch(apiUrl(`/api/challenges/${sessionId}/form-fields`), {
        headers: authHeaders(),
      });
      const payload = await response.json();
      if (!response.ok || !payload.success) {
        message.error(payload.detail || payload.message || '字段扫描失败');
        return;
      }
      setFields(payload.fields || []);
      setProfile(payload.profile || {});
      setFieldSummary(payload.summary || {});
      if (payload.session) {
        setActive(payload.session);
      }
      await loadSessions();
      message.success(`已识别 ${payload.summary?.total || 0} 个可操作字段`);
    } catch (error) {
      message.error('字段扫描失败');
    } finally {
      setScanningFields(false);
    }
  };

  const autofillFormFields = async () => {
    if (!active?.id) return;
    setAutofilling(true);
    try {
      const response = await fetch(apiUrl(`/api/challenges/${active.id}/autofill`), {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ overrides: {} }),
      });
      const payload: FormPayload & { success?: boolean; session?: ChallengeSession; detail?: string; message?: string } = await response.json();
      if (!response.ok || !payload.success) {
        message.error(payload.detail || payload.message || '自动填写失败');
        return;
      }
      setFields(payload.fields || []);
      setProfile(payload.profile || {});
      setFieldSummary(payload.summary || {});
      if (payload.session) {
        setActive(payload.session);
      }
      await loadSessions();
      const filledCount = payload.summary?.filled || 0;
      const skippedCount = payload.summary?.skipped || 0;
      message.success(`已填写 ${filledCount} 个字段，跳过 ${skippedCount} 个高风险或待复核字段`);
    } catch (error) {
      message.error('自动填写失败');
    } finally {
      setAutofilling(false);
    }
  };

  const startBossSession = async (payload?: { keyword?: string; city?: string; max_count?: string | number }) => {
    setStartingBoss(true);
    try {
      const keyword = payload?.keyword || 'python';
      const city = payload?.city || '全国';
      const maxCount = Number(payload?.max_count || 10);
      const response = await fetch(
        apiUrl(`/api/boss/challenge/start?keyword=${encodeURIComponent(keyword)}&city=${encodeURIComponent(city)}&max_count=${maxCount}`),
        {
          method: 'POST',
          headers: authHeaders(),
        },
      );
      const result = await response.json();
      if (!response.ok || !result.session) {
        message.error(result.detail || result.message || '创建 Boss challenge 会话失败');
        return;
      }
      window.localStorage.setItem('last_boss_session_id', result.session.id);
      setActive(result.session);
      setFields([]);
      setProfile({});
      setFieldSummary({});
      await loadSessions();
      message.success('Boss challenge 会话已创建');
    } catch (error) {
      message.error('创建 Boss challenge 会话失败');
    } finally {
      setStartingBoss(false);
    }
  };

  const startGenericSession = async () => {
    if (!genericUrl.trim()) {
      message.error('请先输入官网投递页面 URL');
      return;
    }
    setStartingGeneric(true);
    try {
      const response = await fetch(apiUrl('/api/challenges/start'), {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({
          url: genericUrl.trim(),
          title: genericTitle.trim() || 'Official Careers Session',
          provider: 'playwright',
        }),
      });
      const payload = await response.json();
      if (!response.ok || !payload.session) {
        message.error(payload.detail || payload.message || '创建官网会话失败');
        return;
      }
      setActive(payload.session);
      setFields([]);
      setProfile({});
      setFieldSummary({});
      await loadSessions();
      message.success('官网投递会话已创建');
    } catch (error) {
      message.error('创建官网会话失败');
    } finally {
      setStartingGeneric(false);
    }
  };

  const submitCode = async () => {
    if (!active?.id) return;
    if (!code.trim()) {
      message.error('请先输入验证码');
      return;
    }
    setSubmitting(true);
    try {
      const response = await fetch(apiUrl(`/api/challenges/${active.id}/submit`), {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ code: code.trim() }),
      });
      const payload = await response.json();
      if (!response.ok || !payload.session) {
        message.error(payload.detail || payload.message || '验证码提交失败');
        return;
      }
      setCode('');
      setActive(payload.session);
      await loadSessions();
      message.success('验证码已提交');
    } catch (error) {
      message.error('验证码提交失败');
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
        setFields([]);
        setProfile({});
        setFieldSummary({});
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
      if (!response.ok) {
        message.error(payload.detail || payload.message || '恢复执行失败');
        return;
      }
      if (payload.requires_human) {
        message.warning(payload.message || '出现新的人工接管节点');
      } else {
        message.success(payload.result?.message || 'Boss 执行已恢复');
      }
      await loadSessions();
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
    const explicitSessionId = search.get('session_id') || window.localStorage.getItem('last_boss_session_id') || '';
    if (explicitSessionId && sessions.length) {
      const matched = sessions.find((item) => item.id === explicitSessionId);
      if (matched) {
        setActive(matched);
        setAutostartHandled(true);
        return;
      }
    }
    if (!autostartHandled && search.get('provider') === 'boss' && search.get('autostart') === '1' && sessions.length) {
      const reusable = sessions.find((item) => item.provider?.includes('boss') && !['closed', 'expired', 'failed'].includes(item.state || ''));
      if (reusable) {
        setActive(reusable);
        window.localStorage.setItem('last_boss_session_id', reusable.id);
        setAutostartHandled(true);
        return;
      }
      setAutostartHandled(true);
      void startBossSession({
        keyword: search.get('keyword') || 'python',
        city: search.get('city') || '全国',
        max_count: search.get('max_count') || '10',
      });
    }
  }, [autostartHandled, sessions]);

  useEffect(() => {
    if (!active?.id) return undefined;
    const timer = window.setInterval(() => {
      void refreshSession(active.id);
    }, 4000);
    return () => window.clearInterval(timer);
  }, [active?.id]);

  const fieldStats = useMemo(
    () => ({
      total: fieldSummary.total || fields.length,
      ready: fieldSummary.ready || 0,
      review: fieldSummary.review || 0,
      unmatched: fieldSummary.unmatched || 0,
    }),
    [fieldSummary, fields.length],
  );

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
      highlight="人工接管 + 表单自动填写"
      subtitle="同一套云端浏览器会话里处理验证码、滑块和官网申请表单。先识别字段，再自动填写，最后由用户确认。"
      terminalLabel="Challenge_Center::Terminal"
      terminalPrompt={active ? `当前会话状态：${active.state || 'unknown'}` : '暂无 challenge 会话，等待创建...'}
      primaryCta={startingBoss ? '创建中...' : '新建 Boss Challenge 会话'}
      onPrimaryClick={() => void startBossSession()}
      terminalLines={[
        { time: '11:30:01', level: 'STATE', text: active?.state || 'idle' },
        { time: '11:30:05', level: 'URL', text: active?.current_url || active?.target_url || 'no active url' },
        { time: '11:30:09', level: 'FIELDS', text: `fields=${fieldStats.total} ready=${fieldStats.ready} review=${fieldStats.review} unmatched=${fieldStats.unmatched}` },
      ]}
    >
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[0.78fr_1.22fr]">
        <div className="space-y-6">
          <Card className="glass-panel" styles={{ body: { padding: 24 } }}>
            <div className="mb-4 text-xl font-bold text-cyan-100">会话列表</div>
            <List
              dataSource={sessions}
              locale={{ emptyText: '暂无会话' }}
              renderItem={(item) => (
                <List.Item style={{ cursor: 'pointer' }} onClick={() => setActive(item)}>
                  <div className="w-full">
                    <div className="flex items-center justify-between gap-3">
                      <div className="font-bold text-cyan-100">{item.title || item.id}</div>
                      <Tag color={item.state === 'challenge_required' ? 'gold' : item.state === 'failed' ? 'red' : 'cyan'}>
                        {item.state || 'unknown'}
                      </Tag>
                    </div>
                    <div className="mt-1 break-all text-xs text-cyan-100/60">{item.current_url || item.target_url || '-'}</div>
                  </div>
                </List.Item>
              )}
            />
          </Card>

          <Card className="glass-panel" styles={{ body: { padding: 24 } }}>
            <div className="mb-4 text-lg font-bold text-cyan-100">官网投递会话</div>
            <div className="space-y-4">
              <Input
                placeholder="官网投递页 URL，例如 https://jobs.xxx.com/apply/..."
                value={genericUrl}
                onChange={(event) => setGenericUrl(event.target.value)}
              />
              <Input
                placeholder="会话标题，可选"
                value={genericTitle}
                onChange={(event) => setGenericTitle(event.target.value)}
              />
              <Space wrap>
                <Button type="primary" loading={startingGeneric} onClick={startGenericSession}>
                  新建官网会话
                </Button>
                <Button loading={startingBoss} onClick={() => void startBossSession()}>
                  新建 Boss 会话
                </Button>
              </Space>
            </div>
          </Card>

          <Card className="glass-panel" styles={{ body: { padding: 24 } }}>
            <div className="mb-3 text-lg font-bold text-cyan-100">验证码 / 人工确认</div>
            <div className="space-y-3">
              <Input
                placeholder="输入你在验证码页看到的文本验证码；滑块则直接在截图上拖动"
                value={code}
                onChange={(event) => setCode(event.target.value)}
              />
              <Space wrap>
                <Button type="primary" loading={submitting} disabled={!active?.id} onClick={submitCode}>
                  提交验证码
                </Button>
                {active?.provider?.includes('boss') && ['ready', 'resumed'].includes(active.state || '') ? (
                  <Button type="default" loading={resuming} onClick={resumeBossSession}>
                    恢复 Boss 执行
                  </Button>
                ) : null}
              </Space>
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="glass-panel" styles={{ body: { padding: 24 } }}>
            <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="text-xl font-bold text-cyan-100">{active?.title || '未选择会话'}</div>
                <div className="mt-1 break-all text-sm text-cyan-100/60">{active?.message || '请选择左侧会话，或新建一个官网/Boss 会话。'}</div>
                {active?.provider?.includes('boss') ? (
                  <div className="mt-2 text-xs text-cyan-300/80">
                    {['ready', 'resumed'].includes(active?.state || '')
                      ? '当前已具备恢复条件，可继续 Boss 执行。'
                      : ['challenge_required', 'waiting_human'].includes(active?.state || '')
                        ? '先在截图中处理验证，再点击恢复 Boss 执行。'
                        : '当前会话尚未进入可恢复状态。'}
                  </div>
                ) : null}
                {active?.metadata ? (
                  <div className="mt-3 flex flex-wrap gap-2 text-xs text-cyan-100/60">
                    {active.metadata.keyword ? <Tag color="cyan">keyword: {String(active.metadata.keyword)}</Tag> : null}
                    {active.metadata.city ? <Tag color="cyan">city: {String(active.metadata.city)}</Tag> : null}
                    {active.metadata.max_count ? <Tag color="cyan">max_count: {String(active.metadata.max_count)}</Tag> : null}
                    {active.updated_at ? <Tag color="default">updated: {active.updated_at}</Tag> : null}
                  </div>
                ) : null}
              </div>
              <Space wrap>
                <Button disabled={!active?.id} onClick={() => active?.id && void refreshSession(active.id)}>刷新</Button>
                <Button disabled={!active?.id} loading={scanningFields} onClick={() => active?.id && void inspectFormFields(active.id)}>
                  扫描表单字段
                </Button>
                <Button disabled={!active?.id || fieldStats.total === 0} loading={autofilling} onClick={autofillFormFields}>
                  一键填写建议值
                </Button>
                <Button danger disabled={!active?.id} onClick={() => { if (!active?.id) return; if (window.confirm('关闭后当前恢复链路会终止，确定继续吗？')) { void closeSession(); } }}>关闭会话</Button>
              </Space>
            </div>

            {active?.id ? (
              <>
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
                <div className="mt-3 text-sm text-cyan-100/60">
                  点击截图可发送点击；拖拽可尝试滑块。系统不会自动绕过验证码，只提供同一会话内的人机接管。
                  {interacting ? ' 正在发送交互...' : ''}
                </div>
              </>
            ) : (
              <div className="rounded-xl border border-dashed border-cyan-400/20 p-12 text-center text-cyan-100/50">
                暂无截图
              </div>
            )}
          </Card>

          <Card className="glass-panel" styles={{ body: { padding: 24 } }}>
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-lg font-bold text-cyan-100">表单字段识别</div>
                <div className="text-sm text-cyan-100/60">
                  只填低风险字段。协议、上传文件、checkbox/radio、验证码不自动处理。
                </div>
              </div>
              <Space wrap>
                <Tag color="cyan">总计 {fieldStats.total}</Tag>
                <Tag color="green">可填 {fieldStats.ready}</Tag>
                <Tag color="gold">待复核 {fieldStats.review}</Tag>
                <Tag color="default">未匹配 {fieldStats.unmatched}</Tag>
              </Space>
            </div>

            {Object.keys(profile).length ? (
              <div className="mb-4 grid grid-cols-1 gap-2 md:grid-cols-2">
                {Object.entries(profile)
                  .filter(([, value]) => String(value || '').trim())
                  .slice(0, 8)
                  .map(([key, value]) => (
                    <div key={key} className="rounded-xl border border-cyan-400/20 bg-black/20 px-3 py-2 text-sm text-cyan-100/80">
                      <div className="font-mono text-xs uppercase text-cyan-300/80">{key}</div>
                      <div className="truncate">{String(value)}</div>
                    </div>
                  ))}
              </div>
            ) : null}

            <List
              dataSource={fields}
              locale={{ emptyText: '先点击“扫描表单字段”，再决定是否自动填写。' }}
              renderItem={(field) => (
                <List.Item>
                  <div className="w-full">
                    <div className="flex flex-wrap items-center gap-2">
                      <div className="font-semibold text-cyan-100">{field.label || field.name || field.placeholder || field.field_id}</div>
                      <Tag color={field.status === 'ready' ? 'green' : field.status === 'review' ? 'gold' : 'default'}>
                        {field.status || 'unknown'}
                      </Tag>
                      {field.required ? <Tag color="red">required</Tag> : null}
                      <Tag color="cyan">{field.tag || 'field'}:{field.type || 'text'}</Tag>
                    </div>
                    <div className="mt-2 text-sm text-cyan-100/70">
                      建议映射：{field.profile_key || '未匹配'} · 建议值：{field.suggested_value || '—'}
                    </div>
                    <div className="mt-1 break-all text-xs text-cyan-100/40">
                      selector: {field.selector || 'n/a'}
                    </div>
                  </div>
                </List.Item>
              )}
            />
          </Card>
        </div>
      </div>
    </CinematicLegacyShell>
  );
};

export default ChallengeCenter;
