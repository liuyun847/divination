# divination

三枚铜钱法起卦 CLI 工具，本地预置 64 卦数据，调用 OpenAI 兼容 API 进行 AI 解卦。

## 功能

- 模拟三枚铜钱抛掷 6 次，生成六十四卦本卦
- 自动识别变爻（老阴/老阳），计算变卦
- 调用兼容 OpenAI 接口的 AI 模型解读卦象
- 支持有问题求卦和无问题通用解卦两种模式
- 终端彩色输出，支持 `--no-color` 关闭

## 安装

需要 Python 3.12+。

```bash
# 克隆仓库
git clone https://github.com/liuyun847/divination.git
cd divination

# 用 uv 安装依赖
uv sync
```

## 配置

在项目目录创建 `config.json`（或放在 `~/.divination/config.json`）：

```json
{
    "base_url": "https://api.deepseek.com/v1",
    "api_key": "sk-your-api-key",
    "model": "deepseek-chat"
}
```

也可通过命令行参数指定：

```bash
uv run divination --base-url https://api.openai.com/v1 --api-key sk-xxx --model gpt-4o
```

## 使用

```bash
# 带问题求卦
uv run divination "我最近换工作合适吗？"

# 无问题求卦
uv run divination

# 关闭彩色输出
uv run divination "财运如何？" --no-color
```

## 项目结构

```
divination/
├── casting.py          # 起卦逻辑（投掷铜钱、变爻计算）
├── gua_data.py         # 六十四卦基础数据
├── interpreter.py      # AI 解卦（提示词构建、API 调用）
├── divination.py       # CLI 主入口
├── test_divination.py  # 测试
├── config.example.json # 配置文件模板
├── pyproject.toml      # 项目配置
└── uv.lock             # 依赖锁文件
```

## 测试

```bash
uv run pytest test_divination.py -v
```

## License

MIT