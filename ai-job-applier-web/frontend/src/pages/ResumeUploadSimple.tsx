import React, { useEffect, useState } from 'react';
import { Button, Card, Space, Spin, Typography, Upload, message } from 'antd';
import { CheckCircleOutlined, FileTextOutlined, UploadOutlined } from '@ant-design/icons';
import { apiUrl, authHeaders } from '../lib/api';
import CinematicLegacyShell from '../components/CinematicLegacyShell';

const { Text, Title } = Typography;

interface Resume {
  filename: string;
  size: number;
}

const ResumeUploadSimple: React.FC = () => {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    loadResumes();
  }, []);

  const loadResumes = async () => {
    setLoading(true);
    try {
      const response = await fetch(apiUrl('/api/resume/list'), { headers: authHeaders() });
      const result = await response.json();
      if (result.success) setResumes(result.resumes || []);
    } catch (error) {
      console.error('加载失败', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await fetch(apiUrl('/api/resume/upload'), { method: 'POST', headers: authHeaders(), body: formData });
      const result = await response.json();
      if (result.success) {
        message.success('简历上传成功');
        loadResumes();
      } else {
        message.error(result.detail || '上传失败');
      }
    } catch (error) {
      message.error('上传失败，请重试');
    } finally {
      setUploading(false);
    }
    return false;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <CinematicLegacyShell
      sectionId="resumequick"
      title="快速上传"
      highlight="一键接入"
      subtitle="这是轻量版上传通道，适合先把简历资产接进系统，再决定是否进入深度分析和工作台执行。"
      terminalLabel="Resume_Quick::Terminal"
      terminalPrompt={uploading ? '正在上传并解析文件结构...' : '等待上传第一份简历资产...'}
      primaryCta="刷新上传状态"
      onPrimaryClick={loadResumes}
      terminalLines={[
        { time: '10:41:01', level: 'UPLOAD', text: 'Quick upload surface initialized.' },
        { time: '10:41:06', level: 'FILES', text: `Current files: ${resumes.length}` },
        { time: '10:41:09', level: 'READY', text: 'Quick resume upload is available.' },
      ]}
    >
      <div className="space-y-6">
        <Card className="glass-panel" styles={{ body: { padding: 32 } }}>
          <Space direction="vertical" size="middle" style={{ width: '100%', textAlign: 'center' }}>
            <FileTextOutlined style={{ fontSize: 48, color: '#22d3ee' }} />
            <Upload beforeUpload={handleUpload} accept=".pdf,.doc,.docx" maxCount={1} showUploadList={false} disabled={uploading}>
              <Button icon={<UploadOutlined />} type="primary" size="large" loading={uploading} style={{ minWidth: 220 }}>
                {uploading ? '上传中...' : '上传简历'}
              </Button>
            </Upload>
            <Text type="secondary">支持 PDF、Word | 最大 10MB</Text>
          </Space>
        </Card>

        <Card className="glass-panel" title="我的简历" styles={{ header: { color: '#67e8f9' }, body: { padding: 24 } }}>
          {loading ? (
            <div className="text-center py-12"><Spin /></div>
          ) : resumes.length === 0 ? (
            <div className="text-center py-12 text-cyan-100/60">还没有上传简历</div>
          ) : (
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              {resumes.map((resume, index) => (
                <Card key={index} size="small" style={{ background: 'rgba(0,0,0,0.28)' }}>
                  <Space>
                    <CheckCircleOutlined style={{ color: '#22d3ee', fontSize: 20 }} />
                    <div>
                      <Text strong>{resume.filename}</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>{formatFileSize(resume.size)}</Text>
                    </div>
                  </Space>
                </Card>
              ))}
            </Space>
          )}
        </Card>
      </div>
    </CinematicLegacyShell>
  );
};

export default ResumeUploadSimple;
