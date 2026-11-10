# lzl-weaver-evolve

跨项目整理知识、规则与经验，把值得复用的内容放到正确位置，并保留来源、适用条件和处理进度。

**所有支持技能的 Agent 使用同一套文件。** 不提供按产品区分的正文、目录或安装选项。运行时依据当前宿主提供的规则、工具、历史入口和记忆写入机制确定做法，不假定某个产品的配置路径或聊天格式。

## 能做什么

- 明确本次覆盖的项目、数据源和时间范围，区分已读、部分读取和不可读。
- 提炼稳定偏好、项目决策、成功方法、有效工具经验、用户纠正及错误教训；一次明确且重要的决定也可以保留。
- 区分执行规则、全局偏好、项目背景和通用知识，复用已有存放机制。
- 检查同一结论的适用范围、冲突、旧版本和关联引用，避免把项目例外升级为全局规则。
- 跟踪各来源的扫描位置及待处理事项；未读取的来源不前移，待确认事项不会随扫描进度丢失。
- 根据已有授权推进工作，集中提出真正影响判断的问题，交付实际变更和未完成事项。

主技能自包含。以下三个配套技能可以独立使用，也可按任务需要配合：

| 技能 | 用途 |
|---|---|
| `lzl-weaver-evolve` | 跨项目知识整理与经验提炼，主入口 |
| `memory-keeper` | 明确的记住、忘掉和记忆结构整理 |
| `file-tidy` | 按现有结构分析并归位文件 |
| `debug-architect` | 复盘已发生的错误及预防措施 |

主技能调用配套技能时传递当前范围、来源和授权；配套技能不存在或与环境不兼容时，按主技能流程继续可完成的工作。

## 安装

需要 Python 3.9+。先确认当前宿主实际加载技能的目录，将其作为 `--dest` 传入；安装器不会猜测产品或写入多个位置。

```bash
git clone https://github.com/solplum/weaver-evolve.git
cd weaver-evolve

# 查看计划；不会创建目录或修改文件
python3 scripts/install.py --dest "/path/to/your/skills" --dry-run

# 只安装主技能
python3 scripts/install.py --dest "/path/to/your/skills"

# 同时安装三个可选配套技能
python3 scripts/install.py --dest "/path/to/your/skills" --all
```

`bash install.sh` 是同一安装器的入口，参数完全相同。PowerShell 入口使用本机 Python 执行同一文件：

```powershell
.\install.ps1 -Dest "D:\path\to\skills" -DryRun
.\install.ps1 -Dest "D:\path\to\skills" -All
```

安装脚本的外壳只解决操作系统的启动方式，安装的技能文件始终相同。

### 更新、旧名迁移与备份

已存在的技能默认跳过。明确要更新时，加 `--force`：

```bash
python3 scripts/install.py --dest "/path/to/your/skills" --force
```

若目标目录中存在旧主技能 `weaver-自我迭代`，这次更新会将它备份并迁移为 `lzl-weaver-evolve`，避免新旧名字同时被加载。没有 `--force` 时保留原件，跳过主技能。

备份位于 `--dest` 父目录下的 `.lzl-weaver-evolve-backups/<时间>-<唯一标识>/`，具体绝对路径会打印出来。它在技能扫描目录之外；已有的自定义文件也随原目录完整保留。安装前会验证全部选中来源，文件复制完成后才替换目录；替换阶段失败会尝试恢复整批原目录。

需要回退时，先将当前版本移出宿主扫描范围，再把备份中的对应目录移回 `--dest`。恢复旧名时也先移出新主技能，以免重复加载。安装器拒绝源仓库与目标互相包含、符号链接目标或来源，以及非目录的既有技能路径。

## 使用

在支持显式技能引用的宿主中使用 `lzl-weaver-evolve`；也可以直接提出自然语言请求：

```text
使用 lzl-weaver-evolve，整理这两个项目过去一周的知识和决策。
全局整理：先查看上次未完成事项，再处理新增内容。
把近期有效的工作方法提炼出来，保留适用条件和来源。
```

仅要求评估时交付候选和建议；明确授权整理时按授权执行。宿主托管或自动生成的记忆遵循其指定接口，不直接改写生成文件。缺少历史入口时报告实际覆盖范围，使用可用来源，不把局部检查宣称为全局完成。

## 仓库结构与验证

```text
skills/
  lzl-weaver-evolve/   # 唯一主技能正文与按需引用的资源
  memory-keeper/       # 可选配套，单一版本
  file-tidy/           # 可选配套，单一版本
  debug-architect/     # 可选配套，单一版本
scripts/install.py    # 统一安装器
install.sh            # 启动入口
install.ps1           # 启动入口
tests/                # 安装及状态处理等行为验证
```

`skills/skill-optimizer` 是保留的历史独立内容，不在这四个技能的安装清单中。

```bash
python3 -m unittest discover -s tests -v
bash -n install.sh
```

测试使用隔离的临时目录，不读取真实聊天、修改实际记忆或操作在线系统。安装行为覆盖干跑、默认与全套安装、已有副本保护、旧名迁移、备份、故障回滚及路径边界；技能判断质量还需通过具体任务和原始材料独立验证。

## 许可证

[MIT](LICENSE)
