# Singapore AI Radar

新加坡 AI 活动信息雷达：每周收集新加坡的 AI Meetup、Workshop、黑客松和讲座，整理后发布到小红书和社群。

网站：https://magicmajie.github.io/sg_ai_radar/

## 目录

| 目录 | 内容 | 维护者 |
|---|---|---|
| `events/` | 活动数据，每个活动一个文件 | ChatGPT |
| `issues/` | 每期范围、文案、图片和完成报告 | ChatGPT |
| `assets/backgrounds/` | 可复用的背景图 | ChatGPT |
| `docs/` | 数据、生图、个人报告规范与示例 | Claude |
| `site/` | 网站样式和脚本 | Claude |
| `scripts/build_site.py` | 从 `events/`、`issues/` 生成网站 | Claude |
| `.github/workflows/` | 自动构建和部署到 GitHub Pages（推送后、每天 00:05 新加坡时间） | Claude |
| `issues/*/publish/` | 发布素材包（待建） | Claude |

**提交数据前请先阅读 [docs/DATA_SPEC.md](docs/DATA_SPEC.md)。**

> 本仓库是公开的。个人活动报告不存放在本仓库，见 [docs/PERSONAL_REPORT_SPEC.md](docs/PERSONAL_REPORT_SPEC.md)。

## 本地预览网站

```bash
pip install pyyaml
python3 scripts/build_site.py
python3 -m http.server 8765 --directory _site
```

构建时发现的数据问题（缺必填字段、YAML 写错等）会打印为警告，对应文件会被跳过，不影响整个网站。
