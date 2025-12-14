# 使用官方 Python 运行时作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MODE=prod \
    PYTHONPATH=/app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p static logs

# 暴露端口（根据配置，默认是 8512）
# 注意：如果修改了配置文件中的端口，需要同步修改这里和 docker-compose.yml
EXPOSE 8512

# 健康检查
# 检查 /api/health 端点，确保应用正常运行
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8512/api/health').read()" || exit 1

# 运行应用
# 使用 python -u 确保输出不被缓冲
CMD ["python", "-u", "main.py"]

