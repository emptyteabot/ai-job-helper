import React, { useEffect, useState } from 'react';
import { Button, Card, List, message, Popconfirm, Typography, Upload } from 'antd';
import { DeleteOutlined, FileTextOutlined, UploadOutlined } from '@ant-design/icons';
import { apiUrl, authFetch, authHeaders } from '../utils/network';

const { Paragraph, Text } = Typography;

interface Resume {
  filename: string;
  size: number;
  path: string;
}

const ResumeUpload: React.FC = () => {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedResume, setSelectedResume] = useState('');
  const [resumeText, setResumeText] = useState('');

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
      message.error(error?.message || '加载简历列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadResumes();
  }, []);

  const handleUpload = async (file: File) => {
    setLoading(true);
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
      message.error(error?.message || '简历上传失败');
    } finally {
      setLoading(false);
    }
    return false;
  };

  const handleDelete = async (filename: string) => {
    try {
      const response = await authFetch(`/api/resume/${encodeURIComponent(filename)}`, { method: 'DELETE' });
      const result = await response.json();
      if (!response.ok || !result.success) {
        throw new Error(result.detail || result.message || '删除失败');
      }
      message.success('简历删除成功');
      await loadResumes();
      if (selectedResume === filename) {
        setSelectedResume('');
        setResumeText('');
      }
    } catch (error: any) {
      message.error(error?.message || '简历删除失败');
    }
  };

  const handleView = async (filename: string) => {
    try {
      const response = await authFetch(`/api/resume/text/${encodeURIComponent(filename)}`);
      const result = await response.json();
      if (!response.ok || !result.success) {
        throw new Error(result.detail || result.message || '读取失败');
      }
      setSelectedResume(filename);
      setResumeText(result.text || '');
    } catch (error: any) {
      message.error(error?.message || '加载简历内容失败');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div>
      <h1>简历管理</h1>

      <Card style={{ marginBottom: 16 }}>
        <Upload beforeUpload={handleUpload} accept=".pdf,.doc,.docx,.txt" maxCount={1} showUploadList={false}>
          <Button icon={<UploadOutlined />} type="primary" size="large" loading={loading}>
            上传简历
          </Button>
        </Upload>
        <Text type="secondary" style={{ marginLeft: 16 }}>
          支持 PDF、Word、TXT，最大 10MB
        </Text>
      </Card>

      <Card title="我的简历" loading={loading}>
        <List
          dataSource={resumes}
          locale={{ emptyText: '暂无简历，请先上传' }}
          renderItem={(resume) => (
            <List.Item
              actions={[
                <Button key="view" type="link" icon={<FileTextOutlined />} onClick={() => handleView(resume.filename)}>
                  查看
                </Button>,
                <Popconfirm
                  key="delete"
                  title="确定删除这份简历吗？"
                  onConfirm={() => handleDelete(resume.filename)}
                  okText="确定"
                  cancelText="取消"
                >
                  <Button type="link" danger icon={<DeleteOutlined />}>
                    删除
                  </Button>
                </Popconfirm>,
              ]}
            >
              <List.Item.Meta
                avatar={<FileTextOutlined style={{ fontSize: 22 }} />}
                title={resume.filename}
                description={`大小: ${formatFileSize(resume.size)}`}
              />
            </List.Item>
          )}
        />
      </Card>

      {selectedResume && (
        <Card title={`简历内容 - ${selectedResume}`} style={{ marginTop: 16 }}>
          <Paragraph ellipsis={{ rows: 12, expandable: true, symbol: '展开' }} style={{ whiteSpace: 'pre-wrap' }}>
            {resumeText}
          </Paragraph>
        </Card>
      )}
    </div>
  );
};

export default ResumeUpload;
