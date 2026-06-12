import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 300000, // 5 min for large uploads
});

export type OutputFormat = 'pdf' | 'tiff' | 'jpeg' | 'txt' | 'md' | 'json';

export const OUTPUT_FORMAT_LABELS: Record<OutputFormat, string> = {
  pdf: '可搜索PDF',
  tiff: 'TIFF图像',
  jpeg: 'JPEG预览',
  txt: '纯文本',
  md: 'Markdown',
  json: 'JSON结构化数据',
};

export interface StatsInfo {
  total_jobs: number;
  success_jobs: number;
  failed_jobs: number;
  processing_jobs: number;
  today_jobs: number;
  total_files: number;
}

export interface UploadResult {
  job_id: string;
  status: string;
  formats: string[];
  result_url: string | null;
  error: string | null;
}

export interface BatchJobInfo {
  job_id: string;
  type: string;
  status: string;
  source_dir: string | null;
  dest_dir: string | null;
  total_files: number;
  processed_files: number;
  error_count: number;
  formats: string[];
  created_at: string;
  updated_at: string;
}

export interface BatchFileInfo {
  filename: string;
  status: string;
  error_msg: string | null;
  result_path: string | null;
}

export interface BatchDetail {
  job_id: string;
  status: string;
  total_files: number;
  processed_files: number;
  error_count: number;
  formats: string[];
  created_at: string;
  updated_at: string;
  files: BatchFileInfo[];
}

export interface HealthInfo {
  status: string;
  paddleocr: string;
  mineru: string;
}

// 统计
export async function getStats(): Promise<StatsInfo> {
  const resp = await api.get<StatsInfo>('/stats');
  return resp.data;
}

// 单文件上传
export async function uploadFile(file: File, formats: OutputFormat[]): Promise<UploadResult> {
  const form = new FormData();
  form.append('file', file);
  const resp = await api.post<UploadResult>(`/upload?formats=${formats.join(',')}`, form);
  return resp.data;
}

// 查询任务状态
export async function getJob(jobId: string): Promise<UploadResult> {
  const resp = await api.get<UploadResult>(`/jobs/${jobId}`);
  return resp.data;
}

// 创建批量任务
export async function createBatch(
  sourceDir: string,
  destDir: string,
  formats: OutputFormat[],
  filePattern = '*',
): Promise<{ job_id: string; status: string; total_files: number; formats: string[] }> {
  const resp = await api.post('/batch', {
    source_dir: sourceDir,
    dest_dir: destDir,
    file_pattern: filePattern,
    formats,
  });
  return resp.data;
}

// 批量任务详情
export async function getBatchDetail(jobId: string): Promise<BatchDetail> {
  const resp = await api.get<BatchDetail>(`/batch/${jobId}`);
  return resp.data;
}

// 批量任务列表
export async function listBatches(): Promise<BatchJobInfo[]> {
  const resp = await api.get<{ jobs: BatchJobInfo[] }>('/batch');
  return resp.data.jobs;
}

// 健康检查
export async function getHealth(): Promise<HealthInfo> {
  const resp = await api.get<HealthInfo>('/health');
  return resp.data;
}

// 文件下载 URL
export function getDownloadUrl(jobId: string, filename: string): string {
  return `/api/download/${jobId}/${filename}`;
}
