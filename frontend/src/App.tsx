import { useState, useCallback } from 'react';
import { ConfigProvider, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import AppLayout from './components/AppLayout';

type ThemeMode = 'light' | 'dark';

export interface ColorPreset {
  name: string;
  color: string;
}

const COLOR_PRESETS: ColorPreset[] = [
  { name: '极客蓝', color: '#1677ff' },
  { name: '火山橙', color: '#fa541c' },
  { name: '金盏花', color: '#faad14' },
  { name: '极客绿', color: '#52c41a' },
  { name: '暮光紫', color: '#722ed1' },
  { name: '烈焰红', color: '#f5222d' },
];

function App() {
  const [mode, setMode] = useState<ThemeMode>('light');
  const [primaryColor, setPrimaryColor] = useState('#1677ff');

  const handleToggleTheme = useCallback(() => {
    setMode(m => (m === 'light' ? 'dark' : 'light'));
  }, []);

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: mode === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: primaryColor,
          borderRadius: 6,
        },
      }}
    >
      <AppLayout
        mode={mode}
        primaryColor={primaryColor}
        colorPresets={COLOR_PRESETS}
        onToggleTheme={handleToggleTheme}
        onChangeColor={setPrimaryColor}
      />
    </ConfigProvider>
  );
}

export default App;
