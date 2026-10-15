[![License: MIT](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](../../LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-orange?style=flat-square)](https://claude.ai)

# file-tidy v2 — 文件整理师

> 结构感知归位：学习项目已有目录结构，帮跑错地方的文件回到该去的子目录。

## v2 核心变化

| v1 | v2 |
|----|----|
| 按扩展名归类（*.py → scripts/） | 按项目结构判断归属 |
| 内置默认规则驱动 | AI 结构感知驱动 |
| .tidy-rules.yaml 是引擎 | .tidy-rules.yaml 是辅助配置 |
| 不确定时按规则硬归类 | 不确定就放着 |

## 安装

本 Skill 属于 [weaver-evolve 技能集群](https://github.com/solplum/weaver-evolve)：

```bash
git clone https://github.com/solplum/weaver-evolve.git
cd weaver-evolve && bash install.sh
```

单独安装：

```bash
git clone https://github.com/solplum/file-tidy.git
cp -r file-tidy/ ~/.claude/skills/file-tidy/
```

## 使用

```
整理文件                     # 干跑模式，展示计划
整理文件 --confirm           # 执行全部建议
整理文件 --safe              # 只执行高置信度项
整理文件 --classify          # 只移动高置信度，不执行删除
```

项目配置见 [references/rules-schema.md](references/rules-schema.md)。

## 被 weaver 调用

[weaver-自我迭代](../weaver-自我迭代/) 在全局整理时调用 file-tidy：
1. 干跑扫描 → 四档计划 → 嵌入 weaver 摘要
2. 用户确认 → weaver 调用 file-tidy 执行
