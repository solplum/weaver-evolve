# 增量进度与待处理事项

需要持续增量或跨轮续接时读取。本机制只管理本技能的任务进度，不是长期记忆系统，也不扫描任何宿主历史。

## 选择位置与来源身份

在当前请求允许的持久数据目录下选择明确的 `progress.json`。沿用已有位置；不要把它写进托管记忆、规则正文或技能安装目录。一次性分析没有合适位置时，交付续接清单即可。

来源 ID 应稳定区分真实来源，如 `workspace-a:conversation-index` 或某文件的规范定位；不同来源不能复用同一 ID。游标采用当前来源实际支持的序号、提交、偏移或内容版本，并在其 JSON 对象中保留已覆盖起点和稳定筛选条件。例如 `{"covered_from":"2026-11-04","selection":"workspace-a/all-events","event":42}`；这些是调用者的覆盖描述，不是所有数据源必须实现的原生字段。

读取前比较本次范围与已有覆盖：从近七天扩大为近一月时，先补扫更早三周；项目或事件筛选变化时，补扫新纳入部分。对会改写的文件核对内容版本，不能只凭时间戳或末尾游标判断未变。旧状态缺少足够的范围信息时，重读本次约定范围，依靠候选身份和目标内容去重。完整读取后保存实际覆盖边界。

脚本只保存游标，不解释其排序、自动发现来源或判断是否真的完整读过。游标后移也不能替代覆盖证明；补扫失败仍保留旧游标，并把新增范围列为未覆盖。

## 命令

通过当前环境可用的 Python 3 解释器运行，传入实际绝对路径：

```sh
python3 <skill-dir>/scripts/progress.py show --state <data-dir>/progress.json
python3 <skill-dir>/scripts/progress.py update --state <data-dir>/progress.json --batch <batch.json>
```

`show` 只读；文件不存在时返回以下空状态，不创建目录：

```json
{"schema_version":1,"revision":0,"sources":{},"candidates":{}}
```

先处理返回的 `pending` 候选，再读新增来源。已完成候选用于识别相同事件；语义去重仍需要搜索知识落点，脚本不替代判断。

## 提交批次

从最新 `show` 结果取得 `expected_revision`，为本次实际读取的来源构造批次：

```json
{
  "expected_revision": 0,
  "sources": [
    {
      "id": "workspace-a:events",
      "coverage": "complete",
      "cursor": {"covered_from": "2026-11-04", "selection": "workspace-a/all-events", "event": 42},
      "candidates": [
        {
          "id": "workspace-a:event-40:method",
          "status": "pending",
          "evidence": "workspace-a/event-40#user-decision",
          "target": "workspace-a/docs/methods.md",
          "reason": "需要核对适用范围"
        }
      ]
    },
    {"id": "workspace-b:events", "coverage": "unavailable"}
  ]
}
```

- `complete`：本次约定范围完整读取，所有提炼候选已有明确结果或已记为 `pending`。允许更新游标。
- `partial`／`unavailable`：保留旧游标；可保存已观察到的候选。省略 `cursor`，或传入与旧值完全相同的值；不同值会报错。
- `pending`：缺证据、缺落点、待确认或执行／验证失败。独立保存，完整扫描来源可以推进，但下次仍要处理这些候选。
- `applied`：知识更新已通过目标读回或接口回执验证。
- `excluded`：无复用价值、相同内容已覆盖或明确无需处理，在 `reason` 说明原因。

候选 ID 依据来源事件和知识主题保持稳定；不因每次执行换 ID。证据引用优先采用稳定事件 ID 或文件内容版本加锚点，避免插入旧资料后行号漂移。同 ID 的来源和证据引用不可替换；原记录反映当时的观察，新版本的证据需要重审时另建候选并在原因中关联旧事项。旧候选不会因批次没列出而删除，已完成候选也不能退回 `pending`。

状态仅允许来源引用、目标引用、状态和简短原因，不复制聊天全文、凭据或私密内容。批次中的目标只是记录，脚本不会修改这些目标，也不证明知识已经保存。

## 并发与失败

脚本使用修订号检查、独占锁和原子替换。修订号冲突时重新 `show` 并合并本次结果；不能直接把旧批次的修订号改大后盲目重试。无实质变化时不写文件、不增加修订号。

写入失败保留旧状态；知识文件可能已经更新，重试前先读目标确认，避免重复写入。锁冲突时等待现有更新完成；只有确认没有活跃写入进程后才移除遗留的 `.lock`。不自动抢锁或重置状态。

进度成功提交不等于全局整理完成：仍要报告待处理候选和未覆盖来源。
