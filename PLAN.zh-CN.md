# Omarchy 中英文输入法切换插件方案

调研日期：2026-10-25。本文保留初始设计；当前实现以 README.md 和 VALIDATION.md 为准。

实施更新：本机已发现并验证 `/rime` 上的 `org.fcitx.Fcitx.Rime1` 精确模式接口，因此不需要额外 C++ addon。首版使用本机已有的 Python `dbus-python` 库与 asyncio，避免另装 dbus-next。

## 1. 推荐方向

暂名 **Input Switch**，插件 ID 可用 `io.github.chivopic.input-switch`（发布前确认命名）。采用 Omarchy 原生 Quickshell/QML，提供顶部栏状态、单击切换、右键面板和短暂 OSD。复用 Fcitx5 与当前 Rime 配置。

第一版以手动快速切换和正确反馈为中心。按应用记忆放到第二版；按编辑器插入/普通模式切换由编辑器插件提供事件，桌面只显示结果。

## 2. 本机已核对的信息

| 项目 | 本机情况 | 对方案的影响 |
| --- | --- | --- |
| Omarchy | 4.0.6-1 | 根据本机插件协议开发，不能照抄最新主线命令 |
| Quickshell | 0.3.2.r7.g2b4501a-1 | 首选原生 QML 集成 |
| 输入法 | Fcitx5 5.1.23-1；中文扩展与 Rime 已安装 | 无须另建输入法引擎 |
| 当前输入法组 | `keyboard-us`、`rime`，默认 IM 为 `rime` | 按这两个实际配置的引擎做默认切换对 |
| 现有栏组件 | `omarchy.keyboard-layout`，位于 center | 本机源码读取 XKB 布局，不是 Rime 中英文状态 |
| 现有按键 | Ctrl+Space 触发；左右 Shift 枚举；Super+Space 切组 | 保留现有习惯，先观察状态，再决定是否统一快捷键 |
| Rime 自定义 | Shift/Control 内部切换设为 noop；启用了 Caps Lock 相关选项 | 仍不能仅凭引擎名称断言中英文模式 |
| 输入状态共享 | Fcitx5 `ShareInputState=All` | 第一版沿用；按应用策略作为可选独立模式 |

工具会话无法连接桌面会话 D-Bus：`fcitx5-remote` 查询报连接失败，`omarchy plugin list` 也未找到运行中的 Shell。因此上述是安装与配置事实；运行中的输入状态、实际快捷键冲突、延迟、焦点行为仍需桌面联调。

## 3. 借鉴对象

1. **Omarchy 原生插件体系**：`bar-widget`、`service`、`panel` 的组合、主题跟随、多显示器布局、用户插件目录与热加载。参考 <https://omarchy.org/manual/shell-plugins/>，实现时以本机 `/usr/share/omarchy/shell/README.md` 和 `services/PluginRegistry.qml` 为准。
2. **Fcitx5 Controller**：明确区分查询、启用/停用和指定引擎；复用其控制接口。参考 <https://fcitx-im.org/wiki/DBus_Interface>。
3. **hypr-input-switcher**：通过 Hyprland 活动窗口事件匹配应用规则；借鉴显式默认规则与 `keep` 行为。参考 <https://github.com/icyleaf/hypr-input-switcher>。它是参考实现，不代表已在本机验证，也不直接套用其旧版 Hyprland 配置语法。
4. **im-select.nvim**：插入模式恢复、退出插入模式切换等编辑器联动；此类事件应该来自编辑器。参考 <https://github.com/keaising/im-select.nvim>。

最新 Omarchy 手册已有输入法/布局统一切换描述：<https://omarchy.org/manual/keyboard-mouse-trackpad/>。本机打包组件仍为 XKB 布局组件。需要做版本能力检测，避免将来升级后出现两套切换逻辑。

## 4. 技术栈选择

| 方案 | 适合 | 成本与限制 | 建议 |
| --- | --- | --- | --- |
| QML + `fcitx5-remote` | 最小原型、单击切换、引擎状态显示 | 命令调用简单；需要刷新机制；只能查询引擎与激活状态 | 第一阶段验证控制路径 |
| QML + Python asyncio / dbus-next | 状态聚合、超时恢复、后续规则、JSON 流 | 增加一个小型桥接进程和依赖；不会自动获得 Rime 内部状态 | 推荐首版应用架构 |
| QML + Qt/C++ / QtDBus | 原生常驻桥接、较严谨的类型与事件处理 | 需构建和发布二进制；接口能力仍受 Fcitx 限制 | 原生发布路线的替代选项 |
| QML + Rust / zbus 或 Go D-Bus 库 | 独立守护服务、未来多桌面复用 | 更完整的工具链和打包工作；首版收益有限 | 后续有跨桌面需求再选 |
| Fcitx5 C++ addon + QML | 需要读取实际输入上下文、Rime 子模式或公开自定义状态接口 | 更深入的输入法集成；版本与部署维护成本最高 | 精确 Rime 模式能力无法外部获得时评估 |
| Waybar 自定义模块 + 脚本 | 使用 Waybar 的旧环境 | 本机运行 Quickshell；需要另一套 UI 适配 | 作为兼容分支 |
| Eww/AGS/GTK layer-shell | 独立桌面浮层 | 另建主题、进程和栏集成 | 本机无必要 |

QtDBus、dbus-next、zbus 等是访问同一接口的不同客户端。换语言不等于新增了 Rime 运行时状态接口。

## 5. 推荐架构

```text
BarWidget.qml ─┐
Panel.qml ─────┼── Service.qml ── Bridge（Python）── Fcitx5 Controller
Osd.qml ───────┘       │                 │
                      IPC               ├── 状态订阅 / 有限频率查询
                                        ├── 能力检测后的 Rime 状态适配
                                        └── Hyprland 窗口事件（第二版）
```

- 一个插件服务共享状态，多屏只挂 UI，避免每个屏幕产生一个轮询器。
- 服务持有一个桥接子进程，通过 stdin/stdout 的 NDJSON 请求与快照通信；首版可由插件生命周期管理，暂不另装 systemd 服务。
- 界面只发 `toggle`、`set-engine`、`set-language` 等请求；控制器串行执行，查询确认后才展示成功。
- 使用参数数组执行命令，避免把应用名和输入法 ID 拼进 shell 字符串。
- 服务重连后先拿完整快照；桥接重启、Fcitx5 重启与无焦点都必须有可恢复状态。
- Omarchy 第三方插件只能使用自己获准的服务和生命周期接口；不依赖其他内置插件的私有对象。

建议内部快照字段：

```json
{
  "backend": "fcitx5",
  "available": true,
  "engine": "rime",
  "active": true,
  "asciiMode": null,
  "effectiveLanguage": "unknown",
  "pending": false,
  "source": "controller"
}
```

`asciiMode` 为 null 表示没有可靠观测；它与 false 必须区别处理。界面此时展示 `RIME`，不能展示已经确认的 `中`。

## 6. 切换语义与 Rime 难点

需要区分三层：XKB 键盘布局、Fcitx5 引擎/激活状态、Rime 内部 `ascii_mode`。`US` 不等于当前输入英文，`rime` 不等于当前输入中文。

已有基础控制接口如下，供实现时调用；本次未执行切换：

```bash
fcitx5-remote -n                # 当前引擎名称
fcitx5-remote                   # 激活状态
fcitx5-remote -s keyboard-us    # 请求切至英文键盘引擎
fcitx5-remote -s rime           # 请求切至 Rime 引擎，不保证 ascii_mode=false
```

正式版定义两类操作：

- `set-engine(rime)`：只承诺引擎选择。
- `set-language(zh)`：必须确认 Rime 处于中文模式；没有能力就返回不支持或未确认，不能伪报成功。

第一轮技术验证必须优先解决 Rime 能力：

1. 在真实桌面检查 Controller introspection 和已启用的托盘/状态接口。
2. 验证状态变化是否有可靠通知。Fcitx Controller 源码的组变化信号不能当成所有引擎、子模式变化信号。参考 <https://github.com/fcitx/fcitx5/blob/master/src/modules/dbus/dbusmodule.cpp>。
3. 现有接口不够时，评估 Fcitx addon 的输入上下文和子模式能力，以及经公开接口控制 Rime 运行会话的可行性；不得假定插件进程另开 librime 就能访问 Fcitx 正在用的会话。参考 <https://github.com/fcitx/fcitx5-rime/blob/master/src/rimestate.cpp>。
4. 不为获取状态而直接接管 Kimpanel UI；接管可能影响候选窗。若考察现有状态信号，必须验证不会改变候选窗路径。
5. 如只能获得引擎级信息，先交付清楚标注的 `EN / RIME` 原型；完整“中英文”版本以子模式验证通过为发布门槛。

可用外部信号就事件驱动；缺失信号时允许一个共享的低频查询器，例如原型阶段 500–1000ms。切换请求之后立即补查，打开面板/焦点变化时补查，进程失败后指数退避。只查 Controller 无法补出 Rime 子模式，这个限制要明确保留。

## 7. 三种布局

### A. 极简状态徽标 + 右键面板（推荐）

顶部栏单独显示 `中` / `EN`，有可靠状态时才使用这两个标签；可选 `RIME`、`…`、`!` 等未确认/等待/异常状态。

- 左键：切换；右键：展开面板。
- 面板约 280–320px，显示当前引擎、可用语言、快捷键提示和设置入口。
- 切换成功在当前活动屏显示约 700ms 的 OSD；OSD 不取得键盘焦点。
- 本机顶部栏右侧已有较多组件，建议先沿用现有布局指示器所在的 center 区域；安装时由用户选择共存或替换其位置。XKB 多布局用户保留原组件。

### B. 双段按钮

顶部栏常驻 `[中 | EN]`，点击目标语言直接选择。易理解、可显式选择，代价是占用更多栏空间。重复点击当前语言应该是幂等操作。

### C. 快捷键优先 + OSD

不常驻状态徽标，通过快捷键切换并短暂显示结果。视觉最少，但无法随时确认状态。适合熟练键盘用户，可与 A 的徽标组合。

不建议首版放光标旁浮标。Wayland 下普通外部插件不能假设总能得到输入光标位置，优先用活动显示器上的固定位置 OSD。

## 8. 交互和默认配置

- 沿用现有 Ctrl+Space 和 Shift 行为，插件观察最终结果；不对同一个键在 Fcitx 和 Hyprland 各执行一次 toggle。
- 提供可选“直接中文”“直接英文”绑定，安装时先检查实际绑定。`Super+Shift+Space` 在本机默认配置是切换顶部栏，不能直接拿来当输入法切换键。
- 面板选择必须记住打开前的目标窗口；关闭面板恢复焦点后再应用到预期输入上下文，避免把切换作用到面板自身。
- 第一版维持当前全局共享语义；第二版提供“全局 / 按应用”互斥策略，避免和 Fcitx 自身的共享策略同时竞争。
- 按应用默认 `keep`；终端偏好英文、聊天偏好中文仅作为用户可选规则。临时手动选择优先于默认规则。
- 编辑器内普通/插入模式不靠窗口标题推测，由编辑器联动提供。
- 只记录引擎、语言、状态及错误；不记录输入文本。
- 配色、字体、圆角跟随 Omarchy，中文状态文字与英文状态文字本身可辨识，不只靠颜色。

## 9. 建议目录

```text
omarchy-input-switcher/
  manifest.json
  BarWidget.qml
  InputPanel.qml
  Osd.qml
  Service.qml
  InputModel.js
  bridge/input_bridge.py
  scripts/install
  scripts/uninstall
  tests/
  README.md
  PLAN.zh-CN.md
  previews/input-switch-layouts.html
```

开发在项目目录中完成。安装目标为 `~/.config/omarchy/plugins/<plugin-id>/`；配置合并到用户配置，不覆盖整个 shell.json，不编辑 `/usr/share/omarchy/`。安装脚本保存自己改动的条目，卸载只撤销这些条目。先验证插件与服务协议，再提供打包和发布。

## 10. 分期与验收

| 阶段 | 内容 | 完成门槛 |
| --- | --- | --- |
| P0 技术验证 | 真实桌面查询/指定引擎、Rime 子模式能力、焦点行为 | 明确能否保证“直接中文”，并形成可复现记录 |
| P1 手动原型 | 原生徽标、切换请求、右键面板、OSD、异常反馈 | 能确认引擎切换；无法观测的模式明确显示为未确认 |
| P2 首个正式版 | 完成 Rime 精确适配、快捷键同步、多屏共享服务 | 中文/英文显示与实际输入一致；失败不伪报成功 |
| P3 可选增强 | 应用规则、记忆、暂停自动切换、编辑器联动 | 手动意图不被后台规则立即覆盖，规则优先级明确 |

测试覆盖：键盘外部切换、鼠标切换、Rime 英文模式、Caps Lock、未上屏组合、无输入焦点、面板打开/关闭、多屏、Shell 热加载、Fcitx 重启、GTK/Qt/Chromium/Electron/终端、XWayland。输入法服务不可用时显示未连接并自动恢复。

性能目标待测：指定状态切换到确认反馈争取 150ms 内（不含配置的 OSD 停留时间）；事件可用时空闲不高频派生子进程。该数字是设计目标，不是本次实测。

交付前运行本机支持的插件验证命令；如改动 Hyprland 用户 Lua，必须执行 `hyprctl reload` 与 `hyprctl configerrors`。发布前检查最低 Omarchy 版本和主线输入法功能的重叠。
