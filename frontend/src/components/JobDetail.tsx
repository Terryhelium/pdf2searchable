import { Descriptions, Tag, Table, Typography } from 'antd';
import type { BatchDetail } from '../api/client';

interface JobDetailProps {
  detail: BatchDetail;
}

const STATUS_MAP: Record<string, { color: string; text: string }> = {
  pending: { color: 'default', text: '等待中' },
  processing: { color: 'processing', text: '处理中' },
  done: { color: 'success', text: '完成' },
  failed: { color: 'error', text: '失败' },
};

const FILE_COLUMNS = [
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
    width: 100,
    render: (status: string) => {
      const s = STATUS_MAP[status] || { color: 'default', text: status };
      return <Tag color={s.color}>{s.text}</Tag>;
    },
  },
  {
    title: '错误信息',
    dataIndex: 'error_msg',
    key: 'error_msg',
    ellipsis: true,
    render: (msg: string | null) =>
      msg ? <Typography.Text type="danger">{msg}</Typography.Text> : '-',
  },
];

function JobDetail({ detail }: JobDetailProps) {
  const s = STATUS_MAP[detail.status] || { color: 'default', text: detail.status };

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
        columns={FILE_COLUMNS}
        rowKey="filename"
        size="small"
        pagination={false}
      />
    </div>
  );
}

export default JobDetail;