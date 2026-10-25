import QtQuick
import Quickshell
import Quickshell.Io
import "InputModel.js" as InputModel

Item {
  id: root
  property var shell: null
  property var manifest: null
  property var snapshot: ({ available: false, effectiveLanguage: "unknown", error: "正在连接…" })
  property bool pending: false
  property string lastError: ""
  property bool showOsd: true
  property int osdDuration: 700
  property int serial: 0
  property int currentRequest: -1
  property int restartDelay: 1000
  property bool receivedSnapshot: false
  property bool shuttingDown: false
  property bool startAttempted: false
  property string requestedOperation: ""
  readonly property string bridgePath: decodeURIComponent(Qt.resolvedUrl("bridge/input_bridge.py").toString().replace(/^file:\/\//, ""))
  readonly property string label: InputModel.label(snapshot, pending)
  readonly property string description: InputModel.description(snapshot)
  readonly property string tooltip: InputModel.tooltip(snapshot, pending, lastError)

  function configure(enabled, duration) {
    showOsd = enabled !== false
    osdDuration = Math.max(250, Math.min(3000, Number(duration) || 700))
  }

  function send(operation, language) {
    if (pending) return "busy"
    if (!bridge.running) {
      lastError = "输入法服务正在重连"
      return "unavailable"
    }
    lastError = ""
    currentRequest = ++serial
    pending = true
    requestedOperation = operation
    requestTimeout.restart()
    bridge.write(JSON.stringify({ id: currentRequest, op: operation, language: language || "" }) + "\n")
    return "queued"
  }

  function setLanguage(language) {
    if (language !== "zh" && language !== "en") return "invalid-language"
    return send("set", language)
  }

  function toggleLanguage() { return send("toggle", "") }
  function refresh() { return send("status", "") }

  function feedback() {
    if (showOsd && (snapshot.effectiveLanguage === "zh" || snapshot.effectiveLanguage === "en"))
      osd.show(InputModel.label(snapshot, false), InputModel.description(snapshot), snapshot.schema || (snapshot.engine === "keyboard-us" ? "English (US)" : snapshot.engine), osdDuration)
  }

  function receive(line) {
    var message
    try { message = JSON.parse(line) } catch (e) { return }
    if (message.type === "state") {
      var previousKnown = snapshot.effectiveLanguage === "zh" || snapshot.effectiveLanguage === "en"
      var changed = receivedSnapshot && previousKnown && snapshot.effectiveLanguage !== message.effectiveLanguage
      snapshot = message
      receivedSnapshot = true
      restartDelay = 1000
      if (changed && !pending) feedback()
    } else if (message.type === "result" && message.id === currentRequest) {
      requestTimeout.stop()
      pending = false
      if (!message.ok) lastError = message.error ? message.error.message : "切换失败"
      else if (requestedOperation !== "status") feedback()
    }
  }

  function statusJson() {
    return JSON.stringify({ state: snapshot, pending: pending, error: lastError })
  }

  function disconnected() {
    if (shuttingDown || restart.running) return
    pending = false
    requestTimeout.stop()
    snapshot = { available: false, effectiveLanguage: "unknown", error: "输入法服务已断开" }
    restart.interval = restartDelay
    restartDelay = Math.min(30000, restartDelay * 2)
    restart.start()
  }

  Component.onCompleted: { startAttempted = true; bridge.running = true }
  Component.onDestruction: { shuttingDown = true; restart.stop() }

  Process {
    id: bridge
    command: ["python3", root.bridgePath]
    stdinEnabled: true
    stdout: SplitParser { onRead: data => root.receive(data) }
    stderr: SplitParser { onRead: data => console.warn("Input Switch bridge:", data) }
    onExited: root.disconnected()
    onRunningChanged: if (!running && root.startAttempted) root.disconnected()
  }

  Timer {
    id: restart
    onTriggered: bridge.running = true
  }

  Timer {
    id: requestTimeout
    interval: 8000
    onTriggered: {
      root.lastError = "输入法响应超时，正在重连"
      root.pending = false
      bridge.running = false
    }
  }

  Osd { id: osd }

  IpcHandler {
    target: "input-switch"
    function status(): string { return root.statusJson() }
    function toggle(): string { return root.send("toggle", "") }
    function set(language: string): string {
      return language === "zh" || language === "en" ? root.send("set", language) : "invalid-language"
    }
    function refresh(): string { return root.send("status", "") }
    function ping(): string { return "ok" }
  }
}
