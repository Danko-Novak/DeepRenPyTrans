#!/usr/bin/env bash
# ============================================================
# DeepRenPyTrans APK Builder v1.0 (Linux Edition)
# ============================================================

echo "============================================================"
echo "  DeepRenPyTrans APK Builder v1.0 (Linux Edition)"
echo "  PC 240_026 + Russian Translation - Android APK"
echo "============================================================"
echo ""

# ============================================================
# CONFIGURATION
# ============================================================
# Path configuration (using relative paths for portability)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/spacejourneyx-205_010c-release.apk" ]; then
    OLD_APK="$SCRIPT_DIR/spacejourneyx-205_010c-release.apk"
    PC_GAME="$SCRIPT_DIR/SpaceJourneyX-240_026-pc/game"
    WORK_DIR="$SCRIPT_DIR/apk_work"
    OUTPUT_APK="$SCRIPT_DIR/SpaceJourneyX-240_026-RU.apk"
else
    OLD_APK="$SCRIPT_DIR/../spacejourneyx-205_010c-release.apk"
    PC_GAME="$SCRIPT_DIR/../SpaceJourneyX-240_026-pc/game"
    WORK_DIR="$SCRIPT_DIR/../apk_work"
    OUTPUT_APK="$SCRIPT_DIR/../SpaceJourneyX-240_026-RU.apk"
fi

# Determine 7-Zip executable
if command -v 7z &> /dev/null; then
    SEVENZ="7z"
elif command -v 7za &> /dev/null; then
    SEVENZ="7za"
else
    SEVENZ=""
fi

# --- Feature Flags (1 = Enabled, 0 = Disabled) ---
RESTORE_OLD_ASSETS=1
COMPRESS_AUDIO=1
COMPRESS_IMAGES=1
INJECT_TRANSLATION=1
LANG_FOLDER="russian"
COMPRESSION_LEVEL=9

# Environment variables for Python scripts
export OLD_APK="$OLD_APK"
export TARGET_DIR="${WORK_DIR}/game"
export RESTORED_JSON="${WORK_DIR}/restored_assets.json"

# Resolve absolute output path for 7z repacking step
if [[ "$OUTPUT_APK" = /* ]]; then
    ABS_OUTPUT_APK="$OUTPUT_APK"
else
    ABS_OUTPUT_APK="$PWD/$OUTPUT_APK"
fi

# ============================================================
# STEP 0: Check tools
# ============================================================
echo "[0/7] Checking tools..."

if [ -z "$SEVENZ" ]; then
    echo "  [ERROR] 7-Zip not found!"
    echo "  Install: sudo pacman -S p7zip (Arch/CachyOS) or apt install p7zip-full (Debian)"
    exit 1
fi
echo "  [OK] 7-Zip found ($SEVENZ)"

if command -v ffmpeg &> /dev/null; then
    echo "  [OK] ffmpeg found"
    HAS_FFMPEG=1
else
    echo "  [WARN] ffmpeg NOT found - audio compression SKIPPED"
    echo "         Install: sudo pacman -S ffmpeg"
    HAS_FFMPEG=0
fi
echo ""

# ============================================================
# STEP 1: Copy game files to working directory
# ============================================================
echo "[1/7] Preparing working copy..."

rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR/game"
echo "  Copying game files (this may take a minute)..."
cp -a "$PC_GAME/." "$WORK_DIR/game/"
echo "  [OK] Game files copied"

# Clean PC-only junk
rm -f "$WORK_DIR/game/check_translation.py"
rm -f "$WORK_DIR/game/untranslated.log"
rm -f "$WORK_DIR/game/testfile.txt"
rm -f "$WORK_DIR/game/extracted_strings.json"
rm -f "$WORK_DIR/game/strings_to_translate.json"
rm -f "$WORK_DIR/game/translation_source.json"
rm -rf "$WORK_DIR/game/saves"
rm -rf "$WORK_DIR/game/cache"
echo "  [OK] Cleaned PC-only files"
echo ""

# ============================================================
# STEP 1.5: Restore compressed assets from old APK
# ============================================================
if [ "$RESTORE_OLD_ASSETS" -eq 1 ]; then
    echo "[1.5/7] Restoring compressed assets from old APK..."
    if command -v python3 &> /dev/null; then
        python3 "$SCRIPT_DIR/restore_compressed_assets.py"
    else
        echo "  [WARN] Python3 NOT found - asset restoration SKIPPED!"
    fi
    echo ""
else
    echo "[1.5/7] Asset restoration SKIPPED by configuration."
    echo ""
fi

# ============================================================
# STEP 2: Compress .wav -> .ogg
# ============================================================
if [ "$COMPRESS_AUDIO" -eq 1 ]; then
    echo "[2/7] Compressing audio..."
    if [ "$HAS_FFMPEG" -eq 1 ]; then
        echo "  Converting WAV files to OGG in parallel..."
        if command -v nproc &> /dev/null; then
            CORES=$(nproc)
        elif command -v sysctl &> /dev/null; then
            CORES=$(sysctl -n hw.ncpu)
        else
            CORES=4
        fi
        RUNNING_JOBS=0
        while read -r f; do
            ogg_file="${f%.wav}.ogg"
            ffmpeg -hide_banner -loglevel error -y -i "$f" -c:a libvorbis -q:a 4 "$ogg_file" 2>/dev/null && rm -f "$f" &
            RUNNING_JOBS=$((RUNNING_JOBS + 1))
            if [ "$RUNNING_JOBS" -ge "$CORES" ]; then
                wait -n
                RUNNING_JOBS=$((RUNNING_JOBS - 1))
            fi
        done < <(find "$WORK_DIR/game/audio" -type f -name "*.wav" 2>/dev/null)
        wait
        echo "  [OK] Audio conversion completed."

        echo "  Patching .rpy audio references..."
        # We use Python to patch all .rpy files replacing .wav with .ogg safely (handles BSD vs GNU sed differences on macOS/Linux)
        python3 -c "
import os
for root, dirs, files in os.walk('$WORK_DIR/game'):
    for f in files:
        if f.endswith('.rpy'):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                new_content = content.replace('.wav\"', '.ogg\"').replace('.wav)', '.ogg)')
                if new_content != content:
                    with open(path, 'w', encoding='utf-8') as file:
                        file.write(new_content)
            except Exception:
                pass
"
        echo "  [OK] Audio references patched (.wav -> .ogg)"

        echo "  [INFO] Keeping .rpyc files (Android assets are read-only and cannot compile .rpy at runtime)"
    else
        echo "  [SKIP] No ffmpeg - keeping original .wav files"
        echo "         APK will be ~160 MB larger!"
    fi
    echo ""
else
    echo "[2/7] Audio compression SKIPPED by configuration."
    echo ""
fi

# ============================================================
# STEP 2.5: Compress images for mobile
# ============================================================
if [ "$COMPRESS_IMAGES" -eq 1 ]; then
    echo "[2.5/7] Optimizing images for mobile..."
    if command -v python3 &> /dev/null; then
        python3 "$SCRIPT_DIR/compress_assets.py"
    else
        echo "  [WARN] Python3 NOT found - image compression SKIPPED!"
    fi
    echo ""
else
    echo "[2.5/7] Image optimization SKIPPED by configuration."
    echo ""
fi

# ============================================================
# STEP 2.7: Compile game scripts (.rpy -> .rpyc)
# ============================================================
echo "[2.7/7] Skipping PC script compilation to avoid Android path issues..."
# Android will automatically compile the .rpy scripts on first launch correctly using forward slashes.
echo ""

# ============================================================
# STEP 3: Extract old APK shell
# ============================================================
echo "[3/7] Extracting APK shell from old version..."

mkdir -p "$WORK_DIR/apk_shell"
"$SEVENZ" x "$OLD_APK" -o"$WORK_DIR/apk_shell" -y >/dev/null 2>&1
echo "  [OK] APK extracted"

ASSETS_GAME=""
if [ -d "$WORK_DIR/apk_shell/assets/game" ]; then
    ASSETS_GAME="$WORK_DIR/apk_shell/assets/game"
elif [ -d "$WORK_DIR/apk_shell/assets/x-game" ]; then
    ASSETS_GAME="$WORK_DIR/apk_shell/assets/x-game"
elif [ -d "$WORK_DIR/apk_shell/assets/x-game/game" ]; then
    ASSETS_GAME="$WORK_DIR/apk_shell/assets/x-game/game"
fi

if [ -z "$ASSETS_GAME" ]; then
    echo "  [WARN] WARNING: Standard game path not found!"
    echo "         Scanning assets directory..."
    FOUND_RPY=$(find "$WORK_DIR/apk_shell/assets/" -name "*.rpy" -o -name "*.rpyc" | head -n 1)
    if [ -n "$FOUND_RPY" ]; then
        ASSETS_GAME=$(dirname "$FOUND_RPY")
    else
        echo "  [ERROR] Cannot locate game files in APK!"
        exit 1
    fi
fi
echo "  [OK] Game assets at: $ASSETS_GAME"
echo ""

# ============================================================
# STEP 4: Replace game content
# ============================================================
echo "[4/7] Injecting game content..."

python3 "$SCRIPT_DIR/inject_x_assets.py" "$WORK_DIR/game" "$ASSETS_GAME"
echo "  [OK] Game content replaced"

if [ "$INJECT_TRANSLATION" -eq 1 ]; then
    if [ -f "$ASSETS_GAME/x-tl/x-$LANG_FOLDER/x-hooks.rpy" ]; then echo "  [OK] hooks.rpy present"; else echo "  [WARN] hooks.rpy MISSING!"; fi
    if [ -f "$ASSETS_GAME/x-tl/x-$LANG_FOLDER/x-dictionary.json" ]; then echo "  [OK] dictionary.json present"; else echo "  [WARN] dictionary.json MISSING!"; fi
else
    echo "  [INFO] Translation injection disabled. Removing translation folders..."
    rm -rf "$ASSETS_GAME/x-tl/x-$LANG_FOLDER" 2>/dev/null
fi
echo ""

# ============================================================
# STEP 5: Clean APK metadata
# ============================================================
echo "[5/7] Cleaning signatures..."

rm -rf "$WORK_DIR/apk_shell/META-INF"
echo "  [OK] Old signatures removed"
echo ""

# ============================================================
# STEP 6: Repack APK
# ============================================================
echo "[6/7] Repacking APK (this may take a few minutes)..."

rm -f "$OUTPUT_APK"

pushd "$WORK_DIR/apk_shell" >/dev/null
"$SEVENZ" a -tzip "$ABS_OUTPUT_APK" * -mx=$COMPRESSION_LEVEL -mmt=on >/dev/null 2>&1
popd >/dev/null

if [ ! -f "$OUTPUT_APK" ]; then
    echo "  [ERROR] Failed to create APK!"
    exit 1
fi

APK_MB=$(du -m "$OUTPUT_APK" | cut -f1)
echo "  [OK] APK created: ${APK_MB} MB"
echo ""

# ============================================================
# STEP 7: Sign APK
# ============================================================
echo "[7/7] Signing APK..."

SIGNED=0
KS="$WORK_DIR/debug.keystore"

HAS_APKSIGNER=0
HAS_JARSIGNER=0
HAS_KEYTOOL=0

if command -v apksigner &> /dev/null; then HAS_APKSIGNER=1; fi
if command -v jarsigner &> /dev/null; then HAS_JARSIGNER=1; fi
if command -v keytool &> /dev/null; then HAS_KEYTOOL=1; fi

if [ "$HAS_KEYTOOL" -eq 1 ]; then
    if [ ! -f "$KS" ]; then
        keytool -genkey -v -keystore "$KS" -alias debugkey -keyalg RSA -keysize 2048 -validity 10000 -storepass android -keypass android -dname "CN=Debug,O=Debug,C=US" >/dev/null 2>&1
    fi
fi

if [ "$HAS_APKSIGNER" -eq 1 ] && [ -f "$KS" ]; then
    apksigner sign --ks "$KS" --ks-key-alias debugkey --ks-pass pass:android "$OUTPUT_APK" >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        SIGNED=1
        echo "  [OK] Signed with apksigner"
    fi
fi

if [ "$SIGNED" -eq 0 ] && [ "$HAS_JARSIGNER" -eq 1 ] && [ -f "$KS" ]; then
    jarsigner -sigalg SHA256withRSA -digestalg SHA-256 -keystore "$KS" -storepass android "$OUTPUT_APK" debugkey >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        SIGNED=1
        echo "  [OK] Signed with jarsigner"
    fi
fi

if [ "$SIGNED" -eq 0 ]; then
    echo "  [WARN] APK NOT SIGNED - no signing tools found"
    echo ""
    echo "  To sign manually, install ONE of these:"
    echo "    Option 1: Android Build Tools (apksigner) - sudo pacman -S android-tools"
    echo "    Option 2: JDK (jarsigner+keytool) - sudo pacman -S jdk-openjdk"
    echo "    Option 3: uber-apk-signer (standalone JAR)"
fi

echo ""
echo "============================================================"
FINAL_MB=$(du -m "$OUTPUT_APK" | cut -f1)
echo "  OUTPUT:  $OUTPUT_APK"
echo "  SIZE:    ${FINAL_MB} MB"
if [ "$SIGNED" -eq 1 ]; then
    echo "  STATUS:  Ready to install!"
else
    echo "  STATUS:  Needs signing before install"
fi
echo "============================================================"
echo ""
echo "  To install: adb install -r $OUTPUT_APK"
echo "  NOTE: Uninstall old version first if signed with different key"
echo ""
