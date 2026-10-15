[![License: MIT](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](../../LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-orange?style=flat-square)](https://claude.ai)

# weaver-自我迭代 — 编织者

> 跨项目记忆分层归位、全局配置审查、经验模式识别、自我进化。当 Skill 多了之后，需要"整理 Skill 的 Skill"。

## 为什么需要

- **Skill 多了会互相打架。** 配置冲突、触发词重叠、记忆分散——没人做全局视角的整理。
- **该沉淀的经验没沉淀。** 今天的踩坑教训如果只停在这段对话里，明天在另一个项目还会踩。
- **知识需要分层。** 不是所有信息都该进 CLAUDE.md，不是所有习惯都该变规则。

## 核心能力

| 能力 | 说明 |
|------|------|
| 🗂️ 分层归位 | 信息路由到 Obsidian / memory / CLAUDE.md / rules / agents |
| 🔍 配置审查 | 扫描 settings.json 权限白名单，移除过期、合并重复 |
| 🧠 经验识别 | 从历史对话中识别可复用模式 |
| 📊 自我进化 | 建议新规则、新 Skill、新 Agent |
| 🔗 子 Skill 调度 | 自动调用 file-tidy + debug-architect |

## 安装

本 Skill 属于 [weaver-evolve 技能集群](https://github.com/solplum/weaver-evolve)：

```bash
git clone https://github.com/solplum/weaver-evolve.git
cd weaver-evolve && bash install.sh
```

## 触发

| 你说 | 行为 |
|------|------|
| `编织一下` / `全局整理` | 启动全局知识整理 |
| `/weaver` / `/global-tidy` | 同上 |

## 相关项目

| 项目 | 关系 |
|------|------|
| [file-tidy](../file-tidy/) | 子 Skill — 文件归位 |
| [memory-keeper](../memory-keeper/) | 子 Skill — 记忆整理 |
| [debug-architect](../debug-architect/) | 子 Skill — 错误复盘 |
| [skill-optimizer](../skill-optimizer/) | 兄弟 — Skill 级优化 |

独立仓库：[file-tidy](https://github.com/solplum/file-tidy) · [memory-keeper](https://github.com/solplum/memory-keeper) · [debug-architect](https://github.com/solplum/debug-architect) · [skill-optimizer](https://github.com/solplum/skill-optimizer)
