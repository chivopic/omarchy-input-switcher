import QtQuick
import qs.Commons
import qs.Commons as Commons
import qs.Ui

PopupCard {
  id: root
  property var inputService: null
  readonly property var state: inputService ? inputService.snapshot : ({})
  readonly property bool busy: inputService ? inputService.pending : false
  readonly property string problem: inputService ? (inputService.lastError || state.error || "") : "输入法服务未就绪"
  signal languageChosen(string language)
  contentWidth: fittedContentWidth(Style.space(310))
  contentHeight: fittedContentHeight(content.implicitHeight)

  Column {
    id: content
    width: parent.width
    spacing: Style.space(12)

    Row {
      width: parent.width
      Text {
        width: parent.width * 0.45
        text: "输入法"
        textFormat: Text.PlainText
        color: Commons.Color.foreground
        font.family: Style.font.family
        font.pixelSize: Style.font.subtitle
      }
      Text {
        width: parent.width * 0.55
        text: root.state.engine === "rime" ? "Rime" : root.state.engine === "keyboard-us" ? "English (US)" : (root.state.engine || "未连接")
        textFormat: Text.PlainText
        color: Commons.Color.muted
        font.family: Style.font.family
        font.pixelSize: Style.font.body
        horizontalAlignment: Text.AlignRight
        elide: Text.ElideRight
      }
    }

    Row {
      width: parent.width
      spacing: Style.space(8)
      Button {
        width: (parent.width - parent.spacing) / 2
        text: "中文"
        selected: root.state.effectiveLanguage === "zh"
        enabled: !root.busy && root.state.available === true && root.state.preciseRime === true && (root.state.engines || []).indexOf("rime") !== -1
        opacity: enabled ? 1 : 0.45
        focusable: true
        onClicked: root.languageChosen("zh")
      }
      Button {
        width: (parent.width - parent.spacing) / 2
        text: "English"
        selected: root.state.effectiveLanguage === "en"
        enabled: !root.busy && root.state.available === true && (root.state.engines || []).indexOf("keyboard-us") !== -1
        opacity: enabled ? 1 : 0.45
        focusable: true
        onClicked: root.languageChosen("en")
      }
    }

    Text {
      width: parent.width
      visible: text !== ""
      text: root.state.schema || (root.state.available && !root.state.preciseRime ? "此 Rime 未提供精确模式接口" : "")
      textFormat: Text.PlainText
      color: Commons.Color.muted
      font.family: Style.font.family
      font.pixelSize: Style.font.caption
      wrapMode: Text.Wrap
    }

    Text {
      width: parent.width
      visible: root.problem !== ""
      text: root.problem
      textFormat: Text.PlainText
      color: Commons.Color.urgent
      font.family: Style.font.family
      font.pixelSize: Style.font.bodySmall
      wrapMode: Text.Wrap
    }

    PanelSeparator { }

    Text {
      width: parent.width
      text: "保留现有 Fcitx5 切换快捷键"
      textFormat: Text.PlainText
      color: Commons.Color.muted
      font.family: Style.font.family
      font.pixelSize: Style.font.caption
      wrapMode: Text.Wrap
    }

    Button {
      width: parent.width
      text: root.busy ? "正在检查…" : "检查连接"
      enabled: !root.busy
      focusable: true
      onClicked: if (root.inputService) root.inputService.send("status", "")
    }
  }
}
