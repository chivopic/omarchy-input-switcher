import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Wayland
import qs.Commons
import qs.Commons as Commons
import qs.Ui

Item {
  id: root
  property bool opened: false
  property string label: ""
  property string message: ""
  property string detail: ""
  property var targetScreen: null

  function show(nextLabel, nextMessage, nextDetail, duration) {
    label = nextLabel
    message = nextMessage
    detail = nextDetail
    var monitor = Hyprland.focusedMonitor
    var screens = Quickshell.screens
    targetScreen = screens.length ? screens[0] : null
    for (var i = 0; i < screens.length; i++) {
      if (monitor && screens[i].name === monitor.name) targetScreen = screens[i]
    }
    opened = targetScreen !== null
    hideTimer.interval = duration
    hideTimer.restart()
  }

  Timer { id: hideTimer; onTriggered: root.opened = false }

  PanelWindow {
    id: window
    screen: root.targetScreen
    visible: root.opened
    anchors { top: true; bottom: true; left: true; right: true }
    color: "transparent"
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "omarchy-input-switch-osd"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
    mask: Region { }

    BorderSurface {
      width: Math.min(Style.space(300), window.width - Style.space(24))
      height: row.implicitHeight + Style.space(28)
      anchors.horizontalCenter: parent.horizontalCenter
      anchors.bottom: parent.bottom
      anchors.bottomMargin: Style.space(70)
      color: Commons.Color.popups.background
      borderSpec: Border.surfaceSpec("popups", "border", Commons.Color.popups.border, Math.max(1, Style.space(1)))
      radius: Style.cornerRadius

      Row {
        id: row
        anchors.centerIn: parent
        spacing: Style.space(16)
        Text {
          text: root.label
          textFormat: Text.PlainText
          color: Commons.Color.accent
          font.family: Style.font.family
          font.pixelSize: Style.font.title
          anchors.verticalCenter: parent.verticalCenter
        }
        Column {
          spacing: Style.space(4)
          Text {
            text: root.message
            textFormat: Text.PlainText
            color: Commons.Color.foreground
            font.family: Style.font.family
            font.pixelSize: Style.font.body
          }
          Text {
            text: root.detail
            textFormat: Text.PlainText
            color: Commons.Color.muted
            font.family: Style.font.family
            font.pixelSize: Style.font.caption
            width: Math.min(implicitWidth, Style.space(150))
            elide: Text.ElideRight
          }
        }
      }
    }
  }
}
