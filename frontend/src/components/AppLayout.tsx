import { useState } from 'react';
import {
  Layout, Menu, Typography, Button, Tooltip, Space, Dropdown,
} from 'antd';
import {
  DashboardOutlined, UploadOutlined, FolderOpenOutlined,
  SunOutlined, MoonOutlined,
  MenuFoldOutlined, MenuUnfoldOutlined,
  BgColorsOutlined, CheckOutlined,
} from '@ant-design/icons';
import Dashboard from '../pages/Dashboard';
import SingleUpload from '../pages/SingleUpload';
import BatchProcess from '../pages/BatchProcess';
import type { ColorPreset } from '../App';

const { Header, Sider, Content } = Layout;

type PageKey = 'dashboard' | 'upload' | 'batch';

interface AppLayoutProps {
  mode: 'light' | 'dark';
  primaryColor: string;
  colorPresets: ColorPreset[];
  onToggleTheme: () => void;
  onChangeColor: (color: string) => void;
}

const MENU_ITEMS = [
  { key: 'dashboard', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: 'upload', icon: <UploadOutlined />, label: '单文件上传' },
  { key: 'batch', icon: <FolderOpenOutlined />, label: '批量处理' },
];

const PAGE_TITLE: Record<PageKey, string> = {
  dashboard: '仪表盘',
  upload: '单文件上传',
  batch: '批量处理',
};

function AppLayout({ mode, primaryColor, colorPresets, onToggleTheme, onChangeColor }: AppLayoutProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [currentPage, setCurrentPage] = useState<PageKey>('dashboard');

  const isDark = mode === 'dark';
  const siderTheme = isDark ? 'dark' : 'light';
  const headerBg = isDark ? '#141414' : '#fff';
  const headerBorder = isDark ? '#303030' : '#f0f0f0';

  const pageContent = (() => {
    switch (currentPage) {
      case 'upload': return <SingleUpload />;
      case 'batch': return <BatchProcess />;
      default: return <Dashboard />;
    }
  })();

  const colorMenuItems = {
    items: colorPresets.map((p) => ({
      key: p.color,
      label: (
        <Space
          style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between', width: 140 }}
          onClick={() => onChangeColor(p.color)}
        >
          <Space>
            <div
              style={{
                width: 14, height: 14, borderRadius: 3,
                background: p.color, display: 'inline-block',
              }}
            />
            <span>{p.name}</span>
          </Space>
          {primaryColor === p.color && <CheckOutlined style={{ color: p.color }} />}
        </Space>
      ),
    })),
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme={siderTheme}
        width={220}
        style={{ borderRight: `1px solid ${headerBorder}` }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderBottom: `1px solid ${headerBorder}`,
            padding: '0 16px',
          }}
        >
          <Typography.Text
            strong
            style={{
              color: isDark ? '#fff' : undefined,
              fontSize: collapsed ? 20 : 14,
              whiteSpace: 'nowrap',
              textAlign: 'center',
              lineHeight: 1.3,
            }}
          >
            {collapsed ? '\u{1F4C4}' : '宁波市档案馆\n文档OCR处理系统'}
          </Typography.Text>
        </div>
        <Menu
          theme={siderTheme}
          mode="inline"
          selectedKeys={[currentPage]}
          items={MENU_ITEMS}
          onClick={({ key }) => setCurrentPage(key as PageKey)}
          style={{ borderInlineEnd: 'none' }}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: headerBg,
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: `1px solid ${headerBorder}`,
            height: 64,
            lineHeight: '64px',
          }}
        >
          <Space>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
            />
            <Typography.Text
              strong
              style={{ fontSize: 15, color: isDark ? '#e8e8e8' : undefined }}
            >
              {PAGE_TITLE[currentPage]}
            </Typography.Text>
          </Space>

          <Space size="small">
            <Dropdown menu={colorMenuItems} trigger={['click']} placement="bottomRight">
              <Tooltip title="主题色">
                <Button type="text" icon={<BgColorsOutlined style={{ color: primaryColor }} />} />
              </Tooltip>
            </Dropdown>
            <Tooltip title={isDark ? '切换浅色模式' : '切换深色模式'}>
              <Button
                type="text"
                icon={isDark ? <SunOutlined /> : <MoonOutlined />}
                onClick={onToggleTheme}
              />
            </Tooltip>
          </Space>
        </Header>
        <Content
          style={{
            padding: 24,
            maxWidth: 1200,
            margin: '0 auto',
            width: '100%',
            overflow: 'auto',
          }}
        >
          {pageContent}
        </Content>
      </Layout>
    </Layout>
  );
}

export default AppLayout;
