import QtQuick
import Quickshell
import qs.Commons
import qs.Ui

BarWidget {
  id: root
  moduleName: "io.github.chivopic.input-switch"
  readonly property var inputService: bar && bar.shell ? bar.shell.serviceFor(moduleName) : null
  property bool popupOpen: false
  readonly property bool opened: popupOpen
  property string queuedLanguage: ""

  function configureService() {
    if (inputService) inputService.configure(setting("showOsd", true), setting("osdDuration", 700))
  }
  onInputServiceChanged: configureService()
  onSettingsChanged: configureService()

  function open() { popupOpen = true; if (inputService) inputService.send("status", "") }
  function close() { popupOpen = false }
  function togglePanel() { if (popupOpen) close(); else open() }

  function choose(language) {
    if (!inputService || inputService.pending || selectionTimer.running) return
    close()
    queuedLanguage = language
    // The popover fades out and releases its focus grab before changing IM.
    selectionTimer.restart()
  }

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: root.inputService ? root.inputService.label : "!"
    tooltipText: root.inputService ? root.inputService.tooltip : "输入法服务未就绪"
    horizontalMargin: 8
    fontSize: Style.font.body
    onPressed: function(mouseButton) {
      if (mouseButton === Qt.RightButton) root.togglePanel()
      else if (mouseButton === Qt.MiddleButton) {
        if (root.inputService) root.inputService.send("status", "")
      } else if (root.inputService && !selectionTimer.running) {
        if (root.popupOpen) { root.close(); toggleTimer.restart() }
        else root.inputService.send("toggle", "")
      }
    }
  }

  Timer {
    id: selectionTimer
    interval: 180
    onTriggered: if (root.inputService) root.inputService.send("set", root.queuedLanguage)
  }
  Timer {
    id: toggleTimer
    interval: 180
    onTriggered: if (root.inputService) root.inputService.send("toggle", "")
  }

  InputPanel {
    anchorItem: button
    bar: root.bar
    owner: root
    open: root.popupOpen
    inputService: root.inputService
    onLanguageChosen: language => root.choose(language)
  }
}
