import { useState, useEffect, useRef } from 'react';
import { Card, Button, Alert, Progress, Space, Typography, Spin } from 'antd';
import { DownloadOutlined, ReloadOutlined, CloseCircleOutlined } from '@ant-design/icons';
import UploadZone from '../components/UploadZone';
import FormatSelector from '../components/FormatSelector';
import JobList from '../components/JobList';
import {
  uploadFile, listBatches, BatchJobInfo,
  OutputFormat,
} from '../api/client';

type UploadState = 'idle' | 'uploading' | 'processing' | 'done' | 'failed';

interface FileDownload {
  format: string;
  label: string;
  url: string;
}

function SingleUpload() {
  const [uploadState, setUploadState] = useState<UploadState>('idle');
  const [files, setFiles] = useState<FileDownload[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [uploadFileName, setUploadFileName] = useState<string>('');
  const [recentJobs, setRecentJobs] = useState<BatchJobInfo[]>([]);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [formats, setFormats] = useState<OutputFormat[]>(['pdf', 'tiff', 'txt', 'md']);
  const [elapsed, setElapsed] = useState(0);
  const abortRef = useRef<AbortController | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadRecentJobs = async () => {
    setJobsLoading(true);
    try {
      const jobs = await listBatches();
      setRecentJobs(jobs.slice(0, 50));
    } catch {
      // ignore
    } finally {
      setJobsLoading(false);
    }
  };

  useEffect(() => {
    loadRecentJobs();
  }, []);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const handleUploadStart = async (file: File) => {
    setUploadFileName(file.name);
    setError(null);
    setFiles([]);
    setElapsed(0);
    setUploadState('uploading');

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      setUploadState('processing');
      timerRef.current = setInterval(() => {
        setElapsed(s => s + 1);
      }, 1000);

      const result = await uploadFile(file, formats, controller.signal);
      if (timerRef.current) clearInterval(timerRef.current);
      if (result.status === 'done') {
        setUploadState('done');
        setFiles(result.files || []);
        loadRecentJobs();
      } else if (result.status === 'failed') {
        setUploadState('failed');
        setError(result.error || '处理失败');
      } else {
        setUploadState('failed');
        setError('未知状态: ' + result.status);
      }
    } catch (e: any) {
      if (timerRef.current) clearInterval(timerRef.current);
      if (e?.code !== 'ERR_CANCELED' && e?.message !== 'canceled') {
        setUploadState('failed');
        setError(e?.response?.data?.detail || e?.message || '上传或处理失败');
      } else {
        handleReset();
      }
    }
  };

  const handleCancel = () => {
    abortRef.current?.abort();
    if (timerRef.current) clearInterval(timerRef.current);
    handleReset();
  };

  const handleReset = () => {
    setUploadState('idle');
    setFiles([]);
    setError(null);
    setUploadFileName('');
    setElapsed(0);
  };

  const isProcessing = uploadState === 'uploading' || uploadState === 'processing';
  const FMT_LABELS: Record<string, string> = { pdf: '可搜索PDF', tiff: 'TIFF', jpeg: 'JPEG', txt: '文本', md: 'Markdown', json: 'JSON' };
  const fmtLabels = formats.map(f => FMT_LABELS[f] || f).join('、');

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Card title="上传文件">
        {uploadState === 'processing' ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>
              <Typography.Text strong>正在处理: {uploadFileName}</Typography.Text>
            </div>
            <Typography.Text type="secondary" style={{ marginTop: 8, display: 'block' }}>
              正在进行 OCR 识别和文档解析（{elapsed} 秒）...
            </Typography.Text>
            <Typography.Text type="secondary" style={{ fontSize: 12, display: 'block' }}>
              输出格式: {fmtLabels} | 多页文档可能需要几分钟
            </Typography.Text>
            <Button
              danger
              style={{ marginTop: 16 }}
              icon={<CloseCircleOutlined />}
              onClick={handleCancel}
            >
              取消处理
            </Button>
          </div>
        ) : (
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <FormatSelector value={formats} onChange={setFormats} disabled={isProcessing} />
            <UploadZone onUploadStart={handleUploadStart} disabled={isProcessing} />
          </Space>
        )}

        {uploadState === 'uploading' && (
          <Progress percent={99} status="active" style={{ marginTop: 16 }} />
        )}

        {uploadState === 'done' && files.length > 0 && (
          <Alert
            style={{ marginTop: 16 }}
            type="success"
            showIcon
            message={`处理完成（用时 ${elapsed} 秒）`}
            description={
              <Space direction="vertical" style={{ width: '100%' }}>
                <Typography.Text>{uploadFileName}</Typography.Text>
                <Space wrap>
                  {files.map((f) => (
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
              </Space>
            }
          />
        )}

        {uploadState === 'failed' && (
          <Alert
            style={{ marginTop: 16 }}
            type="error"
            showIcon
            message="处理失败"
            description={
              <Space direction="vertical">
                <Typography.Text type="danger">{error}</Typography.Text>
                <Button size="small" icon={<ReloadOutlined />} onClick={handleReset}>
                  重新上传
                </Button>
              </Space>
            }
          />
        )}
      </Card>

      <JobList
        jobs={recentJobs.map(j => ({
          job_id: j.job_id,
          status: j.status,
          created_at: j.created_at,
        }))}
        loading={jobsLoading}
        onRefresh={loadRecentJobs}
      />
    </Space>
  );
}

export default SingleUpload;
