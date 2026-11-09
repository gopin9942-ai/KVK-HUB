from pathlib import Path
import re
import xml.etree.ElementTree as ET
from PIL import Image

root = Path(__file__).resolve().parents[1]
res = root / "android/app/src/main/res"
source = root / "kvk-logo.webp"
if not source.exists():
    raise SystemExit("kvk-logo.webp is missing")

# Rebuild the supplied artwork as a transparent square PNG with Android's
# adaptive-icon safe area respected. Keep the full logo visible after masking.
with Image.open(source) as opened:
    artwork = opened.convert("RGBA")
artwork.thumbnail((680, 680), Image.Resampling.LANCZOS)
foreground_image = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
foreground_image.alpha_composite(
    artwork,
    ((1024 - artwork.width) // 2, (1024 - artwork.height) // 2)
)

foreground = res / "drawable-nodpi"
foreground.mkdir(parents=True, exist_ok=True)
foreground_file = foreground / "ic_launcher_foreground.png"
foreground_image.save(foreground_file, format="PNG", optimize=True)

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

# Legacy square icons for Android launchers that do not use adaptive icons.
for density, size in {
    "mdpi": 48,
    "hdpi": 72,
    "xhdpi": 96,
    "xxhdpi": 144,
    "xxxhdpi": 192,
}.items():
    folder = res / f"mipmap-{density}"
    folder.mkdir(parents=True, exist_ok=True)
    legacy_art = artwork.resize((int(size * 0.82), int(size * 0.82)), Image.Resampling.LANCZOS)
    icon = Image.new("RGBA", (size, size), (0, 0, 0, 255))
    icon.alpha_composite(legacy_art, ((size - legacy_art.width) // 2, (size - legacy_art.height) // 2))
    icon.convert("RGB").save(folder / "ic_launcher.png", optimize=True)
    icon.convert("RGB").save(folder / "ic_launcher_round.png", optimize=True)

    # Capacitor also generates a default blue foreground asset in each density.\n    # Replace it with the same KVK artwork so no launcher/resource variant\n    # can fall back to the Capacitor mark.\n    density_foreground = foreground_image.resize((size * 4, size * 4), Image.Resampling.LANCZOS)\n    density_foreground.save(folder / "ic_launcher_foreground.png", format="PNG", optimize=True)

# Explicitly point the generated Android manifest at our launcher resources.
manifest = root / "android/app/src/main/AndroidManifest.xml"
manifest_text = manifest.read_text(encoding="utf-8")
manifest_text, icon_count = re.subn(
    r'android:icon="[^"]+"',
    'android:icon="@mipmap/ic_launcher"',
    manifest_text,
    count=1
)
manifest_text, round_count = re.subn(
    r'android:roundIcon="[^"]+"',
    'android:roundIcon="@mipmap/ic_launcher_round"',
    manifest_text,
    count=1
)
if icon_count != 1:
    raise SystemExit("Could not set android:icon in the generated manifest")
if round_count == 0:
    manifest_text = manifest_text.replace(
        'android:icon="@mipmap/ic_launcher"',
        'android:icon="@mipmap/ic_launcher" android:roundIcon="@mipmap/ic_launcher_round"',
        1
    )
manifest.write_text(manifest_text, encoding="utf-8")

strings = values / "strings.xml"
if strings.exists():
    tree = ET.parse(strings)
    root_xml = tree.getroot()
    app_name = root_xml.find("string[@name='app_name']")
    if app_name is None:
        app_name = ET.SubElement(root_xml, "string", {"name": "app_name"})
    app_name.text = "KVK HUB"
    tree.write(strings, encoding="utf-8", xml_declaration=True)

# Fail early if the expected icon resources were not generated.
for required in [
    foreground_file,
    v26 / "ic_launcher.xml",
    v26 / "ic_launcher_round.xml",
    res / "mipmap-mdpi/ic_launcher.png",
]:
    if not required.is_file():
        raise SystemExit(f"Missing launcher resource: {required}")
if 'android:icon="@mipmap/ic_launcher"' not in manifest_text:
    raise SystemExit("Manifest does not reference the KVK HUB launcher icon")

print("Configured KVK HUB adaptive + legacy launcher icons and explicit manifest references.")
