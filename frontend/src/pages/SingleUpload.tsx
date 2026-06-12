import { useState, useEffect, useCallback, useRef } from 'react';
import { Card, Button, Alert, Progress, Space, Typography } from 'antd';
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import UploadZone from '../components/UploadZone';
import FormatSelector from '../components/FormatSelector';
import JobList from '../components/JobList';
import {
  uploadFile, getJob, listBatches, BatchJobInfo,
  OutputFormat, OUTPUT_FORMAT_LABELS,
} from '../api/client';

type UploadState = 'idle' | 'uploading' | 'processing' | 'done' | 'failed';

function SingleUpload() {
  const [uploadState, setUploadState] = useState<UploadState>('idle');
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadFileName, setUploadFileName] = useState<string>('');
  const [recentJobs, setRecentJobs] = useState<BatchJobInfo[]>([]);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [formats, setFormats] = useState<OutputFormat[]>(['pdf', 'tiff', 'txt', 'md']);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  const startPolling = useCallback((id: string) => {
    stopPolling();
    pollingRef.current = setInterval(async () => {
      try {
        const job = await getJob(id);
        if (job.status === 'done') {
          setUploadState('done');
          setResultUrl(job.result_url);
          stopPolling();
          loadRecentJobs();
        } else if (job.status === 'failed') {
          setUploadState('failed');
          setError(job.error || '处理失败');
          stopPolling();
        } else if (job.status === 'processing') {
          setUploadState('processing');
        }
      } catch {
        stopPolling();
      }
    }, 2000);
  }, [stopPolling]);

  useEffect(() => {
    return () => stopPolling();
  }, [stopPolling]);

  const handleUploadStart = async (file: File) => {
    setUploadFileName(file.name);
    setError(null);
    setResultUrl(null);
    setUploadState('uploading');

    try {
      const result = await uploadFile(file, formats);
      setUploadState('processing');
      startPolling(result.job_id);
    } catch (e: any) {
      setUploadState('failed');
      setError(e?.response?.data?.detail || e?.message || '上传失败');
    }
  };

  const loadRecentJobs = async () => {
    setJobsLoading(true);
    try {
      const jobs = await listBatches();
      setRecentJobs(jobs.slice(0, 10));
    } catch {
      // ignore
    } finally {
      setJobsLoading(false);
    }
  };

  useEffect(() => {
    loadRecentJobs();
  }, []);

  const handleReset = () => {
    stopPolling();
    setUploadState('idle');
    setResultUrl(null);
    setError(null);
    setUploadFileName('');
  };

  const isProcessing = uploadState === 'uploading' || uploadState === 'processing';

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Card title="上传文件">
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <FormatSelector value={formats} onChange={setFormats} disabled={isProcessing} />

          <UploadZone onUploadStart={handleUploadStart} disabled={isProcessing} />
        </Space>

        {uploadState === 'uploading' && (
          <Progress percent={99} status="active" style={{ marginTop: 16 }} />
        )}

        {uploadState === 'processing' && (
          <Alert
            style={{ marginTop: 16 }}
            type="info"
            showIcon
            message={`正在处理: ${uploadFileName}`}
            description={(() => {
              const fmtLabels = formats.map(f => OUTPUT_FORMAT_LABELS[f]).join('、');
              return `输出格式: ${fmtLabels} | 正在进行OCR识别和文档解析，请稍候...`;
            })()}
          />
        )}

        {uploadState === 'done' && resultUrl && (
          <Alert
            style={{ marginTop: 16 }}
            type="success"
            showIcon
            message="处理完成"
            description={
              <Space>
                <Typography.Text>{uploadFileName}</Typography.Text>
                {formats.map((fmt) => (
                  <Button
                    key={fmt}
                    type="primary"
                    size="small"
                    icon={<DownloadOutlined />}
                    href={resultUrl}
                    target="_blank"
                  >
                    下载 {OUTPUT_FORMAT_LABELS[fmt]}
                  </Button>
                ))}
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
