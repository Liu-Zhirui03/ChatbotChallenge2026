# 每次提交 ZIP：固定指令与打包白名单

适用：当前 `submission_repo` 的**评测运行包**。不是整个项目备份，也不是图片采集资料包。
不要右键压缩整个项目或整个 `submission_repo`；不要复用之前的 ZIP。

## 下次直接给助手的指令

> 请按照 `docs/submission-zip-guide.md`，把当前 `submission_repo` 打包为新的评测 ZIP。
> 只包含本文白名单文件，使用当前数据库，不重新抓取、描述、向量化或重建数据库。
> 不修改、删除原文件，不覆盖旧 ZIP，不切换分支，不 commit 或 push。
> 将 main.py 放在 ZIP 根目录，排除密钥、虚拟环境、图片原件、缓存、测试题、报告和其他 ZIP。
> 打包后校验 ZIP 完整性及文件清单，确认数据库与源文件一致。
> 最后告诉我 ZIP 的绝对路径、大小、所用 Git 提交和是否存在未提交修改。
> 如果必需文件缺失、数据库正在写入或文件在打包期间发生变化，停止并说明原因，不交付不完整包。

## 包含哪些文件

| 白名单 | 原因 |
|---|---|
| `main.py`、`requirements.txt`、`check_setup.py` | 入口、依赖和环境检查工具 |
| `bot/` 内的 `.py` 文件 | 回答、检索和模型访问代码 |
| `build/` 内的 `.py`、`.txt` 文件 | 项目构建工具；不包含其运行产物 |
| `data/chroma/` 内的 SQLite 和完整配套向量文件 | 已建好的向量数据库，必须一起打包 |
| `data/text_search.sqlite`、`data/image_search.sqlite` | 文字和图片的关键词索引 |
| `data/knowledge/entities.json`、`facts.json`、`glossary.json` | 实体、事实和查询扩展 |
| `data/image_evidence/records.json`、`sources.json` | 当前图片证据及溯源信息 |

Chroma 当前持久化文件为 `.sqlite3`、`.bin`、`.pickle`。若版本升级产生其他格式，
先检查并更新白名单，不能悄悄漏掉未知文件。不能只打包 `chroma.sqlite3`。

以下内容**不打包**：

- `.env`、密钥、`.venv/`、`venv/`、`.git/`、`__pycache__/`、`.pyc`。
- 所有旧 `.zip`，包括 `submission.zip`、`submission_repo-1020.zip`。
- `eval/`、`tests/`、`dev_set.json`、测试答案、benchmark 报告。
- `Labs/`、`Slides/`、`docs/`、`artifacts/`。
- `image_source/`、`image_hzq/`、`prompt/`、`prompt_from_web/`。
- `data/web_academy/`、`data/raw_pages/`、`data/processed/`、`data/image_pilot/`。
- `data/pages.json`、`images.json`、`descriptions.json` 等已处理的原始输入。
- embedding 缓存、`curated_backups/`、锁文件、日志、入库回执和临时文件。

运行包利用已有索引回答问题，不需要原图和爬取资料；这些资料仍应另外保留在开发项目中。
包内构建工具不代表此运行包拥有重新采集、描述和建库所需的全部原始资料。
密钥和环境配置由运行环境另外提供，不能通过把 `.env` 放进 ZIP 的方式解决。

## 手动执行：复制整个 PowerShell 代码块

先停止正在执行的入库、数据库更新和 chatbot 进程。下面命令：

- 使用主目录当前文件，包括尚未提交的修改；记录对应 Git 状态。
- 从白名单直接写 ZIP，不创建可能混入旧文件的临时项目目录。
- 将包放在项目旁的 `submission_packages/`，因此不会把 ZIP 自己再打进去。
- 不调用 API、不删除文件、不修改数据库。

```powershell
cd D:\Project\Innowing_Project\ChatbotChallenge2026\submission_repo
$py = '.\.venv\Scripts\python.exe'
@'
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import subprocess
import zipfile

root = Path.cwd().resolve()
repo = root.parent
assert root.name == "submission_repo", "Run from submission_repo"
required = [
    "main.py", "requirements.txt", "check_setup.py",
    "data/chroma/chroma.sqlite3",
    "data/text_search.sqlite", "data/image_search.sqlite",
    "data/knowledge/entities.json", "data/knowledge/facts.json",
    "data/knowledge/glossary.json",
    "data/image_evidence/records.json", "data/image_evidence/sources.json",
]
files = {root / name for name in required}
for folder, suffixes in [("bot", {".py"}), ("build", {".py", ".txt"})]:
    assert (root / folder).is_dir(), "Missing code directory: " + folder
    files.update(p for p in (root / folder).rglob("*")
                 if p.is_file() and p.suffix in suffixes
                 and "__pycache__" not in p.parts)
assert (root / "bot/answer.py") in files, "Missing bot/answer.py"
for p in (root / "data").rglob("*"):
    if p.is_file() and p.name.endswith(("-wal", "-journal", "-shm")):
        if p.stat().st_size:
            raise RuntimeError("Database sidecar present; resolve safely before packaging: " + str(p))
for p in (root / "data/chroma").rglob("*"):
    if not p.is_file():
        continue
    if p.suffix not in {".sqlite3", ".bin", ".pickle"}:
        raise RuntimeError("Unknown Chroma file; review whitelist: " + str(p))
    files.add(p)
assert any(p.suffix == ".bin" for p in files), "Missing Chroma vector files"

def digest_file(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

inventory = {}
for p in sorted(files):
    assert p.is_file(), "Missing required file: " + str(p)
    assert not p.is_symlink(), "Do not package symlinks: " + str(p)
    p.resolve().relative_to(root)
    name = p.relative_to(root).as_posix()
    assert not any(part.startswith(".") for part in Path(name).parts)
    inventory[name] = {"bytes": p.stat().st_size, "sha256": digest_file(p)}

commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=repo, text=True).strip()
status = subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True)
if os.environ.get("PACKAGE_DRY_RUN") == "1":
    print(json.dumps({"files": len(inventory), "commit": commit, "branch": branch,
                      "dirty": bool(status.strip()), "api_calls": 0}))
    raise SystemExit(0)

stamp = datetime.now(timezone(timedelta(hours=8))).strftime("%Y%m%d-%H%M%S-%f")
destination = repo.parent / "submission_packages"
destination.mkdir(exist_ok=True)
archive = destination / ("submission-" + stamp + "-" + commit[:7] + ".zip")
manifest = {
    "created_at_asia_shanghai": stamp, "git_commit": commit, "git_branch": branch,
    "git_status": status.splitlines(), "files": inventory,
    "note": "Working-tree runtime package; no API calls or database rebuild.",
}
with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as z:
    for name in inventory:
        z.write(root / name, name)
    z.writestr("PACKAGE_MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None, "ZIP integrity failure"
    assert set(z.namelist()) == set(inventory) | {"PACKAGE_MANIFEST.json"}
    assert "main.py" in z.namelist(), "main.py must be at ZIP root"
    for name, expected in inventory.items():
        with z.open(name) as stream:
            archived_hash = hashlib.file_digest(stream, "sha256").hexdigest()
        assert archived_hash == expected["sha256"], "File changed during packaging: " + name
        assert digest_file(root / name) == expected["sha256"], "Source changed: " + name
print("VERIFIED ZIP:", archive)
print("SIZE MiB:", round(archive.stat().st_size / 1024**2, 2))
print("COMMIT:", commit, "BRANCH:", branch, "UNCOMMITTED CHANGES:", bool(status.strip()))
'@ | & $py -
if ($LASTEXITCODE -ne 0) { throw 'Packaging failed. Do not submit an unverified ZIP.' }
```

需要 Python 3.11+；当前项目环境为 Python 3.13。仅输出 `VERIFIED ZIP` 且命令成功结束的包可交付。
如果中途失败，可能留下未验证的 ZIP；不要提交它，修复原因后重新执行会生成新名字。
不要直接删除数据库的 WAL/journal 文件来绕过检查。

## 打包后最后确认

1. ZIP 根目录有 `main.py`，不是 `ChatbotChallenge2026/submission_repo/main.py`。
2. 有完整 `data/chroma/`、两个关键词索引及知识 JSON。
3. 没有 `.env`、虚拟环境、测试题、原图和嵌套 ZIP。
4. `PACKAGE_MANIFEST.json` 记录了这次包的文件哈希、Git 版本和未提交状态。
5. 打包成功只证明文件完整，**不代表 API 可用或 benchmark 已通过**。
   需要验证回答时，应在独立解压目录配置环境并运行 `main.py`，不要把密钥再打回包中。

这里不自动 push，不自动上传评测平台，也不更改当前分支。
