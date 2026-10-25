import QtQuick
import Quickshell
import qs.Commons
import qs.Commons as Commons
import qs.Ui

// Render the actual plugin component with sample state, without desktop capture.
ShellRoot {
  id: root
  readonly property string project: Quickshell.env("INPUT_SWITCH_PROJECT")
  readonly property string output: Quickshell.env("INPUT_SWITCH_ASSETS")
  property bool english: false
  property int saved: 0

  QtObject {
    id: sample
    property var snapshot: ({available:true,engine:"rime",effectiveLanguage:"zh",preciseRime:true,engines:["keyboard-us","rime"],schema:"rime_ice",error:""})
    property bool pending: false
    property string lastError: ""
    function send(operation, language) { return "queued" }
  }
  QtObject {
    id: previewBar
    property bool vertical: false
    property int barSize: 28
    property string position: "top"
    property string fontFamily: Style.font.family
    property color barForeground: Commons.Color.foreground
    property color foreground: Commons.Color.foreground
    property color urgent: Commons.Color.urgent
    property bool foregroundAnimationEnabled: false
    property var activePopout: null
    function requestPopout(item) { activePopout = item }
    function releasePopout(item) { activePopout = null }
  }
  FloatingWindow {
    title: "Input Switch documentation preview"
    visible: true
    implicitWidth: 380
    implicitHeight: 320
    color: Commons.Color.background
    Item { id: anchor; x:160; y:20; width:28; height:28 }
  }
  Loader {
    id: panel
    Component.onCompleted: setSource(root.project + "/InputPanel.qml", {
      anchorItem: anchor, bar: previewBar, inputService: sample,
      triggerMode: "hover", open: true
    })
    onLoaded: capture.start()
  }
  Timer {
    id: capture
    interval: 600
    onTriggered: {
      Commons.Color.shellValues = ({})
      Commons.Color.background = "#151c25"
      Commons.Color.foreground = "#e8edf3"
      Commons.Color.accent = "#a8d5bf"
      Commons.Color.muted = "#a0adbc"
      Style.cornerRadius = 10
      var card = panel.item.contentItem[0].parent.parent
      card.grabToImage(function(result) {
        var path = root.output + "/panel-" + (root.english ? "english" : "chinese") + ".png"
        if (result.saveToFile(path)) root.saved += 1
        if (!root.english) {
          root.english = true
          sample.snapshot = {available:true,engine:"keyboard-us",effectiveLanguage:"en",preciseRime:true,engines:["keyboard-us","rime"],schema:"",error:""}
          capture.restart()
        } else {
          console.log("DOC_PREVIEWS_SAVED",root.saved)
          Qt.quit()
        }
      },Qt.size(Math.ceil(card.width*3),Math.ceil(card.height*3)))
    }
  }
  Timer { interval:8000; running:true; onTriggered:Qt.quit() }
}
