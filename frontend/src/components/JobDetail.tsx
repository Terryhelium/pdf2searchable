import { Descriptions, Tag, Table, Typography, Button } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import type { BatchDetail, BatchFileInfo } from '../api/client';

interface JobDetailProps {
  detail: BatchDetail;
}

const STATUS_MAP: Record<string, { color: string; text: string }> = {
  pending: { color: 'default', text: '等待中' },
  processing: { color: 'processing', text: '处理中' },
  done: { color: 'success', text: '完成' },
  failed: { color: 'error', text: '失败' },
};

function JobDetail({ detail }: JobDetailProps) {
  const s = STATUS_MAP[detail.status] || { color: 'default', text: detail.status };

  const columns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => {
        const s2 = STATUS_MAP[status] || { color: 'default', text: status };
        return <Tag color={s2.color}>{s2.text}</Tag>;
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: BatchFileInfo) =>
        record.result_path ? (
          <Button
            type="link"
            size="small"
            icon={<DownloadOutlined />}
            href={`/api/download/${detail.job_id}?format=${record.filename.split('.').pop()}`}
            target="_blank"
          >
            下载
          </Button>
        ) : null,
    },
  ];

  return (
    <div>
      <Descriptions size="small" column={2} style={{ marginBottom: 16 }}>
        <Descriptions.Item label="任务 ID">
          <Typography.Text code>{detail.job_id.slice(0, 8)}...</Typography.Text>
        </Descriptions.Item>
        <Descriptions.Item label="状态">
          <Tag color={s.color}>{s.text}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="总文件数">{detail.total_files}</Descriptions.Item>
        <Descriptions.Item label="已处理">{detail.processed_files}</Descriptions.Item>
        <Descriptions.Item label="错误数">{detail.error_count}</Descriptions.Item>
        <Descriptions.Item label="创建时间">
          {new Date(detail.created_at).toLocaleString('zh-CN')}
        </Descriptions.Item>
        <Descriptions.Item label="更新时间">
          {new Date(detail.updated_at).toLocaleString('zh-CN')}
        </Descriptions.Item>
      </Descriptions>
      <Table
        dataSource={detail.files}
        columns={columns}
        rowKey="filename"
        size="small"
        pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (t) => `共 ${t} 条` }}
      />
    </div>
  );
}

export default JobDetail;
