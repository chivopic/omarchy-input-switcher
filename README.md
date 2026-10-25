# Input Switch · Omarchy 中英文切换插件

Omarchy 原生状态栏插件，复用 Fcitx5 与 Rime，准确区分中文、英文键盘和 Rime 内部英文模式。

## 已实现

- 顶部栏 `中` / `EN` 徽标：左键切换，右键面板，中键检查连接。
- 面板直接选择中文或英文，关闭弹层后再应用，保留现有快捷键。
- 一份共享后台状态，多屏复用；语言变化时在活动屏显示约 700ms 的提示。
- 直接中文会选择 Rime 并设置 `ascii_mode=false`；直接英文选择 `keyboard-us`。
- Rime 子模式不可读时显示 `RIME`，异常时显示 `!`，不会伪报切换成功。
- Fcitx5 断开后自动重试；桥接进程退出后自动重启；请求有超时与结果确认。
- 安装和卸载仅增删本插件配置，保留原来的 XKB 布局组件、快捷键和其他设置。

## 环境与依赖

- Omarchy 4.x 的 Quickshell 插件体系；本机验证版本 **4.0.6-1**。
- Python 3 与 `python-dbus`；不需要 pip 或 Node 作为运行依赖。
- Fcitx5；同一输入法组配置 `keyboard-us`、`rime`。
- 精确中文需要 `org.fcitx.Fcitx.Rime1` 的 `GetCurrentSchema`、`IsAsciiMode`、`SetAsciiMode`。

本机 Fcitx5 **5.1.23-1** / fcitx5-rime **5.1.16-1** 已检测到这些接口。插件按运行时能力检测，不假设其他发行版同版本一定提供。

如缺依赖，使用 Omarchy 包管理：

```bash
omarchy pkg add python-dbus fcitx5 fcitx5-rime
```

已有输入法可直接使用，无须重装或修改 Rime 方案。

## 安装

在此仓库内执行：

```bash
./scripts/input-switch --doctor
./scripts/install --dry-run
./scripts/install
```

安装器将插件复制到 `~/.config/omarchy/plugins/io.github.chivopic.input-switch/`，并在顶部栏 center 区域的键盘布局组件后插入徽标。也可使用 `./scripts/install --section right` 指定首次放置位置；重复安装保留你后来移动的位置和插件设置。

每次变更在 `~/.config/omarchy/input-switch-backups/` 保存配置和旧插件副本，写入失败会回滚插件目录。不编辑 `/usr/share/omarchy/`，不改 Hyprland 或 Fcitx 快捷键。已有非本安装器管理的同名插件目录会拒绝覆盖。

开发修改后重新执行 `./scripts/install` 同步到桌面。Omarchy 配置和插件会热加载；若 Shell 未运行，将在下次启动时加载。

卸载：

```bash
./scripts/uninstall
```

卸载只移除本插件条目，并把插件副本留在备份目录。后续对其他桌面设置的修改会保留。

## 使用与配置

| 操作 | 行为 |
| --- | --- |
| 左键徽标 | 在中文和英文之间切换 |
| 右键徽标 | 展开语言选择面板 |
| 中键徽标 | 重新检查连接和能力 |
| 原 Fcitx5 快捷键 | 行为保留，徽标自动同步结果 |

在 `shell.json` 中本插件的布局条目可以设置：

```json
{
  "id": "io.github.chivopic.input-switch",
  "showOsd": true,
  "osdDuration": 700
}
```

实际切换使用请求后查询确认；外部快捷键通过单个共享的 500ms 查询器同步，所以外部变化的显示最多通常延迟一个查询周期。查询复用同一 D-Bus 连接，不反复启动 `fcitx5-remote` 子进程。服务不可达时退避至最长 10 秒。

输入光标不存在、Rime 正在维护或无法读取子模式时，无法保证直接中文；插件会显示未确认或失败，而不是显示假状态。`EN` 代表英文输入模式，不代表 Caps Lock 状态。

命令行可以独立于插件界面使用：

```bash
./scripts/input-switch --status
./scripts/input-switch --set zh
./scripts/input-switch --set en
./scripts/input-switch --toggle
```

安装并启用插件后，可调用共享服务：

```bash
omarchy-shell input-switch status
omarchy-shell input-switch toggle
omarchy-shell input-switch set zh
omarchy-shell input-switch set en
omarchy-shell shell toggle io.github.chivopic.input-switch
```

IPC 的切换返回 `queued` 只表示接收请求，最终结果通过 `status` 中的 `pending`、`state`、`error` 确认。`busy` 表示已有请求在处理。首版不额外注册快捷键，避免与现有绑定重复触发。

## 验证与开发

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
node tests/model.test.cjs
omarchy plugin validate .
python3 tests/run_qml_smoke.py
```

QML 测试需要正在运行的 Hyprland/Wayland，会创建独立的不可见测试实例，实际切换请求使用模拟服务。

下面的桌面集成测试会短暂切换真实输入法，并在 `finally` 中恢复原状态。它不输入文字；在没有未上屏内容时执行：

```bash
python3 tests/desktop_roundtrip.py --allow-switch
# 安装后同时验证共享服务 IPC：
python3 tests/desktop_roundtrip.py --allow-switch --via-shell
```

桥接协议为 stdin 请求、stdout NDJSON 消息：

```json
{"id":1,"op":"set","language":"zh"}
```

后台发送 `type=state` 快照和带相同 id 的 `type=result`。快照中的 `asciiMode=null` 是未知，不等于中文。非法请求会返回错误，不执行切换。桥接只读取输入法状态，不读取输入文本、候选词或窗口标题。

当前版本聚焦手动切换。按应用规则和编辑器模式联动属于后续可选功能，尚未实现。初始调研和设计见 [PLAN.zh-CN.md](PLAN.zh-CN.md)，实际验证记录见 [VALIDATION.md](VALIDATION.md)。

## 参考

- [Omarchy Shell Plugins](https://omarchy.org/manual/shell-plugins/)
- [Fcitx5 D-Bus Interface](https://fcitx-im.org/wiki/DBus_Interface)
- [fcitx5-rime](https://github.com/fcitx/fcitx5-rime)
- [hypr-input-switcher](https://github.com/icyleaf/hypr-input-switcher)
- [im-select.nvim](https://github.com/keaising/im-select.nvim)

MIT License.
