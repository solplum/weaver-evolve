[![License: MIT](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](../../LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-orange?style=flat-square)](https://claude.ai)

# memory-keeper — 即时记忆管理

> 融入而非追加：找到已有相关内容在原处更新，不是文末加一行。

## 为什么需要

- weaver 是**定期批量整理**，memory-keeper 是**即时单条响应**
- 你说"记住这个"，它立即判断放哪、怎么融入、周边要不要整理
- 你说"忘掉那个"，它搜索、确认、删除、整理残骸

## 核心功能

| 功能 | 说明 |
|------|------|
| 💾 记住 | 7 步：层级 → 类型 → 搜索 → 展示 → 确认 → 写入 → 整理 |
| 🗑️ 忘掉 | 6 步：搜索 → 展示 → 分析影响 → 展示影响 → 确认 → 删除 |
| 🔧 融入规则 | 8 条：先搜后写 / 更新优于追加 / 矛盾以新为准 / ... |
| 📋 6 种类型 | 偏好习惯、工具选择、项目决策、踩坑记录、个人特性、事实信息 |
| 🌐 修改范围 | memory + settings.json + CLAUDE.md 等配置文件 |

## 安装

本 Skill 属于 [weaver-evolve 技能集群](https://github.com/solplum/weaver-evolve)：

```bash
git clone https://github.com/solplum/weaver-evolve.git
cd weaver-evolve && bash install.sh
```

单独安装：

```bash
git clone https://github.com/solplum/memory-keeper.git
cp -r memory-keeper/ ~/.claude/skills/memory-keeper/
```

## 触发

**记住：** "帮我把...加入记忆"、"你要记住..."、"以后也要记住"、"记住..."

**忘掉：** "忘了..."、"不用再记..."、"删掉...的记忆"、"清除..."

> 分层决策指南：`../weaver-自我迭代/references/layer-guide.md`

## 与 weaver 的关系

| | memory-keeper | weaver-自我迭代 |
|------|---------------|-------------|
| 触发 | 实时 | 定期 |
| 粒度 | 单条即时 | 批量历史 |
| 删除 | 确认后+整理 | 矛盾+扫描 |
