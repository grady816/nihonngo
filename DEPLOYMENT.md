# 部署指南

本文档说明如何在本地或生产环境部署该 Flask 应用。

## 部署结论

该项目是一个标准的 Flask 应用，依赖仅包含 `Flask`，可以直接部署运行。
需要注意的要点：

- 使用 SQLite 数据库文件 `app.db`，部署环境必须对项目目录有写权限。
- 生产环境建议使用 WSGI 服务器（如 Gunicorn）并由反向代理（如 Nginx）对外提供服务。

## 环境要求

- Python 3.10+（建议 3.11）
- `pip`

## 本地运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

服务默认监听 `http://0.0.0.0:5000/`。

## 生产环境（Gunicorn + Nginx 示例）

### 1. 安装依赖并启动 Gunicorn

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

gunicorn -w 2 -b 0.0.0.0:8000 app:app
```

### 2. Nginx 反向代理示例

```nginx
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

重新加载 Nginx 后，访问 `http://example.com/` 即可。

## 数据文件说明

- SQLite 数据库文件：`app.db`
- 若需迁移或备份数据，请复制该文件。

## 常见问题

- **无法写入数据库**：请确保部署用户对项目目录有写权限，或者将项目目录移动到可写路径。
- **静态文件无法访问**：确认 Nginx 未拦截 `/static/` 路由，或使用默认的 Flask 静态目录。
