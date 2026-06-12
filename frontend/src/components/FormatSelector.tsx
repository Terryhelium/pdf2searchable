import { Checkbox, Space, Typography } from 'antd';
import type { OutputFormat } from '../api/client';
import { OUTPUT_FORMAT_LABELS } from '../api/client';

interface FormatSelectorProps {
  value: OutputFormat[];
  onChange: (formats: OutputFormat[]) => void;
  disabled?: boolean;
}

const ALL_FORMATS: OutputFormat[] = ['pdf', 'tiff', 'jpeg', 'txt', 'md', 'json'];

const FORMAT_DESCRIPTIONS: Record<OutputFormat, string> = {
  pdf: '双层PDF（图像+文字层）',
  tiff: '归档级TIFF（LZW压缩）',
  jpeg: '查询浏览用JPEG',
  txt: 'OCR提取纯文本',
  md: '结构化Markdown（可入知识库）',
  json: 'OCR完整数据JSON（供NER标注）',
};

function FormatSelector({ value, onChange, disabled }: FormatSelectorProps) {
  return (
    <div>
      <Typography.Text strong style={{ display: 'block', marginBottom: 8 }}>
        输出格式
      </Typography.Text>
      <Checkbox.Group
        value={value}
        onChange={(vals) => onChange(vals as OutputFormat[])}
        disabled={disabled}
      >
        <Space direction="vertical" size={4}>
          {ALL_FORMATS.map((fmt) => (
            <Checkbox key={fmt} value={fmt}>
              <Space size={4}>
                <Typography.Text>{OUTPUT_FORMAT_LABELS[fmt]}</Typography.Text>
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                  {FORMAT_DESCRIPTIONS[fmt]}
                </Typography.Text>
              </Space>
            </Checkbox>
          ))}
        </Space>
      </Checkbox.Group>
    </div>
  );
}

export default FormatSelector;
