FROM registry.baidubce.com/paddlepaddle/paddle:2.6.1-gpu-cuda11.7-cudnn8.4-trt8.4

RUN apt-get update && apt-get install -y --no-install-recommends \
    ghostscript \
    unpaper \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q https://mirrors.ustc.edu.cn/github-release/conda-forge/miniforge/LatestRelease/Miniforge3-Linux-x86_64.sh -O /tmp/miniforge.sh \
    && bash /tmp/miniforge.sh -b -p /opt/conda \
    && rm /tmp/miniforge.sh
ENV PATH="/opt/conda/bin:$PATH"

RUN conda create -n ocr python=3.11 -y
ENV PATH="/opt/conda/envs/ocr/bin:$PATH"

# 分步安装，确保每步成功
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com \
    ocrmypdf img2pdf pluggy pillow

RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com \
    ocrmypdf-paddleocr --no-deps

RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com \
    paddleocr fastapi uvicorn python-multipart

RUN pip install --no-cache-dir \
    paddlepaddle-gpu==2.6.1.post117 -i https://www.paddlepaddle.org.cn/packages/stable/cu117/

WORKDIR /app
COPY server.py .

EXPOSE 8090
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8090"]
