#!/usr/bin/env python3
"""Render the QML sample states, then compose the README language preview."""
import base64
from pathlib import Path
import struct
import subprocess
import tempfile

DOCS = Path(__file__).resolve().parent
ASSETS = DOCS / "assets"


def main() -> None:
    # Keep the composite in sync with the actual QML component previews.
    subprocess.run(["python3", str(DOCS / "render-previews.py")], check=True)

    chinese = base64.b64encode((ASSETS / "panel-chinese.png").read_bytes()).decode("ascii")
    english = base64.b64encode((ASSETS / "panel-english.png").read_bytes()).decode("ascii")
    panel_height = 300

    def image_dimensions(name: str, center_x: int) -> tuple[float, float]:
        data = (ASSETS / name).read_bytes()
        width, height = struct.unpack(">II", data[16:24])
        display_width = panel_height * width / height
        return center_x - display_width / 2, display_width

    chinese_x, chinese_width = image_dimensions("panel-chinese.png", 300)
    english_x, english_width = image_dimensions("panel-english.png", 900)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="510" viewBox="0 0 1200 510">
  <rect x="18" y="18" width="564" height="474" rx="18" fill="#f1f3f0" stroke="#d9dfda" stroke-width="2"/>
  <rect x="618" y="18" width="564" height="474" rx="18" fill="#f1f3f0" stroke="#d9dfda" stroke-width="2"/>
  <g font-family="Inter, 'Noto Sans', Arial, sans-serif" fill="#26332c">
    <text x="48" y="66" font-size="17" font-weight="650" letter-spacing="1.2">中文 <tspan fill="#738279" font-weight="400">/ RIME · RIME_ICE</tspan></text>
    <text x="648" y="66" font-size="17" font-weight="650" letter-spacing="1.2">ENGLISH <tspan fill="#738279" font-weight="400">/ US KEYBOARD</tspan></text>
  </g>
  <image x="{chinese_x:.2f}" y="112" width="{chinese_width:.2f}" height="{panel_height}" preserveAspectRatio="none" href="data:image/png;base64,{chinese}"/>
  <image x="{english_x:.2f}" y="112" width="{english_width:.2f}" height="{panel_height}" preserveAspectRatio="none" href="data:image/png;base64,{english}"/>
  <g font-family="Inter, 'Noto Sans', Arial, sans-serif" font-size="14" fill="#67766d">
    <text x="48" y="457">Sample Chinese state</text><text x="648" y="457">Sample English state</text>
  </g>
</svg>'''
    with tempfile.TemporaryDirectory(prefix="input-switch-preview-") as temporary:
        source = Path(temporary) / "language-panels.svg"
        source.write_text(svg, encoding="utf-8")
        subprocess.run(
            ["rsvg-convert", "-o", str(ASSETS / "language-panels.png"), str(source)],
            check=True,
        )
    print(f"Wrote {ASSETS / 'language-panels.png'}")


if __name__ == "__main__":
    main()
