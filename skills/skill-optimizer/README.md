[![License: MIT](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](../../LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-orange?style=flat-square)](https://claude.ai)

# skill-optimizer — Skill 优化器

> 分析对话 → 识别改进点 → 置信度分级 → 长期复利滤网 → 用户确认后修改。元技能。

## 为什么需要

- skill 用久了会腐烂：触发词不准、流程冗余、内容过时
- 改 skill 全靠直觉，没有系统化分析框架
- 盲目修改带来长期副作用——为今天的对话加补丁，明天就后悔

## 核心管线

| 阶段 | 说明 |
|------|------|
| 🔍 上下文采集 | 分析 skill 的触发/执行/纠正事件 |
| 🔬 条件复盘 | 自动调用 [debug-architect](../debug-architect/) 获取硬证据 |
| 📐 三维审查 | 触发准确度 + 内容质量 + 工作流效率 |
| 📊 置信度分级 | [高] / [中] / [低] 三档 |
| ⚔️ 对抗验证 | 中置信度由独立 agent 反向论证 |
| 🧹 长期复利滤网 | 三问 + 五条红线，拦截短期补丁 |
| ✅ 用户决策 | 结构化报告，逐条/批量确认 |
| 🛡️ 安全执行 | 修改后自检，失败自动回滚 |

## 安装

本 Skill 属于 [weaver-evolve 技能集群](https://github.com/solplum/weaver-evolve)：

```bash
git clone https://github.com/solplum/weaver-evolve.git
cd weaver-evolve && bash install.sh
```

单独安装：

```bash
git clone git@github.com:solplum/skill-optimizer.git ~/.claude/skills/skill-optimizer/
```

## 触发

| 用户说 | 行为 |
|--------|------|
| `优化 skill` / `skill 优化` | 全局扫描 |
| `XX skill 有问题` | 指定目标 |

## 依赖

- 可选：[debug-architect](../debug-architect/) — 硬证据引擎，不可用时自动降级
