# 🎮 DeepRenPyTrans

**基于人工智能的 Ren'Py 视觉小说游戏通用自动翻译工具。**

🌐 [English](README.md) | [Русский](README.ru.md) | [Español](README.es.md) | [Português](README.pt.md) | [Deutsch](README.de.md) | [Français](README.fr.md) | [简体中文](README.zh.md)

---

无需修改游戏源码，即可使用 DeepSeek（包括 `deepseek-v4-flash` / `deepseek-v4-pro`）、OpenAI 或本地大语言模型（LLM）将任何 Ren'Py 游戏翻译为任意语言。

---

## ✨ 功能特性

- **🔍 智能提取** — 自动识别并提取 `.rpy` 文件中的所有可翻译文本，过滤代码、变量 ID 和调试日志。
- **🤖 智能翻译** — 支持基于 DeepSeek、OpenAI 或本地 Ollama 模型的智能分批翻译，结合场景/章节上下文以保证翻译准确度。
- **🔌 动态注入** — 零源码修改，通过 Ren'Py 内置的 `config.replace_text` 实现运行时的动态文本替换。
- **📊 质量审计** — 查找未翻译文本、冗余翻译、空译文以及垃圾代码项。
- **🧹 字典清理** — 自动清除字典中的测试字符串、文档注释以及编程残留项。
- **⚡ 增量更新** — 支持断点续传，只处理新增或缺失的文本字符串。
- **📱 跨平台** — 兼容 PC 版、Android 移动版（APK 资源注入）及 iOS 版。

## 🚀 快速上手

### 1. 安装

```bash
git clone https://github.com/Danko-Novak/DeepRenPyTrans.git
cd DeepRenPyTrans

# 方法 A：作为包安装（推荐 — 会在系统中注册 `deeprenpytrans` 命令）
pip install -e .

# 方法 B：仅安装依赖项
pip install -r requirements.txt
```

> 安装完成后，您可直接使用 `deeprenpytrans` 命令，而无需键入 `python -m deeprenpytrans`。

### 2. 配置

```bash
# 复制示例配置文件
cp .env.example .env
cp config.example.yaml config.yaml

# 编辑 .env 文件，填入您的 API 密钥
# 编辑 config.yaml 文件，配置您的游戏路径与目标翻译语言
```

您可以通过以下两种方式运行该工具：

#### 方法 A：Web 可视化控制台 (推荐)
启动本地 Web 服务器，在浏览器中使用高级玻璃质感界面管理设置、切换打包标志并执行所有操作：
```bash
python gui_server.py
```
程序会自动在浏览器中打开 `http://localhost:8000`。

#### 方法 B：命令行界面 (CLI)
```bash
# 步骤 1：提取游戏中的文本字符串
python -m deeprenpytrans extract --game "./MyGame/game"

# 步骤 2：使用人工智能进行翻译
python -m deeprenpytrans translate --strings strings_by_file.json --dict "./MyGame/game/tl/chinese/dictionary.json"

# 步骤 3：生成运行时挂钩 (hooks.rpy)
python -m deeprenpytrans inject --game "./MyGame/game" --lang chinese
```


## 📖 命令详解

### `extract` — 查找并提取可翻译文本

```bash
python -m deeprenpytrans extract --game ./MyGame/game --output strings.json
```

遍历所有 `.rpy` 文件，提取双引号文本，并应用智能过滤器以过滤：
- 游戏内部 ID（如 `ITM_Sword`, `LOC_Bridge`, `ACT_NPC01`）
- Python 逻辑代码及断言判断
- 文件路径及十六进制颜色代码
- 调试输出与日志信息
- 已经完成翻译的目标语言字符

参数选项：
| 选项 | 说明 |
|------|-------------|
| `--game PATH` | 游戏根目录下的 `game/` 文件夹路径 |
| `--output FILE` | 输出的 JSON 字典文件路径（默认：`strings_by_file.json`） |
| `--include-log PATH` | 合并来自 `untranslated.log` 日志中的未翻译行 |

### `translate` — AI 自动翻译

```bash
python -m deeprenpytrans translate --strings strings.json --dict dictionary.json
```

将文本分批（根据源文件进行上下文分组）发送至 AI 接口。
支持增量翻译：自动忽略已翻译好的词条。

### `audit` — 翻译质量审计

```bash
python -m deeprenpytrans audit --dict dictionary.json --strings strings.json
```

生成一份详细的审计报告，包含：
- ❌ 未翻译项（源文件中存在，但字典中缺失）
- 👻 冗余项（字典中存在，但源文件中已删除）
- 🔁 键值等同项（可能遗漏翻译的文本）
- 📭 空值项
- 🗑️ 垃圾残留（代码片段、调试消息等）

### `clean` — 字典垃圾清理

```bash
python -m deeprenpytrans clean --dict dictionary.json --dry-run
python -m deeprenpytrans clean --dict dictionary.json --remove-orphaned
```

参数选项：
| 选项 | 说明 |
|------|-------------|
| `--dry-run` | 预览即将被清理的词条（不执行写入） |
| `--keep-junk` | 保留测试调试/技术类字符串 |
| `--remove-orphaned` | 同时删除游戏中已不存在的冗余译文 |

### `inject` — 生成 hooks.rpy 运行时脚本

```bash
python -m deeprenpytrans inject --game ./MyGame/game --lang chinese
```

生成 `hooks.rpy` 脚本，用于：
- 在游戏启动时加载 `dictionary.json` 译文。
- 通过内置 `config.replace_text` 动态替换屏幕文本。
- 将游戏过程中遇到的未翻译词条实时输出至 `untranslated.log`。
- 添加热键，支持在游戏中一键开启/关闭翻译对照。
- 自动重写游戏字体，使之支持目标语言。

## ⚙️ 配置参数

### `config.yaml`

```yaml
game_dir: "./MyGame/game"
target_language: "Chinese"
translation_dir: "chinese"

api:
  provider: "deepseek"    # 或 "openai", "ollama"
  model: "deepseek-chat"  # 支持最新的 deepseek-v4-flash / deepseek-v4-pro
  temperature: 0.2
  batch_size: 40

fonts:
  default: "DejaVuSans.ttf"
  replacements:
    "OriginalFont.ttf": "DejaVuSans.ttf"

extraction:
  skip_prefixes: ["ITM", "ACT", "LOC", "QST"]
  force_include: ["Q.Save", "Q.Load"]
```

### `.env`

```bash
DEEPSEEK_API_KEY=sk-your-key-here
# 或
OPENAI_API_KEY=sk-your-openai-key
```

## 🏗️ 工作原理

```
┌────────────────┐     ┌──────────────┐     ┌────────────────┐
│  .rpy 脚本文件 │────▶│  文本提取器  │────▶│  strings.json  │
│  (游戏源代码)  │     │   (过滤器)   │     │ (按脚本文件)   │
└────────────────┘     └──────────────┘     └───────┬────────┘
                                                    │
                                                    ▼
┌────────────────┐     ┌──────────────┐     ┌────────────────┐
│   翻译字典     │◀────│ 自动翻译器   │◀────│  API 接口模型  │
│   .json        │     │  (分批处理)  │     │ (DeepSeek/etc) │
└───────┬────────┘     └──────────────┘     └────────────────┘
        │
        ▼
┌────────────────┐     ┌──────────────┐
│   hooks.rpy    │────▶│  Ren'Py 游戏 │ ← 玩家在游戏界面看到译文！
│ (运行时加载)   │     │  (运行时)    │
└────────────────┘     └──────────────┘
```

## 📱 移动端部署

### Android (APK 自动打包注入)
1. 使用我们提供的自动化脚本 `build_apk.bat`，它将自动完成所有工作：
   - 自动解压老版本 APK 游戏包。
   - 自动恢复原 APK 中的压缩资源，最多可缩减 60% 的包体体积（平均节省 400-500 MB 空间）。
   - 自动将音频文件进行 wav 至 ogg 压缩。
   - 自动优化新图片资源，跳过已缩减的原图。
   - 使用 7z 最高压缩率重新封包并进行自动签名。
2. **自定义参数构建**：您可以通过修改 `build_apk.bat` 文件头部的配置标志（Flags）来自定义构建行为：
   - `RESTORE_OLD_ASSETS` (1/0)：开启/关闭从旧 APK 恢复已压缩资产的功能。
   - `COMPRESS_AUDIO` (1/0)：开启/关闭音频 wav-to-ogg 转换及脚本路径自动修正。
   - `COMPRESS_IMAGES` (1/0)：开启/关闭新图片资源的优化压缩。
   - `INJECT_TRANSLATION` (1/0)：开启/关闭注入翻译文件。设为 `0` 将直接构建一个纯净的原版语言（英文等）Android 移植版。
   - `LANG_FOLDER`：目标语言包在 `game/tl/` 下的文件夹名称（如 `russian`，`chinese` 等）。
   - `COMPRESSION_LEVEL` (0-9)：7z 打包时的压缩级别（9 为最高极限压缩，0 为仅存储）。
3. 手动打包：使用 7zip 解包，将翻译文件放入 `assets/x-game/game/` 目录，清理 `META-INF/` 签名并重封包签名。

### iOS
1. 在 Ren'Py Launcher 中生成 Xcode 渲染工程。
2. 将 `tl/chinese/` 语言包放入工程项目中。
3. 编译并部署至您的 iOS 设备。

## ⚠️ 重要说明与局限性

- **测试状况**：目前该工具仅在一款特定的游戏上进行了完整测试与验证，确保翻译、资源压缩与封包无误。
- **游戏代码差异**：虽然我们的目标是打造完美的通用翻译工具，但由于不同 Ren'Py 游戏使用的代码规范、自定义前缀与脚本结构差异巨大，在翻译其他游戏时，**很可能**需要针对目标游戏代码对过滤器和提取规则进行微调。
- **不懂编程？**：如果您不具备编程基础或没有时间调试代码，我们强烈建议您配合使用基于人工智能的编程助手（如 **Antigravity**、**Cursor** 等），这些工具可以快速帮您完成对提取器及规则过滤器的定制化修改。

## 🤝 参与贡献

欢迎大家提交 Pull Request！我们目前需要以下方面的帮助：
- 集成更多的大模型 API 供应商。
- 完善和测试中日韩（CJK）语言支持。
- 改进针对特定游戏特异代码的文本提取启发算法。

## 🗺️ 开发路线图与特性

我们会在 GitHub 的 **Discussions** (讨论) 板块追踪开发进度并规划新特性。如果您有好的想法或希望请求某个新功能，请前往 Discussions 提交您的建议或为已有的点子投票！

| 功能特性 | 票数 | 状态 | 进度 |
| :--- | :--- | :--- | :--- |
| **GUI Web 仪表盘控制台** | - | 🚀 已发布 | `[████████████████████]` 100% |
| **Android APK 封包与优化器** | - | 🚀 已发布 | `[████████████████████]` 100% |
| **本地大模型与 Ollama 支持** | - | 🚀 已发布 | `[████████████████████]` 100% |
| **macOS & Linux 运行支持** | 0 | 📋 规划中 | `[██░░░░░░░░░░░░░░░░░░]` 10% |
| **中日韩（CJK）翻译质量校验** | 0 | 📋 规划中 | `[█░░░░░░░░░░░░░░░░░░░]` 5% |

---

## 💖 支持与赞助

DeepRenPyTrans 是一款出于兴趣开发、旨在简化视觉小说翻译流程的开源工具。如果它为您节省了时间或帮助您将喜爱的游戏带给了更广泛的受众，欢迎支持本项目的开发！

我目前使用的是一套基础开发设备，并计划将其升级为在 Linux 下搭载 ROCm 的专用本地 AI 工作站。这将实现对本地大语言模型（LLM）的原生高速测试与优化。

**当前筹款进度：** 0 / 1,200 USD

### 🚀 硬件升级阶梯：
* **第一阶段：显卡升级 ($850)** — 升级为 24GB 显存的 AMD Radeon 显卡（例如 RX 7900 XTX 或同等性能的下一代显卡），用于在 Linux ROCm 环境下本地运行大型本地大模型（如 14B/32B/70B 模型）。
* **第二阶段：存储升级 ($150)** — 升级为高速 2TB PCIe 4.0 NVMe 固态硬盘。本地大模型需要占用大量硬盘空间（每个模型 5GB 至 40GB+），我目前使用的 500GB 硬盘已满。
* **第三阶段：内存升级 ($150)** — 额外加装 32GB 内存（使总内存达到 64GB），以便运行并行工作流、高负载 IDE 多任务，以及支持将超大模型的部分权重卸载到内存中运行。
* **日常维护：API 测试基金 ($50)** — 用于在翻译质量评估和新功能测试中，支付商业 API（如 DeepSeek、OpenAI、Claude）小额使用费用的预留资金。

### 如何帮助：
* **点亮 Star：** 为项目提供更多曝光，鼓励我继续写代码！
* **参与贡献：** 反馈 Issues、提出新功能想法或直接提交 PR。
* **赞助 (USDT - TON / TON 网络)：**
  `UQBdHUyR8nG5p_Rwhw_Rtmgc7QJdJ-G5nOPJa7Pq0mh2A27K`

## 📄 开源协议

本项目采用 GNU AGPL v3 协议开源 — 详见 [LICENSE](LICENSE) 文件。
