import { UploadOutlined } from '@ant-design/icons';
import { Button, Card, Space, Tag, Typography } from 'antd';

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
  return (
    <Card
      title="任务记录"
      size="small"
      extra={
        <Button size="small" onClick={onRefresh} loading={loading}>
          刷新
        </Button>
      }
    >
      {jobs.length === 0 ? (
        <Typography.Text type="secondary">暂无任务记录</Typography.Text>
      ) : (
        <Space direction="vertical" style={{ width: '100%' }}>
          {jobs.map((job) => {
            const s = STATUS_MAP[job.status] || { color: 'default', text: job.status };
            return (
              <div
                key={job.job_id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '8px 0',
                  borderBottom: '1px solid #f0f0f0',
                }}
              >
                <Space>
                  <UploadOutlined />
                  <Typography.Text code style={{ fontSize: 12 }}>
                    {job.job_id.slice(0, 8)}...
                  </Typography.Text>
                  {job.created_at && (
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      {new Date(job.created_at).toLocaleString('zh-CN')}
                    </Typography.Text>
                  )}
                </Space>
                <Tag color={s.color}>{s.text}</Tag>
              </div>
            );
          })}
        </Space>
      )}
    </Card>
  );
}

export default JobList;