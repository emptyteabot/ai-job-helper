import React, { useEffect, useState } from 'react';
import { Button, List, Popconfirm, Typography, Upload, message } from 'antd';
import { DeleteOutlined, FileTextOutlined, UploadOutlined } from '@ant-design/icons';
import { apiUrl, authHeaders } from '../lib/api';
import CinematicLegacyShell from '../components/CinematicLegacyShell';

const { Text, Paragraph } = Typography;

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
      console.error('加载简历列表失败', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (file: File) => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await fetch(apiUrl('/api/resume/upload'), { method: 'POST', headers: authHeaders(), body: formData });
      const result = await response.json();
      if (result.success) {
        message.success('简历上传成功');
        loadResumes();
      } else {
        message.error(result.detail || '简历上传失败');
      }
    } catch (error) {
      message.error('简历上传失败');
    } finally {
      setLoading(false);
    }
    return false;
  };

  const handleDelete = async (filename: string) => {
    try {
      const response = await fetch(apiUrl(`/api/resume/${filename}`), { method: 'DELETE', headers: authHeaders() });
      const result = await response.json();
      if (result.success) {
        message.success('简历删除成功');
        loadResumes();
        if (selectedResume === filename) {
          setSelectedResume('');
          setResumeText('');
        }
      } else {
        message.error('简历删除失败');
      }
    } catch (error) {
      message.error('简历删除失败');
    }
  };

  const handleView = async (filename: string) => {
    try {
      const response = await fetch(apiUrl(`/api/resume/text/${filename}`), { headers: authHeaders() });
      const result = await response.json();
      if (result.success) {
        setSelectedResume(filename);
        setResumeText(result.text || '');
      } else {
        message.error('加载简历内容失败');
      }
    } catch (error) {
      message.error('加载简历内容失败');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  return (
    <CinematicLegacyShell
      sectionId="resumeupload"
      title="简历管理"
      highlight="资产仓库"
      subtitle="简历不是一次性文件，而是会被重写、选取和回看的资产。这个页面就该像资产仓库，而不是临时上传框。"
      terminalLabel="Resume_Upload::Terminal"
      terminalPrompt={loading ? '正在同步简历仓库状态...' : '简历仓库已连接，等待上传或查看...'}
      primaryCta="刷新简历仓库"
      onPrimaryClick={loadResumes}
      terminalLines={[
        { time: '10:31:01', level: 'STORE', text: 'Syncing resume file list...' },
        { time: '10:31:04', level: 'FILES', text: `Current files: ${resumes.length}` },
        { time: '10:31:08', level: 'READY', text: 'Resume storage surface is ready.' },
      ]}
    >
      <div className="space-y-6">
        <div className="glass-panel rounded-2xl p-8">
          <Upload beforeUpload={handleUpload} accept=".pdf,.doc,.docx" maxCount={1} showUploadList={false}>
            <Button icon={<UploadOutlined />} type="primary" size="large">上传简历</Button>
          </Upload>
          <Text type="secondary" style={{ marginLeft: 16 }}>支持 PDF、Word，最大 10MB</Text>
        </div>

        <div className="glass-panel rounded-2xl p-8">
          <List
            loading={loading}
            dataSource={resumes}
            renderItem={(resume) => (
              <List.Item
                actions={[
                  <Button type="link" icon={<FileTextOutlined />} onClick={() => handleView(resume.filename)}>查看</Button>,
                  <Popconfirm title="确定删除这份简历吗？" onConfirm={() => handleDelete(resume.filename)} okText="确定" cancelText="取消">
                    <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
                  </Popconfirm>,
                ]}
              >
                <List.Item.Meta avatar={<FileTextOutlined style={{ fontSize: 24 }} />} title={resume.filename} description={`大小: ${formatFileSize(resume.size)}`} />
              </List.Item>
            )}
          />
        </div>

        {selectedResume ? (
          <div className="glass-panel rounded-2xl p-8">
            <h3 className="text-cyan-100 text-xl font-bold mb-4">{selectedResume}</h3>
            <Paragraph ellipsis={{ rows: 10, expandable: true, symbol: '展开' }} style={{ whiteSpace: 'pre-wrap', color: '#e0f2fe' }}>
              {resumeText}
            </Paragraph>
          </div>
        ) : null}
      </div>
    </CinematicLegacyShell>
  );
};

export default ResumeUpload;
