# 首版验证记录

日期：2026-10-25。版本：0.1.0。

## 环境

- Omarchy 4.0.6-1
- Quickshell 0.3.2.r7.g2b4501a-1
- Fcitx5 5.1.23-1 / fcitx5-rime 5.1.16-1
- Rime 方案：rime_ice
- 输入法组：keyboard-us、rime
- 一个活动显示器；Python dbus-python 已安装

## 已通过

| 检查 | 结果 |
| --- | --- |
| Python 单元测试 | 19 项通过，覆盖 Rime 内部英文、精确中文、显式英文键盘、重复选择、缺失引擎/接口、未确认状态、非法请求、连接恢复、安装更新卸载与失败回滚 |
| JavaScript 状态显示 | 通过，未知子模式显示 RIME，等待和异常不会显示假中文 |
| Omarchy 清单 | `omarchy plugin validate .` 通过 |
| Shell / Python 语法 | 通过 |
| 实际 Wayland QML 加载 | 服务、徽标、语言面板、OSD 均加载成功，无场景错误；模拟服务验证延后选择回调 |
| 真实 D-Bus 切换 | 指定英文、指定中文、Rime 内部英文后返回中文均验证成功 |
| 外部模式同步 | 独立桥接进程观察到外部 SetAsciiMode 引起的状态变化 |
| 已安装服务 IPC | `omarchy-shell input-switch set en/zh` 均先返回 queued，再确认实际结果 |
| 测试状态恢复 | 往返测试后，原引擎、激活状态、Rime 子模式均与测试前一致 |
| 桌面安装 | 已启用；实际栏几何报告徽标可见，28 × 26px，位于 center |
| 多实例防重复 | 安装后的实际桥接进程数量为 1 |
| 现有配置 | 当前 shell.json 删除本插件条目后，与首次安装前 JSON 完全相同 |
| 运行日志 | 最终日志中未发现本插件组件的 TypeError、ReferenceError 或加载失败 |

安装位置：`~/.config/omarchy/plugins/io.github.chivopic.input-switch/`。

首次安装备份：`~/.config/omarchy/input-switch-backups/20261025T204216.171606/`。

## 验证边界

- 测试确认控制接口和实际模式状态，没有向用户应用注入文字。
- 尚未逐一完成 GTK、Qt、Chromium、Electron、终端输入框的手工输入和未上屏组合测试。
- 当前只有一个活动显示器；多屏共享服务和活动屏 OSD 已实现，仍需双屏实机验收。
- QML 加载测试不等同于真实鼠标点击、键盘导航和所有主题下的视觉验收。
- 外部快捷键通过 500ms 共享查询同步；本次不把 D-Bus 调用耗时当作完整界面延迟。
- 输入法服务重启恢复使用模拟单元测试；未为了测试而终止用户正在运行的 Fcitx5。
- 应用规则、按应用记忆和编辑器联动未进入本次首版范围。
