from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
res = root / "android/app/src/main/res"
source = root / "kvk-logo.webp"
if not source.exists():
    raise SystemExit("kvk-logo.webp is missing")

# Android 8+ adaptive launcher icon: use the exact approved artwork, no extra tint or glow.
foreground = res / "drawable-nodpi"
foreground.mkdir(parents=True, exist_ok=True)
shutil.copyfile(source, foreground / "ic_launcher_foreground.webp")

v26 = res / "mipmap-anydpi-v26"
v26.mkdir(parents=True, exist_ok=True)
adaptive = """<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/kvk_icon_background"/>
    <foreground android:drawable="@drawable/ic_launcher_foreground"/>
</adaptive-icon>
"""
(v26 / "ic_launcher.xml").write_text(adaptive, encoding="utf-8")
(v26 / "ic_launcher_round.xml").write_text(adaptive, encoding="utf-8")

values = res / "values"
values.mkdir(parents=True, exist_ok=True)
(values / "kvk_icon_colors.xml").write_text(
    '<resources><color name="kvk_icon_background">#000000</color></resources>',
    encoding="utf-8"
)

strings = values / "strings.xml"
if strings.exists():
    tree = ET.parse(strings)
    root_xml = tree.getroot()
    app_name = root_xml.find("string[@name='app_name']")
    if app_name is None:
        app_name = ET.SubElement(root_xml, "string", {"name": "app_name"})
    app_name.text = "KVK HUB"
    tree.write(strings, encoding="utf-8", xml_declaration=True)
print("Applied the exact approved KVK HUB logo and app name.")
