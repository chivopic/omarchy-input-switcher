<p align="center">
  <img src="docs/assets/hero.svg" alt="Input Switch — 一键切换中英文输入" width="100%">
</p>

<p align="center">
  <a href="https://omarchy.org"><img src="https://img.shields.io/badge/Omarchy-4.x-a8d5bf?style=flat-square&amp;labelColor=294437" alt="Omarchy 4.x"></a>
  <img src="https://img.shields.io/badge/UI-Native_QML-a8d5bf?style=flat-square&amp;labelColor=294437" alt="原生 QML 界面">
  <img src="https://img.shields.io/badge/Backend-Fcitx5_%2B_Rime-a8d5bf?style=flat-square&amp;labelColor=294437" alt="Fcitx5 与 Rime">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-a8d5bf?style=flat-square&amp;labelColor=294437" alt="MIT 许可证"></a>
</p>

<p align="center"><a href="README.md">English</a> · <b>简体中文</b></p>

**为 Omarchy 打造的原生中英文输入法切换插件。** 在顶部栏点击一次即可切换，也能从面板直接选择中文或英文。短暂的屏幕提示确认切换结果，随后继续输入。

插件会同时检查 Fcitx5 引擎和 Rime 内部的英文模式，避免把“正在使用 Rime”误报成“正在输入中文”。

## 界面预览

<table>
  <tr><th width="50%">中文 · Rime</th><th width="50%">英文 · US 键盘</th></tr>
  <tr>
    <td align="center" valign="top"><img src="docs/assets/panel-chinese.png" alt="真实 QML 组件预览：选中中文，显示 rime_ice 方案" width="360"></td>
    <td align="center" valign="top"><img src="docs/assets/panel-english.png" alt="真实 QML 组件预览：选中英文，显示 English (US) 引擎" width="360"></td>
  </tr>
</table>

*预览由实际 QML 组件渲染，使用示例状态与示例主题。安装后的颜色、字体、间距会跟随你的 Omarchy 主题。*

## 核心体验

- **一键切换**：顶部栏只占一个小徽标，左键切换，右键展开语言面板。
- **按实际状态反馈**：直接中文会选择 Rime 并关闭 `ascii_mode`；直接英文明确选择 `keyboard-us`。结果确认后再更新标签。
- **保留输入习惯**：现有 Fcitx5 快捷键不变，外部切换通过共享查询同步到徽标。
- **轻量提示**：切换结果在活动屏幕短暂显示，不抢键盘焦点，也不挡鼠标点击。
- **后台共享**：各屏幕共用一个服务和持久 D-Bus 连接；连接失败后自动退避重试。
- **明确表达未知**：不能确认 Rime 子模式时显示 `RIME`，服务不可用时显示 `!`，不把未确认状态伪装成中文。

| 徽标 | 含义 |
| :---: | --- |
| `中` | 已确认 Rime 处于中文模式 |
| `EN` | 已确认英文输入，包含 Rime 内部英文模式 |
| `RIME` | 选择了 Rime，但其内部模式尚未确认 |
| `…` | 请求处理中 |
| `!` | 输入法服务不可用 |

## 安装

### 环境要求

- 使用 **Quickshell 插件体系**的 Omarchy；Python 3 与 `python-dbus`。
- Fcitx5 正在运行，**同一个输入法组中配置了 `keyboard-us` 和 `rime`**。
- 精确中文切换需要运行时 `org.fcitx.Fcitx.Rime1` 接口提供 `GetCurrentSchema`、`IsAsciiMode`、`SetAsciiMode`。

已验证环境：Omarchy **4.0.6-1**、Quickshell **0.3.2.r7.g2b4501a-1**、Fcitx5 **5.1.23-1**、fcitx5-rime **5.1.16-1**。插件会检测接口能力，不假定其他发行版的同版本一定提供相同接口。

仅在缺少依赖时安装：

```bash
omarchy pkg add python-dbus fcitx5 fcitx5-rime
```

下面两种安装方式**选择一种**即可。

### 使用 Omarchy 插件管理器

```bash
omarchy plugin add https://github.com/chivopic/omarchy-input-switcher --enable
```

默认放在顶部栏中间区域，也可以移动到右侧：

```bash
omarchy bar move io.github.chivopic.input-switch --section right
```

通过插件管理器安装的版本，使用对应命令更新或移除：

```bash
omarchy plugin update io.github.chivopic.input-switch
omarchy plugin remove io.github.chivopic.input-switch
```

### 本地源码安装 / 开发

```bash
git clone https://github.com/chivopic/omarchy-input-switcher.git
cd omarchy-input-switcher

./scripts/input-switch --doctor
./scripts/install --dry-run
./scripts/install
```

本地安装器会把插件复制到 `~/.config/omarchy/plugins/io.github.chivopic.input-switch/`，并在已有键盘布局组件后插入徽标。原有设置会保留，每次变更前都会备份。源码修改后重新运行 `./scripts/install` 即可同步，使用 `./scripts/uninstall` 卸载这一安装方式。

备份位于 `~/.config/omarchy/input-switch-backups/`。安装器拒绝覆盖不由它管理的同名插件目录，不编辑 `/usr/share/omarchy/`，不修改 Hyprland 快捷键或 Rime 方案。

## 操作与设置

| 操作 | 行为 |
| --- | --- |
| 左键点击徽标 | 中英文切换 |
| 右键点击徽标 | 打开语言选择面板 |
| 中键点击徽标 | 重新检查连接 |
| 在面板选择中文或英文 | 关闭面板，再应用目标语言 |
| 使用原来的 Fcitx5 快捷键 | 行为保留，徽标同步结果 |

插件默认不注册额外快捷键。`EN` 表示英文输入模式，不表示 Caps Lock 状态。

可以在 `~/.config/omarchy/shell.json` 中本插件的布局条目设置：

```json
{
  "id": "io.github.chivopic.input-switch",
  "showOsd": true,
  "osdDuration": 700
}
```

`osdDuration` 单位是毫秒，范围限制在 250–3000ms。把 `showOsd` 设为 `false`，只保留状态栏显示。

## 命令行与桌面联动

在本地源码目录中，可独立使用：

```bash
./scripts/input-switch --status
./scripts/input-switch --set zh
./scripts/input-switch --set en
./scripts/input-switch --toggle
```

插件启用后，可以调用共享服务：

```bash
omarchy-shell input-switch status
omarchy-shell input-switch set zh
omarchy-shell input-switch set en
omarchy-shell input-switch toggle
omarchy-shell shell toggle io.github.chivopic.input-switch
```

IPC 返回 `queued` 表示请求被接收，`busy` 表示已有请求正在处理。最终结果需要查看 `status` 中的 `state`、`pending`、`error`，接收请求不等于切换已经成功。

## 实现方式

<img src="docs/assets/architecture.svg" alt="徽标、面板和屏幕提示共享一个 Quickshell 服务；Python 桥接通过持久 D-Bus 连接控制 Fcitx5 和 Rime，并返回确认后的实际状态。" width="100%">

Python 桥接使用 `asyncio` 和 `dbus-python`，复用同一条 D-Bus 连接，避免每次刷新都启动 `fcitx5-remote` 子进程。单个共享的 500ms 查询器同步外部变化，服务不可达时退避至最长 10 秒。

桥接只读取引擎与模式元数据，不读取输入文本、候选词或窗口标题。插件运行不需要 pip、Node 或自定义 C++ 扩展。

## 排查与当前边界

| 现象 | 检查方式 |
| --- | --- |
| 显示 `!` | 在源码目录运行 `./scripts/input-switch --doctor`，或查看 `omarchy-shell input-switch status`；确认 Fcitx5 在同一个桌面会话中运行。 |
| 显示 `RIME`，中文按钮不可用 | Rime 可能未提供精确模式接口。检查状态中的 `preciseRime`，插件不会猜测模式。 |
| 切换结果未确认 | 聚焦输入框后重试。缺少输入上下文或 Rime 维护状态可能导致模式暂时不可读。 |
| 原快捷键切换后徽标稍晚更新 | 外部变化由 500ms 查询器同步，与主动请求的结果确认分开。 |

首版聚焦**手动切换**。按应用规则、应用独立记忆和编辑器模式联动尚未实现。多屏共享机制已经实现，但仍需双屏硬件验收；GTK、Qt、Chromium、Electron 的全部输入框流程也尚未逐项验证。

## 开发与验证

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
node tests/model.test.cjs
omarchy plugin validate .
```

目前包含 **19 项 Python 测试**、状态显示检查、独立 Wayland QML 加载测试，以及显式开启的真实桌面往返测试。桌面测试、桥接协议和原生预览生成方式见[开发指南](docs/DEVELOPMENT.md)，实际检查范围见[验证记录](VALIDATION.md)。

欢迎提交 Issue 或 Pull Request。报告问题时，请附上 Omarchy、Fcitx5、Rime 版本和相关状态输出。

## 致谢

基于 [Omarchy 插件体系](https://omarchy.org/manual/shell-plugins/)、[Fcitx5](https://fcitx-im.org/wiki/DBus_Interface) 与 [Rime](https://github.com/fcitx/fcitx5-rime) 构建。初始交互方案也参考了 [hypr-input-switcher](https://github.com/icyleaf/hypr-input-switcher) 和 [im-select.nvim](https://github.com/keaising/im-select.nvim)。

采用 [MIT 许可证](LICENSE)。
