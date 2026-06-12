# 双远程 Git 配置

本项目使用双远程 Git 仓库：一个用于私有协作（Gitea），一个用于公开备份（GitHub）。

## 当前远程配置

```bash
git remote -v
```

预期输出：

```
gitea   http://192.168.31.217:8080/admin/pdf2searchable.git (fetch)
gitea   http://192.168.31.217:8080/admin/pdf2searchable.git (push)
github  https://github.com/Terryhelium/pdf2searchable.git (fetch)
github  https://github.com/Terryhelium/pdf2searchable.git (push)
```

## 推送到两个远程

```bash
# 推送到 Gitea（私有）
git push gitea main

# 推送到 GitHub（公开）
git push github main

# 同时推送到两个远程
git push gitea main && git push github main
```

## 从远程克隆

```bash
# 从 Gitea 克隆
git clone http://192.168.31.217:8080/admin/pdf2searchable.git

# 克隆后添加第二个远程
cd pdf2searchable
git remote add github https://github.com/Terryhelium/pdf2searchable.git
```

## 配置要点

- `gitea`（私有）：用于团队协作，包含全部开发历史
- `github`（公开）：仅公开非敏感信息

> **注意**：如果仓库尚未创建，需先在 Gitea/GitHub 上创建空仓库，再执行远程添加和推送。
