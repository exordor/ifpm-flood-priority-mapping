# IFPM 工作区边界设计

更新日期：2026-06-04

## 1. 目标

这个工作区现在主要是 Codex 和用户共同探索 IFPM flood-risk modelling 项目的文档、数据清单、导师反馈和会议准备。后续会开始写代码，因此需要把“私有上下文”和“可交付代码”提前分开。

核心原则：

> 同一个 Codex workspace 可以保留完整上下文，但 Git 边界和交付边界必须分开。

## 2. 当前结构

```text
/Users/jlw/code/IFPM/
  .git/                    # 私有上下文 Git 仓库
  AGENTS.md                # Codex 工作区约束
  README.md                # 工作区索引
  workspace_boundary_design_cn.md

  context/                 # 私有项目上下文，不作为代码交付物
    docs/
      original/
      research-review/
      deep-research/
      project-analysis/
      mentor-explanation/
    assets/

  ifpm-flood-pipeline/     # 独立 Git 仓库，未来代码交付来源
    .git/
    README.md
    AGENTS.md
    pyproject.toml
    src/
    tests/
    configs/
    examples/
    docs_public/

  data/                    # 本地数据，默认不提交
  outputs/                 # 运行输出，默认不提交
  exports/                 # 打包交付物，默认不提交
```

## 3. 分类规则

| 类型 | 内容 | 位置 |
| --- | --- | --- |
| `INTERNAL_CONTEXT` | 导师要求、会议准备、文档审查、开放问题、内部判断 | `context/` |
| `DELIVERABLE` | 可复用代码、测试、公开说明、示例配置 | `ifpm-flood-pipeline/` |
| `LOCAL_DATA` | 原始 GIS 数据、下载数据、验证数据、本地样例 | `data/` |
| `OUTPUT` | 中间结果、地图、模型输出、诊断报告 | `outputs/` |
| `EXPORT` | zip、PDF、交付包 | `exports/` |

## 4. 根私有上下文仓库

可以提交：

- `AGENTS.md`
- `README.md`
- `workspace_boundary_design_cn.md`
- `context/**/*.md`
- `context/assets/images/` 中确认为内部上下文需要的小图
- `.gitignore`

禁止提交：

- `ifpm-flood-pipeline/` 的路径、gitlink 或 `.git` 内容
- `.gitmodules`
- raw GIS data、处理输出和大体量数据
- `.env`、token、私有登录态
- 自动导出的 `.pdf/.docx/.pptx/.xlsx`，除非明确决定版本化

## 5. 交付代码仓库

`ifpm-flood-pipeline/` 是独立 Git 仓库，只放未来可交付/可发布的 pipeline 代码和公开材料。

代码仓库不得依赖父目录：

- 不读取 `../context`
- 不读取 `../data` 或 `../outputs`
- 不复制导师会议策略、私有假设、未确认问题
- 不提交真实敏感 GIS 数据或本机绝对路径

## 6. 未来代码方向

当前代码仓库只是骨架。未来可能承载：

- dataset inventory normalization
- GIS preprocessing checks
- AHP-MCDA criteria and weighting utilities
- weighted overlay pipeline
- validation-window comparison utilities
- report/map export helpers

在没有确认 modelling unit、time period、validation data、dataset replacement rules 和 weighting protocol 前，不要把 exploratory notes 写成最终模型承诺。

## 7. 验证命令

根仓库检查：

```bash
git status --short
git check-ignore -v ifpm-flood-pipeline/ data/ outputs/ exports/ tmp/ .tmp/ .env
git ls-files -s ifpm-flood-pipeline
test ! -f .gitmodules
```

代码仓库检查：

```bash
git -C ifpm-flood-pipeline status --short
git -C ifpm-flood-pipeline rev-parse --show-toplevel
```

通过条件：

- 根仓库不跟踪 `ifpm-flood-pipeline/`
- `.gitmodules` 不存在
- 代码仓库 top-level 指向 `.../ifpm-flood-pipeline`
- 代码仓库不包含父目录私有路径、真实数据或私有会议内容
