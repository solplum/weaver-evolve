# `.tidy-rules.yaml`

可选的目录语义提示。用户请求与当前生效规则优先，文件不是授权来源。无需为了使用技能创建配置。

```yaml
directories:
  "outputs/movie/": ["电影", "视频", "movie"]
  "scripts/": ["脚本", "automation"]
safe_zones:
  - ".git/**"
  - "node_modules/**"
  - "*.key"
keep_at_root:
  - "README.md"
  - "package.json"
  - "pyproject.toml"
junk:
  - pattern: "*.tmp"
    reason: "可能的临时文件，需核实用途"
```

- `directories`：相对目标根的已有目录及用途关键词，不授权创建目录。
- `safe_zones`：使用标准 glob 匹配的保护范围，既不移动也不递归读取内容。无配置时也保护版本元数据、代理配置/记忆/技能位置、依赖缓存、凭据与数据库。
- `keep_at_root`：根目录职责文件，即使主题匹配子目录也保留。
- `junk`：只提供候选线索；执行删除取决于实际用途和用户授权。

读取时检查 YAML 可解析、目录在目标根内、规则类型合理。未知字段报告并忽略，不猜测其含义。拒绝绝对目标路径、`..` 越界和通过符号链接越界。保护规则优先于移动或垃圾候选规则。
