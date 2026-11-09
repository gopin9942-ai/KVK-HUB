from pathlib import Path
import re
import xml.etree.ElementTree as ET
from PIL import Image, ImageChops

root = Path(__file__).resolve().parents[1]
res = root / "android/app/src/main/res"
source = root / "kvk-logo.webp"
if not source.exists():
    raise SystemExit("kvk-logo.webp is missing")

# Start from a clean slate: remove every old launcher icon in every resource
# qualifier so Android cannot select a stale Capacitor/default icon.
removed = []
for candidate in list(res.rglob("ic_launcher*")):
    if candidate.is_file():
        removed.append(str(candidate.relative_to(res)))
        candidate.unlink()
print("Cleared old launcher resources:", removed)

# The supplied logo file has a black canvas around the blue KVK artwork.
# Crop that empty black area first; simply enlarging the full square image
# would enlarge the black padding rather than the visible logo.
with Image.open(source) as opened:
    original = opened.convert("RGBA")

# Detect the actual colored KVK artwork, not tiny compression/noise
# variations in the surrounding black canvas.
rgb = original.convert("RGB")
pixels = rgb.load()
xs, ys = [], []
for y in range(rgb.height):
    for x in range(rgb.width):
        red, green, blue = pixels[x, y]
        brightest = max(red, green, blue)
        saturation = brightest - min(red, green, blue)
        if brightest >= 48 and (saturation >= 24 or brightest >= 105):
            xs.append(x)
            ys.append(y)
if not xs:
    raise SystemExit("Could not detect visible KVK logo artwork")

left, right = min(xs), max(xs) + 1
top, bottom = min(ys), max(ys) + 1
pad_x = max(3, int((right - left) * 0.06))
pad_y = max(3, int((bottom - top) * 0.06))
left = max(0, left - pad_x)
top = max(0, top - pad_y)
right = min(original.width, right + pad_x)
bottom = min(original.height, bottom + pad_y)
artwork = original.crop((left, top, right, bottom))
print(f"Cropped KVK artwork from {original.size} to {artwork.size}")

# Adaptive icons are masked by Android. Keep the artwork inside the central
# safe circle, but make the visible logo itself large instead of scaling its
# original black square canvas.
artwork = artwork.resize((artwork.width * 2, artwork.height * 2), Image.Resampling.LANCZOS)
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

# Rebuild all legacy density icons from the cropped visible artwork too.
for density, size in {
    "mdpi": 48,
    "hdpi": 72,
    "xhdpi": 96,
    "xxhdpi": 144,
    "xxxhdpi": 192,
}.items():
    folder = res / f"mipmap-{density}"
    folder.mkdir(parents=True, exist_ok=True)
    legacy_art = artwork.copy()
    legacy_art.thumbnail((int(size * 0.92), int(size * 0.92)), Image.Resampling.LANCZOS)
    icon = Image.new("RGBA", (size, size), (0, 0, 0, 255))
    icon.alpha_composite(
        legacy_art,
        ((size - legacy_art.width) // 2, (size - legacy_art.height) // 2)
    )
    icon.convert("RGB").save(folder / "ic_launcher.png", optimize=True)
    icon.convert("RGB").save(folder / "ic_launcher_round.png", optimize=True)

# Explicitly point the Android manifest at the rebuilt launcher resources.
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

# Fail early if any competing launcher resource survived the clean rebuild.
remaining = [
    str(path.relative_to(res))
    for path in res.rglob("ic_launcher*")
    if path.is_file() and path not in {
        foreground_file,
        v26 / "ic_launcher.xml",
        v26 / "ic_launcher_round.xml",
        res / "mipmap-mdpi/ic_launcher.png",
        res / "mipmap-mdpi/ic_launcher_round.png",
        res / "mipmap-hdpi/ic_launcher.png",
        res / "mipmap-hdpi/ic_launcher_round.png",
        res / "mipmap-xhdpi/ic_launcher.png",
        res / "mipmap-xhdpi/ic_launcher_round.png",
        res / "mipmap-xxhdpi/ic_launcher.png",
        res / "mipmap-xxhdpi/ic_launcher_round.png",
        res / "mipmap-xxxhdpi/ic_launcher.png",
        res / "mipmap-xxxhdpi/ic_launcher_round.png",
    }
]
if remaining:
    raise SystemExit(f"Unexpected competing launcher resources remain: {remaining}")
if 'android:icon="@mipmap/ic_launcher"' not in manifest_text:
    raise SystemExit("Manifest does not reference the KVK HUB launcher icon")

print("Cleaned and rebuilt KVK HUB launcher icons from tightly cropped logo artwork.")
