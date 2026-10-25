# 使用与配置

[返回 README](../README.zh-CN.md) · [English](USAGE.md)

## 依赖与安装

Input Switch 是 Quickshell 顶部栏组件和共享服务插件。需要 Omarchy Quickshell 插件体系、带 `python-dbus` 的 Python 3，以及正在运行的 Fcitx5。同一个输入法组中需配置 `rime` 与 `keyboard-us`。

精确切换中文需要运行时 `org.fcitx.Fcitx.Rime1` 接口提供 `GetCurrentSchema`、`IsAsciiMode` 和 `SetAsciiMode`。插件会检测能力；即使软件包版本相同，不同发行版也可能提供不同接口。

已验证环境：Omarchy **4.0.6-1**、Quickshell **0.3.2.r7.g2b4501a-1**、Fcitx5 **5.1.23-1**、fcitx5-rime **5.1.16-1**。

仅安装缺少的软件包：

```bash
omarchy pkg add python-dbus fcitx5 fcitx5-rime
```

### Omarchy 插件管理器

以下安装方式**选择一种**即可。同一个插件不要同时使用插件管理器和本地源码安装器安装。

```bash
omarchy plugin add https://github.com/chivopic/omarchy-input-switcher --enable
```

徽标默认放在顶部栏中间区域。移动到右侧：

```bash
omarchy bar move io.github.chivopic.input-switch --section right
```

通过插件管理器安装的版本，可用以下命令更新或移除：

```bash
omarchy plugin update io.github.chivopic.input-switch
omarchy plugin remove io.github.chivopic.input-switch
```

### 本地源码安装

```bash
git clone https://github.com/chivopic/omarchy-input-switcher.git
cd omarchy-input-switcher
./scripts/input-switch --doctor
./scripts/install --dry-run
./scripts/install
```

本地安装器会把插件复制到 `~/.config/omarchy/plugins/io.github.chivopic.input-switch/`，并在已有键盘布局组件后插入徽标。原有设置会保留，每次变更前都会备份。修改源码后重新运行 `./scripts/install`；使用 `./scripts/uninstall` 卸载。

备份位于 `~/.config/omarchy/input-switch-backups/`。安装器不会覆盖不由它管理的同名目录，不会编辑 `/usr/share/omarchy/`、Hyprland 快捷键或 Rime 方案。

## 操作与状态

| 操作 | 结果 |
| --- | --- |
| 左键点击徽标 | 切换中文 / 英文 |
| 右键点击徽标 | 打开语言面板 |
| 中键点击徽标 | 重新检查连接 |
| 在面板选择中文 / English | 关闭面板，再应用语言 |
| 使用原有 Fcitx5 快捷键 | 原有行为保留，徽标同步结果 |

中文会选择 Rime 并清除 `ascii_mode`；英文会明确选择 `keyboard-us`。桥接会通过 Fcitx5 和 Rime 核实结果。仅选择 Rime 并不能证明当前为中文模式。

| 徽标 | 含义 |
| :---: | --- |
| `中` | 已确认 Rime 中文模式 |
| `EN` | 已确认英文输入，包括 Rime 内部英文模式 |
| `RIME` | 已选择 Rime，但内部模式未确认 |
| `…` | 请求处理中 |
| `!` | 输入法服务不可用 |

插件默认不注册额外快捷键。`EN` 表示输入模式，不代表 Caps Lock。

## 选项

在 `~/.config/omarchy/shell.json` 中本插件的布局条目设置：

```json
{
  "id": "io.github.chivopic.input-switch",
  "showOsd": true,
  "osdDuration": 700
}
```

`osdDuration` 单位是毫秒，限制在 250–3000ms。把 `showOsd` 设为 `false` 可关闭 OSD，只保留顶部栏徽标。OSD 不会抢键盘焦点或阻挡点击。

## 命令行与 Shell IPC

在本地源码目录中：

```bash
./scripts/input-switch --status
./scripts/input-switch --set zh
./scripts/input-switch --set en
./scripts/input-switch --toggle
```

插件启用后：

```bash
omarchy-shell input-switch status
omarchy-shell input-switch set zh
omarchy-shell input-switch set en
omarchy-shell input-switch toggle
omarchy-shell shell toggle io.github.chivopic.input-switch
```

IPC 返回 `queued` 表示请求被接收，`busy` 表示已有请求正在处理。最终结果请检查 `status` 中的 `state`、`pending`、`error` 字段；请求被接收不等于切换已确认。

## 故障排查

| 现象 | 检查方式 |
| --- | --- |
| 显示 `!` | 运行 `./scripts/input-switch --doctor` 或查看 `omarchy-shell input-switch status`。确认 Fcitx5 正在同一个桌面会话运行。 |
| 显示 `RIME`，无法确认中文 | 查看状态中的 `preciseRime`。Rime 可能没有提供精确模式接口；插件不会猜测。 |
| 切换未确认 | 聚焦输入框后重试。缺少输入上下文或 Rime 维护状态可能使子模式暂时不可读。 |
| 外部快捷键切换后徽标稍后更新 | 共享查询每 500ms 运行一次；它与切换请求确认分开。 |

## 范围与验证

当前支持手动切换，尚未实现按应用规则、应用独立记忆或编辑器模式联动。多屏共享机制已实现，但双屏硬件及 GTK、Qt、Chromium、Electron 中的各类输入框流程尚未逐一验证。实际检查范围见[验证记录](../VALIDATION.md)。
