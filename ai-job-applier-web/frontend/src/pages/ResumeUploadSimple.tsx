import React, { useEffect, useState } from 'react';
import { Button, Card, Divider, message, Space, Typography, Upload } from 'antd';
import { CheckCircleOutlined, FileTextOutlined, UploadOutlined } from '@ant-design/icons';
import { apiUrl, authFetch, authHeaders } from '../utils/network';

const { Text, Title } = Typography;

interface Resume {
  filename: string;
  size: number;
}

const ResumeUploadSimple: React.FC = () => {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  const loadResumes = async () => {
    setLoading(true);
    try {
      const response = await authFetch('/api/resume/list');
      const result = await response.json();
      if (!response.ok || !result.success) {
        throw new Error(result.detail || result.message || '加载失败');
      }
      setResumes(result.resumes || []);
    } catch (error: any) {
      message.error(error?.message || '加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadResumes();
  }, []);

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(apiUrl('/api/resume/upload'), {
        method: 'POST',
        headers: authHeaders(),
        body: formData,
      });
      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(result.detail || result.message || '上传失败');
      }

      message.success('简历上传成功');
      await loadResumes();
    } catch (error: any) {
      message.error(error?.message || '上传失败，请重试');
    } finally {
      setUploading(false);
    }
    return false;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '20px' }}>
      <Title level={2}>简历管理</Title>
      <Divider />

      <Card style={{ marginBottom: 24, background: '#f8fafc', border: '2px dashed #d9d9d9' }}>
        <Space direction="vertical" size="middle" style={{ width: '100%', textAlign: 'center' }}>
          <FileTextOutlined style={{ fontSize: 48, color: '#1890ff' }} />

          <Upload beforeUpload={handleUpload} accept=".pdf,.doc,.docx,.txt" maxCount={1} showUploadList={false} disabled={uploading}>
            <Button icon={<UploadOutlined />} type="primary" size="large" loading={uploading} style={{ minWidth: 200 }}>
              {uploading ? '上传中...' : '上传简历'}
            </Button>
          </Upload>

          <Text type="secondary">支持 PDF、Word、TXT | 最大 10MB</Text>
        </Space>
      </Card>

      <Card title="我的简历" loading={loading}>
        {resumes.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Text type="secondary">还没有上传简历</Text>
          </div>
        ) : (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            {resumes.map((resume) => (
              <Card key={resume.filename} size="small" style={{ background: '#fafafa' }}>
                <Space>
                  <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 20 }} />
                  <div>
                    <Text strong>{resume.filename}</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {formatFileSize(resume.size)}
                    </Text>
                  </div>
                </Space>
              </Card>
            ))}
          </Space>
        )}
      </Card>
    </div>
  );
};

export default ResumeUploadSimple;
