from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
from PIL import Image

root = Path(__file__).resolve().parents[1]
res = root / "android/app/src/main/res"
source = root / "kvk-logo.webp"
if not source.exists():
    raise SystemExit("kvk-logo.webp is missing")

# Use the approved transparent-padded artwork as the adaptive foreground.
foreground = res / "drawable-nodpi"
foreground.mkdir(parents=True, exist_ok=True)
shutil.copyfile(source, foreground / "ic_launcher_foreground.webp")

adaptive = """<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/kvk_icon_background"/>
    <foreground android:drawable="@drawable/ic_launcher_foreground"/>
</adaptive-icon>
"""
v26 = res / "mipmap-anydpi-v26"
v26.mkdir(parents=True, exist_ok=True)
(v26 / "ic_launcher.xml").write_text(adaptive, encoding="utf-8")
(v26 / "ic_launcher_round.xml").write_text(adaptive, encoding="utf-8")

values = res / "values"
values.mkdir(parents=True, exist_ok=True)
(values / "kvk_icon_colors.xml").write_text(
    '<resources><color name="kvk_icon_background">#000000</color></resources>',
    encoding="utf-8"
)

# Also replace legacy launcher assets for older Android versions/devices.
with Image.open(source) as opened:
    artwork = opened.convert("RGBA")
for density, size in {
    "mdpi": 48,
    "hdpi": 72,
    "xhdpi": 96,
    "xxhdpi": 144,
    "xxxhdpi": 192,
}.items():
    folder = res / f"mipmap-{density}"
    folder.mkdir(parents=True, exist_ok=True)
    scaled = artwork.resize((size, size), Image.Resampling.LANCZOS)
    icon = Image.new("RGBA", (size, size), (0, 0, 0, 255))
    icon.alpha_composite(scaled)
    icon.convert("RGB").save(folder / "ic_launcher.png", optimize=True)
    icon.convert("RGB").save(folder / "ic_launcher_round.png", optimize=True)

strings = values / "strings.xml"
if strings.exists():
    tree = ET.parse(strings)
    root_xml = tree.getroot()
    app_name = root_xml.find("string[@name='app_name']")
    if app_name is None:
        app_name = ET.SubElement(root_xml, "string", {"name": "app_name"})
    app_name.text = "KVK Hub"
    tree.write(strings, encoding="utf-8", xml_declaration=True)

print("Applied the approved KVK Hub launcher icon and display name.")
