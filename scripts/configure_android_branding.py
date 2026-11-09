from pathlib import Path
import xml.etree.ElementTree as ET

res = Path("android/app/src/main/res")
# Vector artwork: the same cyan outline gladiator helmet + microphone emblem used by the website.
vector = """<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="512" android:viewportHeight="512">
    <path android:fillColor="#08142E" android:pathData="M0,0h512v512h-512z"/>
    <group android:fillColor="@android:color/transparent" android:strokeColor="#42DFFF" android:strokeWidth="13" android:strokeLineCap="round" android:strokeLineJoin="round">
        <path android:pathData="M256,28C128,28 48,125 48,256s80,228 208,228 208,-97 208,-228S384,28 256,28Z" android:strokeAlpha="0.75"/>
        <path android:pathData="M178,112L116,78l48,82 -8,35 28,-12 16,-46 56,-47 56,47 16,46 28,12 -8,-35 48,-82 -62,34 -48,-43 -32,14 -32,-14Z"/>
        <path android:pathData="M178,169c-27,15 -44,43 -44,77v91c0,54 43,98 96,98h52c53,0 96,-44 96,-98v-91c0,-34 -17,-62 -44,-77l-78,-37 -78,37Z"/>
        <path android:pathData="M178,225l78,39 78,-39 -12,62 -66,42 -66,-42 -12,-62Z"/>
        <path android:pathData="M206,335h100M213,367h86"/>
        <path android:pathData="M134,265c-30,0 -46,20 -46,49v68c0,47 38,85 85,85h166c47,0 85,-38 85,-85v-68c0,-29 -16,-49 -46,-49"/>
        <path android:pathData="M256,467v25m-70,0h140"/>
    </group>
</vector>
"""
for folder in ["drawable","mipmap-anydpi"]:
    target = res / folder
    target.mkdir(parents=True, exist_ok=True)
    (target / ("ic_launcher_foreground.xml" if folder == "drawable" else "ic_launcher.xml")).write_text(vector if folder == "drawable" else """<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp" android:viewportWidth="512" android:viewportHeight="512">
    <path android:fillColor="#08142E" android:pathData="M0,0h512v512h-512z"/>
    <path android:fillColor="@android:color/transparent" android:strokeColor="#42DFFF" android:strokeWidth="13" android:strokeLineCap="round" android:strokeLineJoin="round" android:pathData="M256,28C128,28 48,125 48,256s80,228 208,228 208,-97 208,-228S384,28 256,28Z M178,112L116,78l48,82 -8,35 28,-12 16,-46 56,-47 56,47 16,46 28,12 -8,-35 48,-82 -62,34 -48,-43 -32,14 -32,-14Z M178,169c-27,15 -44,43 -44,77v91c0,54 43,98 96,98h52c53,0 96,-44 96,-98v-91c0,-34 -17,-62 -44,-77l-78,-37 -78,37Z M178,225l78,39 78,-39 -12,62 -66,42 -66,-42 -12,-62Z M206,335h100M213,367h86M134,265c-30,0 -46,20 -46,49v68c0,47 38,85 85,85h166c47,0 85,-38 85,-85v-68c0,-29 -16,-49 -46,-49M256,467v25m-70,0h140"/>
</vector>
""")
v26 = res / "mipmap-anydpi-v26"
v26.mkdir(parents=True, exist_ok=True)
adaptive = """<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/kvk_icon_background"/>
    <foreground android:drawable="@drawable/ic_launcher_foreground"/>
</adaptive-icon>
"""
(v26 / "ic_launcher.xml").write_text(adaptive)
(v26 / "ic_launcher_round.xml").write_text(adaptive)
colors = res / "values"
colors.mkdir(parents=True, exist_ok=True)
color_file = colors / "kvk_icon_colors.xml"
color_file.write_text("""<resources><color name="kvk_icon_background">#08142E</color></resources>""")

# Ensure Android's launcher label is consistently KVK HUB.
strings = colors / "strings.xml"
if strings.exists():
    tree = ET.parse(strings)
    root = tree.getroot()
    app_name = root.find("string[@name='app_name']")
    if app_name is None:
        app_name = ET.SubElement(root, "string", {"name": "app_name"})
    app_name.text = "KVK HUB"
    tree.write(strings, encoding="utf-8", xml_declaration=True)
print("Configured KVK HUB launcher icon and app label.")
