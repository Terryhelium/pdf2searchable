import { useState } from 'react';
import { Button, Card, Modal, Space, Spin, Tag, Typography, List, Checkbox, Popconfirm, message, Tooltip } from 'antd';
import { DownloadOutlined, EyeOutlined, UploadOutlined, DeleteOutlined, CheckSquareOutlined, CloseOutlined } from '@ant-design/icons';
import { getJob, deleteJob, batchDeleteJobs, UploadResult } from '../api/client';

interface JobInfo {
  job_id: string;
  status: string;
  created_at?: string;
}

interface JobListProps {
  jobs: JobInfo[];
  loading?: boolean;
  onRefresh?: () => void;
}

const STATUS_MAP: Record<string, { color: string; text: string }> = {
  pending: { color: 'default', text: '等待中' },
  processing: { color: 'processing', text: '处理中' },
  done: { color: 'success', text: '完成' },
  failed: { color: 'error', text: '失败' },
};

function JobList({ jobs, loading, onRefresh }: JobListProps) {
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailData, setDetailData] = useState<UploadResult | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [deleting, setDeleting] = useState(false);
  const [batchMode, setBatchMode] = useState(false);

  const handleView = async (jobId: string) => {
    setDetailLoading(true);
    setDetailOpen(true);
    try {
      const result = await getJob(jobId);
      setDetailData(result);
    } catch {
      setDetailData(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleDelete = async (jobId: string) => {
    try {
      await deleteJob(jobId);
      message.success('已删除');
      onRefresh?.();
      if (detailData?.job_id === jobId) setDetailOpen(false);
    } catch {
      message.error('删除失败');
    }
  };

  const handleBatchDelete = async () => {
    setDeleting(true);
    try {
      await batchDeleteJobs(Array.from(selectedIds));
      message.success(`已删除 ${selectedIds.size} 个任务`);
      setSelectedIds(new Set());
      onRefresh?.();
    } catch {
      message.error('批量删除失败');
    } finally {
      setDeleting(false);
    }
  };

  const toggleSelect = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectAll = () => {
    if (selectedIds.size === jobs.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(jobs.map(j => j.job_id)));
    }
  };

  return (
    <>
      <Card
        title="任务记录"
        size="small"
        extra={
          <Space>
            {batchMode && selectedIds.size > 0 && (
              <Popconfirm
                title={`确定删除选中的 ${selectedIds.size} 个任务？`}
                onConfirm={handleBatchDelete}
              >
                <Button danger size="small" loading={deleting} icon={<DeleteOutlined />}>
                  删除 ({selectedIds.size})
                </Button>
              </Popconfirm>
            )}
            <Tooltip title={batchMode ? '退出批量管理' : '批量管理'}>
              <Button
                size="small"
                icon={batchMode ? <CloseOutlined /> : <CheckSquareOutlined />}
                onClick={() => { setBatchMode(!batchMode); setSelectedIds(new Set()); }}
                type={batchMode ? 'primary' : 'default'}
              />
            </Tooltip>
            <Button size="small" onClick={onRefresh} loading={loading}>
              刷新
            </Button>
          </Space>
        }
      >
        {jobs.length === 0 ? (
          <Typography.Text type="secondary">暂无任务记录</Typography.Text>
        ) : (
          <List
            size="small"
            dataSource={jobs}
            renderItem={(job) => {
              const s = STATUS_MAP[job.status] || { color: 'default', text: job.status };
              const checked = selectedIds.has(job.job_id);
              return (
                <List.Item
                  actions={[
                    <Button
                      key="view"
                      type="link"
                      size="small"
                      icon={<EyeOutlined />}
                      onClick={() => handleView(job.job_id)}
                    >
                      详情
                    </Button>,
                    <Popconfirm
                      key="delete"
                      title="删除此任务？"
                      onConfirm={() => handleDelete(job.job_id)}
                    >
                      <Button type="link" danger size="small" icon={<DeleteOutlined />} />
                    </Popconfirm>,
                  ]}
                >
                  {batchMode && <Checkbox checked={checked} onChange={() => toggleSelect(job.job_id)} />}
                  <List.Item.Meta
                    avatar={<UploadOutlined />}
                    title={
                      <Space>
                        <Typography.Text code style={{ fontSize: 12 }}>
                          {job.job_id.slice(0, 8)}...
                        </Typography.Text>
                        <Tag color={s.color}>{s.text}</Tag>
                      </Space>
                    }
                    description={
                      job.created_at && (
                        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                          {new Date(job.created_at).toLocaleString('zh-CN')}
                        </Typography.Text>
                      )
                    }
                  />
                </List.Item>
              );
            }}
          />
        )}
        {batchMode && jobs.length > 0 && (
          <div style={{ marginTop: 8 }}>
            <Button type="link" size="small" onClick={selectAll}>
              {selectedIds.size === jobs.length ? '取消全选' : '全选'}
            </Button>
          </div>
        )}
      </Card>

      <Modal
        title="任务详情"
        open={detailOpen}
        onCancel={() => setDetailOpen(false)}
        footer={null}
        width={500}
      >
        {detailLoading ? (
          <div style={{ textAlign: 'center', padding: 24 }}><Spin /></div>
        ) : detailData ? (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Typography.Text code>{detailData.job_id}</Typography.Text>
            <Tag color={STATUS_MAP[detailData.status]?.color}>
              {STATUS_MAP[detailData.status]?.text || detailData.status}
            </Tag>
            {detailData.error && (
              <Typography.Text type="danger">{detailData.error}</Typography.Text>
            )}
            {detailData.files && detailData.files.length > 0 ? (
              <div>
                <Typography.Text strong>下载文件：</Typography.Text>
                <Space wrap style={{ marginTop: 8 }}>
                  {detailData.files.map((f) => (
                    <Button
                      key={f.format}
                      type="primary"
                      size="small"
                      icon={<DownloadOutlined />}
                      href={f.url}
                      target="_blank"
                    >
                      下载 {f.label}
                    </Button>
                  ))}
                </Space>
              </div>
            ) : detailData.status === 'done' ? (
              <Typography.Text type="secondary">没有可下载的文件</Typography.Text>
            ) : null}
            <Popconfirm
              title="确定删除此任务？"
              onConfirm={() => handleDelete(detailData.job_id)}
            >
              <Button danger icon={<DeleteOutlined />} style={{ marginTop: 8 }}>
                删除此任务
              </Button>
            </Popconfirm>
          </Space>
        ) : (
          <Typography.Text type="danger">加载失败</Typography.Text>
        )}
      </Modal>
    </>
  );
}

export default JobList;
