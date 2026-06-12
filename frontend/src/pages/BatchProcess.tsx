import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Card, Form, Input, Button, List, Tag, Space, Alert, Typography, Spin, Modal,
} from 'antd';
import {
  FolderOpenOutlined, ReloadOutlined, EyeOutlined,
} from '@ant-design/icons';
import FormatSelector from '../components/FormatSelector';
import JobDetail from '../components/JobDetail';
import {
  createBatch, listBatches, getBatchDetail, BatchJobInfo, BatchDetail,
  OutputFormat,
} from '../api/client';

const STATUS_MAP: Record<string, { color: string; text: string }> = {
  pending: { color: 'default', text: '等待中' },
  processing: { color: 'processing', text: '处理中' },
  done: { color: 'success', text: '完成' },
  failed: { color: 'error', text: '失败' },
};

function BatchProcess() {
  const [form] = Form.useForm();
  const [jobs, setJobs] = useState<BatchJobInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedDetail, setSelectedDetail] = useState<BatchDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [formats, setFormats] = useState<OutputFormat[]>(['pdf', 'tiff', 'txt', 'md']);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadJobs = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listBatches();
      setJobs(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  // 轮询还在 processing 的任务
  useEffect(() => {
    const hasProcessing = jobs.some(j => j.status === 'processing' || j.status === 'pending');
    if (hasProcessing) {
      pollingRef.current = setInterval(() => {
        loadJobs();
      }, 3000);
    } else {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    }
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, [jobs, loadJobs]);

  const handleCreate = async (values: { source_dir: string; dest_dir: string; file_pattern?: string }) => {
    setCreating(true);
    setError(null);
    try {
      await createBatch(values.source_dir, values.dest_dir, formats, values.file_pattern || '*');
      form.resetFields();
      loadJobs();
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || '创建批量任务失败');
    } finally {
      setCreating(false);
    }
  };

  const handleViewDetail = async (jobId: string) => {
    setDetailLoading(true);
    setDetailOpen(true);
    try {
      const detail = await getBatchDetail(jobId);
      setSelectedDetail(detail);
    } catch {
      setSelectedDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Card title="创建批量任务">
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreate}
          style={{ maxWidth: 600 }}
        >
          <Form.Item label="输出格式">
            <FormatSelector value={formats} onChange={setFormats} disabled={creating} />
          </Form.Item>

          <Form.Item
            name="source_dir"
            label="源目录"
            rules={[{ required: true, message: '请输入源目录路径' }]}
          >
            <Input placeholder="/mnt/nas/source" />
          </Form.Item>

          <Form.Item
            name="dest_dir"
            label="输出目录"
            rules={[{ required: true, message: '请输入输出目录路径' }]}
          >
            <Input placeholder="/mnt/nas/dest" />
          </Form.Item>

          <Form.Item
            name="file_pattern"
            label="文件匹配模式"
            initialValue="*"
          >
            <Input placeholder="*.pdf（留空处理所有文件）" />
          </Form.Item>

          {error && (
            <Alert
              style={{ marginBottom: 16 }}
              type="error"
              showIcon
              message={error}
              closable
              onClose={() => setError(null)}
            />
          )}

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={creating} icon={<FolderOpenOutlined />}>
              创建任务
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card
        title="批量任务列表"
        extra={
          <Button size="small" icon={<ReloadOutlined />} onClick={loadJobs} loading={loading}>
            刷新
          </Button>
        }
      >
        {jobs.length === 0 && !loading ? (
          <Typography.Text type="secondary">暂无批量任务</Typography.Text>
        ) : (
          <List
            loading={loading}
            dataSource={jobs}
            renderItem={(job) => {
              const s = STATUS_MAP[job.status] || { color: 'default', text: job.status };
              return (
                <List.Item
                  actions={[
                    <Button
                      key="view"
                      type="link"
                      size="small"
                      icon={<EyeOutlined />}
                      onClick={() => handleViewDetail(job.job_id)}
                    >
                      详情
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    title={
                      <Space>
                        <Typography.Text code style={{ fontSize: 12 }}>
                          {job.job_id.slice(0, 8)}...
                        </Typography.Text>
                        <Tag color={s.color}>{s.text}</Tag>
                      </Space>
                    }
                    description={
                      <Space size="small" wrap>
                        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                          源: {job.source_dir || '-'}
                        </Typography.Text>
                        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                          总计: {job.total_files}
                        </Typography.Text>
                        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                          已处理: {job.processed_files}
                        </Typography.Text>
                        {job.error_count > 0 && (
                          <Typography.Text type="danger" style={{ fontSize: 12 }}>
                            错误: {job.error_count}
                          </Typography.Text>
                        )}
                        {job.formats?.length > 0 && (
                          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                            格式: {job.formats.map(f => f.toUpperCase()).join('/')}
                          </Typography.Text>
                        )}
                        {job.created_at && (
                          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                            {new Date(job.created_at).toLocaleString('zh-CN')}
                          </Typography.Text>
                        )}
                      </Space>
                    }
                  />
                </List.Item>
              );
            }}
          />
        )}
      </Card>

      <Modal
        title="任务详情"
        open={detailOpen}
        onCancel={() => setDetailOpen(false)}
        footer={null}
        width={800}
      >
        {detailLoading ? (
          <div style={{ textAlign: 'center', padding: 24 }}>
            <Spin />
          </div>
        ) : selectedDetail ? (
          <JobDetail detail={selectedDetail} />
        ) : (
          <Typography.Text type="danger">加载失败</Typography.Text>
        )}
      </Modal>
    </Space>
  );
}

export default BatchProcess;
