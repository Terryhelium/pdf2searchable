import { useEffect, useState } from 'react';
import {
  Card, Row, Col, Statistic, Space, Typography, List, Tag, Spin,
} from 'antd';
import {
  FileTextOutlined, CheckCircleOutlined, CloseCircleOutlined,
  SyncOutlined, CalendarOutlined, InboxOutlined,
} from '@ant-design/icons';
import { getStats, listBatches, StatsInfo, BatchJobInfo } from '../api/client';

const STATUS_MAP: Record<string, { color: string; text: string }> = {
  pending: { color: 'default', text: '等待中' },
  processing: { color: 'processing', text: '处理中' },
  done: { color: 'success', text: '完成' },
  failed: { color: 'error', text: '失败' },
};

function Dashboard() {
  const [stats, setStats] = useState<StatsInfo | null>(null);
  const [recentJobs, setRecentJobs] = useState<BatchJobInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getStats(), listBatches()]).then(([s, j]) => {
      setStats(s);
      setRecentJobs(j.slice(0, 8));
    }).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Row gutter={[16, 16]}>
        <Col xs={12} sm={8} md={4}>
          <Card size="small">
            <Statistic
              title="总处理文档"
              value={stats?.total_files ?? 0}
              prefix={<InboxOutlined />}
              valueStyle={{ fontSize: 24 }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card size="small">
            <Statistic
              title="今日处理"
              value={stats?.today_jobs ?? 0}
              prefix={<CalendarOutlined />}
              valueStyle={{ fontSize: 24, color: '#1677ff' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card size="small">
            <Statistic
              title="处理成功"
              value={stats?.success_jobs ?? 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ fontSize: 24, color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card size="small">
            <Statistic
              title="处理失败"
              value={stats?.failed_jobs ?? 0}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ fontSize: 24, color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card size="small">
            <Statistic
              title="处理中"
              value={stats?.processing_jobs ?? 0}
              prefix={<SyncOutlined />}
              valueStyle={{ fontSize: 24, color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={4}>
          <Card size="small">
            <Statistic
              title="任务总数"
              value={stats?.total_jobs ?? 0}
              prefix={<FileTextOutlined />}
              valueStyle={{ fontSize: 24 }}
            />
          </Card>
        </Col>
      </Row>

      <Card title="最近处理记录" size="small">
        {recentJobs.length === 0 ? (
          <Typography.Text type="secondary">暂无处理记录</Typography.Text>
        ) : (
          <List
            size="small"
            dataSource={recentJobs}
            renderItem={(job) => {
              const s = STATUS_MAP[job.status] || { color: 'default', text: job.status };
              return (
                <List.Item>
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
                      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                        {job.created_at ? new Date(job.created_at).toLocaleString('zh-CN') : ''}
                        {job.type === 'batch' && ` | ${job.total_files} 个文件`}
                      </Typography.Text>
                    }
                  />
                </List.Item>
              );
            }}
          />
        )}
      </Card>
    </Space>
  );
}

export default Dashboard;
