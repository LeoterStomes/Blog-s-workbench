# Ray 内容工作台桌面版

桌面版由 Electron 托管现有工作台：

- 自动启动 FastAPI Agent Gateway
- 自动提供本地前端服务，因此不需要手动打开浏览器
- 使用受限 preload IPC 访问工作区
- 默认工作区位于系统“文档/Ray Workbench”

## 启动

先在 `astro-blog` 中完成生产构建：

```powershell
npm run build
```

再进入本目录启动桌面版：

```powershell
npm start
```

如系统默认 `python` 不可用，可设置 `WORKBENCH_PYTHON` 为 Python 可执行文件路径。
