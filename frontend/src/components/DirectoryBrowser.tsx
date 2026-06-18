import { useState, useEffect, useCallback } from 'react';
import { Modal, Input, List, Space, Typography, Button, Spin, Alert } from 'antd';
import {
  FolderOutlined, FileOutlined, ArrowLeftOutlined,
  ReloadOutlined, FolderOpenOutlined,
} from '@ant-design/icons';
import { api } from '../api/client';

interface DirEntry {
  name: string;
  path: string;
  is_dir: boolean;
  size: number;
}

interface BrowseResult {
  current: string;
  parent: string | null;
  items: DirEntry[];
}

interface DirectoryBrowserProps {
  open: boolean;
  onClose: () => void;
  onSelect: (path: string) => void;
  title?: string;
  initialPath?: string;
}

function DirectoryBrowser({ open, onClose, onSelect, title = '选择目录', initialPath = '/' }: DirectoryBrowserProps) {
  const [currentPath, setCurrentPath] = useState(initialPath);
  const [items, setItems] = useState<DirEntry[]>([]);
  const [parentPath, setParentPath] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPath = useCallback(async (path: string) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await api.get<BrowseResult>('/browse', { params: { path } });
      setItems(resp.data.items.filter(i => i.is_dir));
      setCurrentPath(resp.data.current);
      setParentPath(resp.data.parent);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || '加载失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      loadPath(initialPath);
    }
  }, [open, initialPath, loadPath]);

  const handleNavigate = (path: string) => loadPath(path);
  const handleSelect = () => { onSelect(currentPath); onClose(); };
  const handleRefresh = () => loadPath(currentPath);

  return (
    <Modal
      title={<Space><FolderOpenOutlined />{title}</Space>}
      open={open}
      onCancel={onClose}
      onOk={handleSelect}
      okText="选择此目录"
      cancelText="取消"
      width={600}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="small">
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Typography.Text code style={{ fontSize: 12 }}>{currentPath}</Typography.Text>
          <Space size="small">
            {parentPath && (
              <Button
                size="small"
                icon={<ArrowLeftOutlined />}
                onClick={() => handleNavigate(parentPath!)}
              >
                上级
              </Button>
            )}
            <Button size="small" icon={<ReloadOutlined />} onClick={handleRefresh} />
          </Space>
        </Space>

        <Input.Search
          placeholder="直接输入路径回车跳转"
          onSearch={(v) => handleNavigate(v || '/')}
          size="small"
        />

        {error && <Alert type="error" message={error} closable />}

        <div style={{ maxHeight: 350, overflow: 'auto' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
          ) : (
            <List
              size="small"
              dataSource={items}
              locale={{ emptyText: '此目录下没有子目录' }}
              renderItem={(item) => (
                <List.Item
                  style={{ cursor: 'pointer', padding: '6px 12px' }}
                  onClick={() => handleNavigate(item.path)}
                >
                  <Space>
                    {item.is_dir
                      ? <FolderOutlined style={{ color: '#faad14' }} />
                      : <FileOutlined />}
                    <Typography.Text
                      style={{ fontSize: 13 }}
                      ellipsis={{ tooltip: item.path }}
                    >
                      {item.name}
                    </Typography.Text>
                  </Space>
                </List.Item>
              )}
            />
          )}
        </div>
      </Space>
    </Modal>
  );
}

export default DirectoryBrowser;
