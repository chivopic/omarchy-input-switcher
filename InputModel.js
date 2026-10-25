function label(state, pending) {
  if (pending) return "…"
  if (!state || !state.available) return "!"
  if (state.effectiveLanguage === "zh") return "中"
  if (state.effectiveLanguage === "en") return "EN"
  if (state.engine === "rime") return "RIME"
  return "?"
}

function description(state) {
  if (!state || !state.available) return "输入法未连接"
  if (state.effectiveLanguage === "zh") return "中文输入"
  if (state.effectiveLanguage === "en") return "英文输入"
  return "模式未确认"
}

function tooltip(state, pending, error) {
  var detail = description(state)
  if (pending) detail = "正在切换…"
  if (error) detail += "\n" + error
  else if (state && state.error) detail += "\n" + state.error
  return detail + "\n左键切换 · 右键设置"
}

if (typeof module !== "undefined") module.exports = {label: label, description: description, tooltip: tooltip}
