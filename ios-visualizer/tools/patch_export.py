#!/usr/bin/env python3
"""Apply the native receiver bridge to the exact sanitized Unity 6000.5.10f1 export.

Run after verifying the import baseline. This changes only Assembly-CSharp.cpp;
linking Week7Start/Week7CopyDisplay/Week7Stop into UnityFramework is a separate step.
Unknown exports and edited patches are rejected without writing. Re-exporting
from Unity requires a reviewed update of these signatures and hashes.
"""

import argparse
import hashlib
import os
from pathlib import Path
import stat
import sys
import tempfile


SOURCE = Path("Il2CppOutputProject/Source/il2cppOutput/Assembly-CSharp.cpp")
ORIGINAL_SHA256 = "a0a1d09266554b15e8f1fd60677db1cd60ec1b125d8d7108f111e0a25fe2a92c"
PREVIOUS_PATCH_SHA256 = "da960b5edf4168811b67fd1d5c7784f6fc76637bd46e398525f69b2451d153ca"
PATCHED_SHA256 = "0cabc95f2c08e96b94998b3f12d34b2fd54da62408dd85d41664b09aaf11ef9c"
RECEIVER = "TlsDataReceiver_t47A6D7DD24307D9353B230F8ADB4F931DBCB4C6E"

DECLARATIONS = b'''// Week 7 native client bridge. Applied by ios-visualizer/tools/patch_export.py.
extern "C" void Week7Start(void);
extern "C" int32_t Week7CopyDisplay(char* buffer, int32_t capacity);
extern "C" void Week7Stop(void);
'''

LAYOUT_DECLARATIONS = b'''// Week 7 display layout declarations.
struct TMP_Text_tE8D677872D43AD4B2AAF0D6101692A17D0B251A9;
struct RectTransform_t6C5DA5E41A89E0F488B001E45E58963480E543A5;
struct Vector2_t1FD6F485C871E832B347AB2DC8CBA08B739D8DF7;
IL2CPP_EXTERN_C IL2CPP_METHOD_ATTR RectTransform_t6C5DA5E41A89E0F488B001E45E58963480E543A5* TMP_Text_get_rectTransform_m22DC10116809BEB2C66047A55337A588ED023EBF (TMP_Text_tE8D677872D43AD4B2AAF0D6101692A17D0B251A9*, const RuntimeMethod*);
IL2CPP_EXTERN_C IL2CPP_METHOD_ATTR void RectTransform_set_anchorMin_m931442ABE3368D6D4309F43DF1D64AB64B0F52E3 (RectTransform_t6C5DA5E41A89E0F488B001E45E58963480E543A5*, Vector2_t1FD6F485C871E832B347AB2DC8CBA08B739D8DF7, const RuntimeMethod*);
IL2CPP_EXTERN_C IL2CPP_METHOD_ATTR void RectTransform_set_anchorMax_m52829ABEDD229ABD3DA20BCA676FA1DCA4A39B7D (RectTransform_t6C5DA5E41A89E0F488B001E45E58963480E543A5*, Vector2_t1FD6F485C871E832B347AB2DC8CBA08B739D8DF7, const RuntimeMethod*);
IL2CPP_EXTERN_C IL2CPP_METHOD_ATTR void RectTransform_set_offsetMin_m07F38B4105C7CA9CC9FBDC9ED0DB008602880AB9 (RectTransform_t6C5DA5E41A89E0F488B001E45E58963480E543A5*, Vector2_t1FD6F485C871E832B347AB2DC8CBA08B739D8DF7, const RuntimeMethod*);
IL2CPP_EXTERN_C IL2CPP_METHOD_ATTR void RectTransform_set_offsetMax_m5514D09D86516F2C0E25FA6D11A3A4274D3D002D (RectTransform_t6C5DA5E41A89E0F488B001E45E58963480E543A5*, Vector2_t1FD6F485C871E832B347AB2DC8CBA08B739D8DF7, const RuntimeMethod*);
IL2CPP_EXTERN_C IL2CPP_METHOD_ATTR void TMP_Text_set_fontSize_m1C3A3BA2BC88E5E1D89375FD35A0AA91E75D3AAD (TMP_Text_tE8D677872D43AD4B2AAF0D6101692A17D0B251A9*, float, const RuntimeMethod*);
IL2CPP_EXTERN_C IL2CPP_METHOD_ATTR void TMP_Text_set_fontSizeMin_mEAF970BB9CA053DF953AF83E638EA0F1D885358F (TMP_Text_tE8D677872D43AD4B2AAF0D6101692A17D0B251A9*, float, const RuntimeMethod*);
IL2CPP_EXTERN_C IL2CPP_METHOD_ATTR void TMP_Text_set_fontSizeMax_mC84B7090F5CE69BA63556A71FD63ABD67C911750 (TMP_Text_tE8D677872D43AD4B2AAF0D6101692A17D0B251A9*, float, const RuntimeMethod*);
IL2CPP_EXTERN_C IL2CPP_METHOD_ATTR void TMP_Text_set_enableAutoSizing_mDD34BC7AA735EEBEB916FF5C9791B1502F65FBCA (TMP_Text_tE8D677872D43AD4B2AAF0D6101692A17D0B251A9*, bool, const RuntimeMethod*);
// End Week 7 display layout declarations.
'''

PREVIOUS_START = '''{
    (void)__this;
    (void)method;
    Week7Start();
}'''

# Method names, original body hashes, and replacements are pinned to the import.
# The receiver layout, constructor, scene, and IL2CPP registration remain intact.
METHODS = (
    (
        "Start_m7C5A4A901498D34F398FC637D16CEA685691AE89",
        "2e789890bd2bf233a603a19008e08c699d896aac911028407fcb39c347000433",
        '''{
    (void)method;
    static bool s_Il2CppMethodInitialized;
    if (!s_Il2CppMethodInitialized)
    {
        il2cpp_codegen_initialize_runtime_metadata((uintptr_t*)&Object_tC12DECB6760A7F2CBF65D9DCF18D044C2D97152C_il2cpp_TypeInfo_var);
        s_Il2CppMethodInitialized = true;
    }
    TMP_Text_tE8D677872D43AD4B2AAF0D6101692A17D0B251A9* label = __this->___displayText;
    il2cpp_codegen_runtime_class_init_inline(Object_tC12DECB6760A7F2CBF65D9DCF18D044C2D97152C_il2cpp_TypeInfo_var);
    if (Object_op_Inequality_mD0BE578448EAA61948F25C32F8DD55AB1F778602(label, (Object_tC12DECB6760A7F2CBF65D9DCF18D044C2D97152C*)NULL, NULL))
    {
        // Keep the scene's label; its imported 200x50 rectangle cannot fit four rows.
        RectTransform_t6C5DA5E41A89E0F488B001E45E58963480E543A5* rect = TMP_Text_get_rectTransform_m22DC10116809BEB2C66047A55337A588ED023EBF(label, NULL);
        Vector2_t1FD6F485C871E832B347AB2DC8CBA08B739D8DF7 minimum = {};
        minimum.___x = 0.05f; minimum.___y = 0.10f;
        Vector2_t1FD6F485C871E832B347AB2DC8CBA08B739D8DF7 maximum = {};
        maximum.___x = 0.95f; maximum.___y = 0.80f;
        Vector2_t1FD6F485C871E832B347AB2DC8CBA08B739D8DF7 zero = {};
        RectTransform_set_anchorMin_m931442ABE3368D6D4309F43DF1D64AB64B0F52E3(rect, minimum, NULL);
        RectTransform_set_anchorMax_m52829ABEDD229ABD3DA20BCA676FA1DCA4A39B7D(rect, maximum, NULL);
        RectTransform_set_offsetMin_m07F38B4105C7CA9CC9FBDC9ED0DB008602880AB9(rect, zero, NULL);
        RectTransform_set_offsetMax_m5514D09D86516F2C0E25FA6D11A3A4274D3D002D(rect, zero, NULL);
        TMP_Text_set_fontSize_m1C3A3BA2BC88E5E1D89375FD35A0AA91E75D3AAD(label, 36.0f, NULL);
        TMP_Text_set_fontSizeMin_mEAF970BB9CA053DF953AF83E638EA0F1D885358F(label, 18.0f, NULL);
        TMP_Text_set_fontSizeMax_mC84B7090F5CE69BA63556A71FD63ABD67C911750(label, 36.0f, NULL);
        TMP_Text_set_enableAutoSizing_mDD34BC7AA735EEBEB916FF5C9791B1502F65FBCA(label, true, NULL);
    }
    Week7Start();
}''',
    ),
    (
        "ListenLoop_mC778FA1AC20130C281CDEFE163E0E5A9B9CAB214",
        "24169691a8803042414a3530f1c3ace4ae7e015fd7b966b01de53eea99aa3fa4",
        '''{
    // The obsolete inbound TLS server is disabled, including direct invocation.
    (void)__this;
    (void)method;
}''',
    ),
    (
        "Update_m9683ECF644857820E3A0A23AFFA90EEC3C4902E7",
        "2977548ad68482cfb593796d0a9370330e446ea2e98bd248d48b638687cc3330",
        '''{
    (void)method;
    static bool s_Il2CppMethodInitialized;
    if (!s_Il2CppMethodInitialized)
    {
        il2cpp_codegen_initialize_runtime_metadata((uintptr_t*)&Object_tC12DECB6760A7F2CBF65D9DCF18D044C2D97152C_il2cpp_TypeInfo_var);
        s_Il2CppMethodInitialized = true;
    }

    // Poll on Unity's thread. Native callbacks never retain managed pointers.
    char display[2048] = {};
    const int32_t length = Week7CopyDisplay(display, static_cast<int32_t>(sizeof(display)));
    if (length <= 0 || length >= static_cast<int32_t>(sizeof(display)))
        return;
    display[length] = '\\0';

    TMP_Text_tE8D677872D43AD4B2AAF0D6101692A17D0B251A9* label = __this->___displayText;
    il2cpp_codegen_runtime_class_init_inline(Object_tC12DECB6760A7F2CBF65D9DCF18D044C2D97152C_il2cpp_TypeInfo_var);
    if (Object_op_Inequality_mD0BE578448EAA61948F25C32F8DD55AB1F778602(label, (Object_tC12DECB6760A7F2CBF65D9DCF18D044C2D97152C*)NULL, NULL))
    {
        String_t* text = il2cpp_codegen_string_new_wrapper(display);
        VirtualActionInvoker1< String_t* >::Invoke(66, label, text);
    }
}''',
    ),
    (
        "OnDestroy_mDE94744C332900B2841E690D87C3CC3D84B44A4A",
        "c062353c6cc35d266dc916767e6aaa1836bfc2afa4d2d444afb6f2d2937702a3",
        '''{
    (void)__this;
    (void)method;
    Week7Stop();
}''',
    ),
)


class PatchError(Exception):
    """The export does not match a reviewed supported state."""


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def render_patch(original):
    """Validate all inputs before returning new bytes; never write here."""
    previous_patch = sha256(original) == PREVIOUS_PATCH_SHA256
    if sha256(original) != ORIGINAL_SHA256 and not previous_patch:
        raise PatchError("Unknown receiver source; expected the verified sanitized import.")
    patched = original
    for name, body_hash, replacement in METHODS:
        if previous_patch:
            old_body = PREVIOUS_START if name.startswith("Start_") else replacement
            body_hash = sha256(old_body.encode("utf-8"))
        signature = (
            "IL2CPP_EXTERN_C IL2CPP_METHOD_ATTR void TlsDataReceiver_"
            + name + " (" + RECEIVER + "* __this, const RuntimeMethod* method) \n"
        ).encode("utf-8")
        if patched.count(signature) != 1:
            raise PatchError("Unknown or ambiguous method signature: " + name)
        body_start = patched.index(signature) + len(signature)
        body_end = patched.find(b"\n// Method Definition Index:", body_start)
        if body_end < 0 or sha256(patched[body_start:body_end]) != body_hash:
            raise PatchError("Unknown generated method body: " + name)
        patched = patched[:body_start] + replacement.encode("utf-8") + patched[body_end:]
    include = b'#include "pch-cpp.hpp"\n'
    if patched.count(include) != 1:
        raise PatchError("Unknown generated include preamble.")
    if previous_patch:
        if patched.count(DECLARATIONS) != 1:
            raise PatchError("Unknown previous bridge declarations.")
        return patched.replace(DECLARATIONS, DECLARATIONS + LAYOUT_DECLARATIONS, 1)
    return patched.replace(include, include + b"\n" + DECLARATIONS + LAYOUT_DECLARATIONS, 1)


def patch_export(export):
    """Apply atomically, preserving file permissions; return whether it changed."""
    source = Path(export) / SOURCE
    original = source.read_bytes()
    if sha256(original) == PATCHED_SHA256:
        return False
    patched = render_patch(original)
    if sha256(patched) != PATCHED_SHA256:
        raise PatchError("Patch implementation differs from its reviewed output hash.")
    mode = stat.S_IMODE(source.stat().st_mode)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".week7-receiver-", dir=source.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(patched)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(mode)
        if source.read_bytes() != original:
            raise PatchError("Receiver source changed during validation; no patch applied.")
        os.replace(temporary, source)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--export", type=Path,
        default=Path(__file__).resolve().parents[1] / "xcode-export",
        help="Unity Xcode export directory (default: ../xcode-export relative to this script)",
    )
    args = parser.parse_args(argv)
    try:
        changed = patch_export(args.export)
    except (OSError, PatchError) as error:
        print("EXPORT_PATCH_FAILED: " + str(error), file=sys.stderr)
        return 1
    print("EXPORT_PATCH_OK: " + ("applied native receiver hooks" if changed else "already applied"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
