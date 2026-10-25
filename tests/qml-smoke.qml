import QtQuick
import Quickshell
import Quickshell.Io

ShellRoot {
  id: root
  readonly property string project: Quickshell.env("INPUT_SWITCH_PROJECT")

  QtObject {
    id: fakeService
    property var snapshot: ({available:true, engine:"rime", effectiveLanguage:"zh", preciseRime:true, engines:["keyboard-us", "rime"], schema:"rime_ice", error:""})
    property bool pending: false
    property string lastError: ""
    property string label: "中"
    property string tooltip: "中文输入"
    property string lastRequest: ""
    function configure(enabled, duration) { }
    function send(op, language) { lastRequest = op + ":" + language; return "queued" }
  }
  QtObject {
    id: facade
    function serviceFor(id) { return fakeService }
  }
  QtObject {
    id: fakeBar
    property var shell: facade
    property bool vertical: false
    property int barSize: 28
    property string position: "top"
    property string fontFamily: "monospace"
    property color barForeground: "#cccccc"
    property color foreground: "#cccccc"
    property color urgent: "#ff8888"
    property bool foregroundAnimationEnabled: false
    property var activePopout: null
    function registerClickTarget(item) { }
    function unregisterClickTarget(item) { }
    function showTooltip(item, text) { }
    function hideTooltip(item) { }
    function requestPopout(item) { activePopout = item }
    function releasePopout(item) { activePopout = null }
  }
  Loader {
    id: widget
    source: root.project + "/BarWidget.qml"
    onLoaded: item.bar = fakeBar
  }
  Loader {
    id: service
    source: root.project + "/Service.qml"
    onLoaded: item.showOsd = false
  }
  Timer {
    interval: 400
    running: true
    onTriggered: {
      if (widget.status !== Loader.Ready || service.status !== Loader.Ready) {
        console.error("QML_SMOKE_FAILED: component loading")
        Qt.quit()
        return
      }
      widget.item.choose("en")
      check.start()
    }
  }
  Timer {
    id: check
    interval: 300
    onTriggered: {
      if (fakeService.lastRequest !== "set:en") {
        console.error("QML_SMOKE_FAILED: deferred language selection")
        Qt.quit()
        return
      }
      console.log("QML_SMOKE_PASSED: service, widget, panel, OSD and deferred selection")
      Qt.quit()
    }
  }
}
