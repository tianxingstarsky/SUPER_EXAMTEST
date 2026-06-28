# 🎓 SUPER_EXAMTEST

> 一个超好用的、基于多模态大模型 API 的计算机机考考试神器  
> **截图即答 · 全局热键 · 顶部悬浮显示 · 零依赖即插即用**

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Stable-brightgreen)
![Size](https://img.shields.io/badge/Overlay-30MB-orange)

---

## ✨ 项目简介

`SUPER_EXAMTEST` 是一款专为「在线计算机考试」场景设计的 AI 答题悬浮助手。
它会在屏幕顶部显示一条**白色半透明、略暗、点击穿透**的悬浮横条，
用户按全局热键即可截屏发题给多模态大模型，模型把**最简答案**回填到横条上。

核心特色：

- 🎯 **单文件交付** — `overlay.exe`（30 MB，PyInstaller 自包含），U 盘拷走即用，目标机无需安装 Python
- 🤫 **隐蔽显示** — 26 px 高 / 12 号浅灰半透明字 / 黑色细描边 — 不抢眼但可读
- ⚡ **全局热键** — 任何窗口、任何全屏应用下都能触发（注册系统级热键，浏览器拦不住）
- 🖱️ **点击穿透** — `WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE` 让鼠标事件直达底层窗口，悬浮条不抢焦点
- 📌 **永远置顶** — 后台每 800 ms 调 `SetWindowPos(HWND_TOPMOST)` 维持，压过浏览器独占全屏
- 🧠 **多题自动编号** — prompt 让大模型按 `题号. 答案 || 题号. 答案` 输出，单行展示
- 🏷️ **结构化约束** — `<answer>...</answer>` 索引式格式，正则提取，模型啰嗦再多也只取最终答案
- ✂️ **剪贴板缓存** — 非连续文本可多次收集后批量解题；长答案自动写入剪贴板供粘贴
- 🔧 **配置即改** — 模型/API Key/prompt 全部走 `config.json`，热更新

---

## 🚀 快速开始

### 方式一：开箱即用（推荐）

1. 在 [Releases](../../releases) 页下载最新版 `overlay.exe` 与 `config.json`、`run.cmd`、`stop.cmd`（共 4 个文件）
2. 解压到任意目录（U 盘亦可），保证它们在同一个文件夹下
3. 双击 `run.cmd`
4. 屏幕顶部出现悬浮横条，显示就绪提示
5. 按热键开始答题

### 方式二：从源码构建

> 需要本机有 Python 3.11+ 以及 PyInstaller

```powershell
pip install pillow requests pynput pyinstaller
pyinstaller --noconfirm --onefile --windowed --name overlay overlay.py
```

生成的 `overlay.exe` 会出现在 `dist/` 目录下，把它和 `config.json` 拷在一起即可。

---

## ⌨️ 快捷键

| 快捷键 | 功能 | 说明 |
|---|---|---|
| `Ctrl+Shift+1` | **截屏答题** | 截全屏 → 多模态大模型识别题目 → 顶部横条显示带题号的答案 |
| `Ctrl+Shift+2` | **收集剪贴板** | 当前剪贴板内容追加进缓存（可多次按，以 `-----` 分段） |
| `Ctrl+Shift+N` | **解题** | 把缓存内容整批发给大模型；>100 字答案会自动写入剪贴板供粘贴 |
| `Ctrl+Shift+0` | **退出** | 关闭悬浮助手 |

> 采用数字键 `1/2/3/0`：浏览器原生 `Ctrl+Shift+字母` 几乎都被占用（P=打印 / M=菜单 / B=Edge 收藏栏 / Y=史无前例的扩展 / N=无痕窗口 / K=浏览器自带等），而 `Ctrl+Shift+数字` 主流浏览器均未默认绑定，最大化避开冲突。
> 如需改键，打开 `overlay.py` 修改 `<ctrl>+<shift>+1/2/3/0` 四处与 `handle_hotkey` 内 `if key == ...` 即可，再 PyInstaller 重新打包。

---

## 📁 文件结构

```
SUPER_EXAMTEST/
├── overlay.py       # 源码（改键位/prompt 后用 PyInstaller 重打包）
├── config.json      # API 配置 / 模型 / prompt / 阈值
├── run.cmd          # 一键启动入口
├── stop.cmd         # 一键停止
├── LICENSE          # MIT 协议
└── README.md        # 本文档
```

> **可执行文件 `overlay.exe` 不在仓库中**，请在 [Releases](../../releases) 页下载。
> 源码构建者运行 `pyinstaller --onefile --windowed --name overlay overlay.py` 自行打包。

最小运行集合只需三个文件：**`overlay.exe` + `config.json` + `run.cmd`**

---

## ⚙️ 配置说明（`config.json`）

```json
{
  "ai": {
    "baseURL": "https://opencode.ai/zen/go/v1",
    "apiKey":  "sk-...",
    "model":   "qwen3.7-plus",
    "endpoint":       "/chat/completions",
    "timeoutSec":     120,
    "imageMaxWidth":  1400,
    "imageQuality":   0.80
  },
  "prompt": {
    "system": "你是考试答题助手。识别图中或文本中的所有题目，按题号顺序作答...",
    "longFillThreshold": 100
  }
}
```

| 字段 | 作用 |
|---|---|
| `ai.apiKey` | 大模型 API Key，更换服务商时改这里 |
| `ai.model` | 模型 ID。本仓库默认 `qwen3.7-plus`（智谱）；可换 `kimi-k2.6`、`glm-5.2`、`deepseek-v4-pro` 等任何 OpenAI 兼容端点支持的模型 |
| `ai.imageMaxWidth` | 截图上传前等比缩放的最大宽度（像素），2500×1600 屏幕一般 1400 足够，兼顾清晰度与上传耗时 |
| `ai.imageQuality` | JPEG 压缩质量 `0~1`，0.80 在文字题面上几乎无失真 |
| `prompt.system` | system prompt，约束模型按 `<answer>题号. 答案 \|\| 题号. 答案</answer>` 输出 |
| `prompt.longFillThreshold` | 答案超过该字符数则自动复制到剪贴板，方便填空长答案粘贴 |

> **修改后无需重新打包 exe** — 程序运行启动时一次性读取 `config.json`。改完关掉再双击 `run.cmd` 即可生效。

---

## 🧠 工作原理

```
┌──────────────────────────────────────────────────────────────┐
│  用户按 Ctrl+Shift+1                                          │
│         │                                                     │
│         ▼                                                     │
│  pynput 全局键盘钩子捕获组合键（系统级，浏览器拦截不到）         │
│         │                                                     │
│         ▼                                                     │
│  ImageGrab.grab(all_screens=True)  → PIL Image                │
│         │                                                     │
│         ▼                                                     │
│  等比缩放到 imageMaxWidth，JPEG 编码 → base64                  │
│         │                                                     │
│         ▼                                                     │
│  POST {baseURL}/chat/completions                              │
│  payload = {                                                  │
│    "model": "qwen3.7-plus",                                   │
│    "messages": [                                              │
│      { "role": "system", "content": <严格格式 prompt> },       │
│      { "role": "user", "content": [                           │
│          { "type":"text", "text": "请识别所有题目..." },        │
│          { "type":"image_url", "image_url": { "url":          │
│             "data:image/jpeg;base64,..." } }                 │
│      ]}                                                       │
│    ]                                                          │
│  }                                                            │
│         │                                                     │
│         ▼                                                     │
│  模型返回 <answer>1. B || 2. ABD || 3. 80 || 4. 错误</answer> │
│         │                                                     │
│         ▼                                                     │
│  正则 (?is)<answer>\s*(.*?)\s*</answer> 提取标签内字符串        │
│         │                                                     │
│         ▼                                                     │
│  把 "||" 替换为 6 空格 → "1. B      2. ABD      3. 80 ..."     │
│         │                                                     │
│         ▼                                                     │
│  Canvas.create_text(...) 居中绘制 + 黑色 1px 描边              │
│  每帧 SetWindowPos(HWND_TOPMOST) 维持置顶                      │
│  WS_EX_TRANSPARENT 让鼠标事件穿透到底层窗口                     │
└──────────────────────────────────────────────────────────────┘
```

### 为什么悬浮条能压过浏览器独占全屏？

浏览器进入 `requestFullscreen()` 后会创建一个独占fullscreen窗口，
常规 `TopMost=True` 的窗口会被它压住。本项目用**后台线程**每 800 ms 调一次 Win32 `SetWindowPos(HWND_TOPMOST)` 主动刷置顶，
加上 `WS_EX_NOACTIVATE` 让悬浮条永远不抢焦点，
因此即便考试页全屏独占，悬浮条仍能稳定显示在最顶层。

### 为什么浏览器按键拦截不到这些热键？

`pynput.keyboard.GlobalHotKeys` 在 Windows 上用 `SetWindowsHookEx(WH_KEYBOARD_LL)` 安装**低级键盘钩子**，
优先级高于浏览器进程内的 JavaScript `keydown` 监听。
即使考试页用 `e.preventDefault()` 也拦不住——按键在到达考试页之前就被我们的钩子先吃掉了。

---

## 🧪 真实测试结果（截屏 → 多模态识别）

测试输入：浏览器全屏打开的"计算机基础综合测验" 5 道题（单选 / 多选 / 填空 / 判断 / 简答混合）。

模型返回的原始内容：

```
<answer>1. B || 2. ABD || 3. 80 || 4. 错误 || 5. 运算器、控制器、存储器、输入设备、输出设备</answer>
```

提取后顶部横条显示：

```
1. B       2. ABD       3. 80       4. 错误       5. 运算器、控制器、存储器、输入设备、输出设备
```

5 题全对，10 秒返回。耗时主要来自模型的"思考模式"。

---

## 🔌 已验证可用的大模型

通过 `opencode.ai/zen/go/v1` 网关，以下模型均已实测可用：

| 模型 ID | 类型 | 备注 |
|---|---|---|
| `qwen3.7-plus` | 多模态 | **默认推荐**，听 `<answer>` 约束最稳 |
| `qwen3.7-max` | 多模态 | 性能更强，推理略慢 |
| `kimi-k2.6` | 偏对话 | 偶有提示不严守 `<answer>` 的情况，建议在 prompt 末尾再强调 |
| `glm-5.2` | 通用 | 中文表现好 |
| `deepseek-v4-pro` | 通用 | 答案精炼 |
| `minimax-m3` | 通用 | 综合模型 |

完整模型清单可以查询：

```powershell
curl -H "Authorization: Bearer <你的KEY>" https://opencode.ai/zen/go/v1/models
```

---

## 🛠️ 技术栈

| 层 | 选型 | 理由 |
|---|---|---|
| GUI | **tkinter** + Canvas | Python 自带，PyInstaller 打包后体积小 |
| 置顶维持 | **ctypes.windll.user32** + `SetWindowPos` | 解决 tk `-topmost` 压不过独占全屏的痛点 |
| 点击穿透 | Win32 `WS_EX_LAYERED \| WS_EX_TRANSPARENT \| WS_EX_NOACTIVATE` | 悬浮条不抢焦点，鼠标直达底层窗口 |
| 全局热键 | **pynput** `GlobalHotKeys` | 低级键盘钩子，绕过浏览器 JS 拦截 |
| 截屏 | **Pillow.ImageGrab** | `all_screens=True` 支持多显示器 |
| HTTP | **requests** | OpenAI 兼容 /chat/completions 端点 |
| 多模态 | `image_url` 携带 `data:image/jpeg;base64,...` | 无需额外上传服务，单请求带图 |
| 答案约束 | `<answer>...</answer>` 索引标签 + 正则提取 | 模型啰嗦也只取结构化答案 |
| 打包 | **PyInstaller --onefile --windowed** | 30 MB 单 EXE，零运行时依赖 |

---

## 🎯 适用场景

- ✅ 在线计算机考试页面截图答题
- ✅ PDF / Word / 图片格式试卷识别
- ✅ 非连续文本（多次复制）拼合后整理解答
- ✅ 长 / 复杂答案自动入剪贴板方便粘贴填空
- ✅ 任意需要"看一眼就给答案"的辅助场景

---

## ⚠️ 使用须知 / 免责声明

本项目仅供**技术学习与研究**用途，包括但不限于：

- 多模态大模型在 Windows GUI 自动化场景的工程实践
- Win32 全局热键、置顶窗口、点击穿透技术的演示
- PyInstaller 自包含应用打包流程

请勿用于任何违反法律法规、考试纪律或他人权益的场景。
使用者自行承担一切后果，作者不对此类使用造成的任何问题负责。

---

## 📜 License

MIT License — 详见 [LICENSE](./LICENSE)

## 🙏 致谢

- 多模态能力由 [OpenCode Zen Gateway](https://opencode.ai/zen/go/v1) 提供
- GUI / 截图 / 热键 / 打包等基础能力均来自 Python 开源生态
- 感谢所有为本项目提供灵感与反馈的朋友

---

<p align="center">
  <sub>Built with ❤️ for the AI era of computer-based exams.</sub>
</p>