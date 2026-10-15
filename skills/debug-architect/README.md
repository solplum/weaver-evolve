[![License: MIT](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](../../LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-orange?style=flat-square)](https://claude.ai)

# debug-architect — 调试建筑师

> 项目完成后扫描报错、分析根因、归档教训、生成预防规则、检测技能漏洞。

## 为什么需要

- 项目做到最后，各种报错散落在对话历史里，没人总结
- 同一个坑反复踩，因为没归档、没规则、没预警
- skill 有漏洞但没人发现——直到下一次报错

## 核心功能

| 步骤 | 说明 |
|------|------|
| 🔍 扫描提取 | 从 sessions 自动搜索所有报错信号 |
| 📊 分类归类 | 语法 / 配置 / 逻辑 / 环境 / 第三方 |
| 🎯 根因分析 | 三层：直接原因 → 深层原因 → 预防缺口 |
| 📈 置信度分级 | 🟢🟡🔵⚪ 四象限，不同等级不同策略 |
| 📝 归档写入 | ERROR_LOG.md + memory/ + wiki/ |
| 🛡️ 预防建议 | 按置信度决定是否写入 CLAUDE.md 规则 |
| 🔎 技能漏洞 | 检测规则缺失、边界遗漏、检查缺失 |

## 安装

本 Skill 属于 [weaver-evolve 技能集群](https://github.com/solplum/weaver-evolve)：

```bash
git clone https://github.com/solplum/weaver-evolve.git
cd weaver-evolve && bash install.sh
```

单独安装：

```bash
git clone https://github.com/solplum/debug-architect.git
cp -r debug-architect/ ~/.claude/skills/debug-architect/
```

## 触发

```
命令：/error-review
关键词："复盘错误"、"错误复盘"、"分析报错"、"回顾错误"、"总结错误"
```

## 被 weaver 调用

[weaver-自我迭代](../weaver-自我迭代/) 在全局整理时调用 debug-architect，范围限定为本次增量 sessions。

## 依赖

- 可选：[memory-keeper](../memory-keeper/) — 归档写入时调用
