import { useState } from 'react';
import { Upload, message } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';

const { Dragger } = Upload;

interface UploadZoneProps {
  onUploadStart: (file: File) => void;
  disabled?: boolean;
}

const ACCEPTED_TYPES = '.pdf,.png,.jpg,.jpeg,.tiff,.tif,.bmp';

function UploadZone({ onUploadStart, disabled }: UploadZoneProps) {
  const [fileList, setFileList] = useState<any[]>([]);

  const props: UploadProps = {
    name: 'file',
    multiple: false,
    accept: ACCEPTED_TYPES,
    fileList,
    disabled,
    beforeUpload: (file) => {
      const maxSize = 100 * 1024 * 1024; // 100MB
      if (file.size > maxSize) {
        message.error(`文件太大：${file.name}（最大 100MB）`);
        return Upload.LIST_IGNORE;
      }
      return false; // 阻止自动上传
    },
    onChange: (info) => {
      setFileList(info.fileList);
      if (info.fileList.length > 0 && info.fileList[0].originFileObj) {
        onUploadStart(info.fileList[0].originFileObj as File);
      }
    },
    onRemove: () => {
      setFileList([]);
    },
  };

  return (
    <Dragger {...props}>
      <p className="ant-upload-drag-icon">
        <InboxOutlined />
      </p>
      <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
      <p className="ant-upload-hint">
        支持 PDF、PNG、JPG、TIFF、BMP 格式，单文件最大 100MB
      </p>
    </Dragger>
  );
}

export default UploadZone;