"""Exercise the guarded export patch and execute its generated C++ bridge hooks."""
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys
import plistlib

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "ios-visualizer/tools/patch_export.py"
CONFIGURE = ROOT / "ios-visualizer/tools/configure_xcode.py"
SOURCE = Path("Il2CppOutputProject/Source/il2cppOutput/Assembly-CSharp.cpp")
# Immutable sanitized import, retained in Git as provenance after the app changes.
BASELINE_BLOB = "d09f01b2d35b3abfd6ad9b8b79e51b4728e28ade"
BASELINE_SHA256 = "a0a1d09266554b15e8f1fd60677db1cd60ec1b125d8d7108f111e0a25fe2a92c"


@pytest.fixture(scope="module")
def baseline():
    data = (ROOT / "ios-visualizer/xcode-export" / SOURCE).read_bytes()
    if hashlib.sha256(data).hexdigest() != BASELINE_SHA256:
        result = subprocess.run(
            ["git", "cat-file", "blob", BASELINE_BLOB], cwd=ROOT,
            capture_output=True, check=True,
        )
        data = result.stdout
    assert hashlib.sha256(data).hexdigest() == BASELINE_SHA256
    return data


def run_patch(export, script=SCRIPT, use_default=False):
    command = [sys.executable, str(script)]
    if not use_default:
        command.extend(["--export", str(export)])
    return subprocess.run(command, capture_output=True, text=True, check=False)


def create_export(tmp_path, baseline):
    export = tmp_path / "xcode-export"
    source = export / SOURCE
    source.parent.mkdir(parents=True)
    source.write_bytes(baseline)
    source.chmod(0o640)
    (export / "scene-untouched.bin").write_bytes(b"keep the scene and metadata")
    return export, source


def test_apply_changes_only_receiver_source_and_preserves_file_mode(tmp_path, baseline):
    export, source = create_export(tmp_path, baseline)
    initial_mode = source.stat().st_mode & 0o777
    result = run_patch(export)
    assert result.returncode == 0, result.stderr
    assert source.read_bytes() != baseline
    assert source.stat().st_mode & 0o777 == initial_mode
    assert (export / "scene-untouched.bin").read_bytes() == b"keep the scene and metadata"
    assert sorted(p.relative_to(export) for p in export.rglob("*") if p.is_file()) == sorted(
        [SOURCE, Path("scene-untouched.bin")]
    )


def test_reapply_keeps_content_and_modification_time(tmp_path, baseline):
    export, source = create_export(tmp_path, baseline)
    first = run_patch(export)
    assert first.returncode == 0, first.stderr
    content, modified = source.read_bytes(), source.stat().st_mtime_ns
    second = run_patch(export)
    assert second.returncode == 0, second.stderr
    assert "already applied" in second.stdout.lower()
    assert source.read_bytes() == content
    assert source.stat().st_mtime_ns == modified


@pytest.mark.parametrize("mutation", ["elsewhere", "signature", "body"])
def test_unknown_original_is_rejected_without_modification(tmp_path, baseline, mutation):
    export, source = create_export(tmp_path, baseline)
    if mutation == "elsewhere":
        unknown = baseline + b"\n// a different Unity export\n"
    elif mutation == "signature":
        unknown = baseline.replace(b"TlsDataReceiver_Start_m7C5A4", b"TlsDataReceiver_Start_m8C5A4", 1)
    else:
        unknown = baseline.replace(b"__this->___isRunning = (bool)1;", b"__this->___isRunning = (bool)0;", 1)
    assert unknown != baseline
    source.write_bytes(unknown)
    result = run_patch(export)
    assert result.returncode != 0
    assert "unknown" in result.stderr.lower()
    assert source.read_bytes() == unknown


def test_modified_patch_is_rejected_without_overwriting_user_edit(tmp_path, baseline):
    export, source = create_export(tmp_path, baseline)
    applied = run_patch(export)
    assert applied.returncode == 0, applied.stderr
    tampered = source.read_bytes().replace(b"char display[2048]", b"char display[4096]", 1)
    assert tampered != source.read_bytes()
    source.write_bytes(tampered)
    rejected = run_patch(export)
    assert rejected.returncode != 0
    assert "unknown" in rejected.stderr.lower()
    assert source.read_bytes() == tampered


def test_missing_export_reports_failure_without_creating_files(tmp_path):
    export = tmp_path / "missing"
    result = run_patch(export)
    assert result.returncode != 0
    assert not export.exists()
    assert "Traceback" not in result.stderr


def test_default_export_is_resolved_relative_to_script(tmp_path, baseline):
    export, source = create_export(tmp_path, baseline)
    tools = tmp_path / "tools"
    tools.mkdir()
    copied_script = tools / "patch_export.py"
    shutil.copyfile(SCRIPT, copied_script)
    result = run_patch(export, copied_script, use_default=True)
    assert result.returncode == 0, result.stderr
    assert source.read_bytes() != baseline


def test_upgrades_previous_reviewed_patch_without_restoring_export(tmp_path, baseline):
    export, source = create_export(tmp_path, baseline)
    assert run_patch(export).returncode == 0
    current = source.read_bytes()
    old = re.sub(
        rb'// Week 7 display layout declarations\.\n.*?// End Week 7 display layout declarations\.\n',
        b'', current, flags=re.S,
    )
    signature = rb'(IL2CPP_EXTERN_C IL2CPP_METHOD_ATTR void TlsDataReceiver_Start_m7C5A4A901498D34F398FC637D16CEA685691AE89 \([^\n]+\) \n)'
    old = re.sub(signature + rb'.*?(?=\n// Method Definition Index:)', lambda m: m.group(1) + b'''{
    (void)__this;
    (void)method;
    Week7Start();
}''', old, count=1, flags=re.S)
    assert hashlib.sha256(old).hexdigest() == 'da960b5edf4168811b67fd1d5c7784f6fc76637bd46e398525f69b2451d153ca'
    source.write_bytes(old)
    result = run_patch(export)
    assert result.returncode == 0, result.stderr
    assert source.read_bytes() == current


def configuration_export(tmp_path):
    export = tmp_path / 'xcode-export'
    blobs = {
        'Unity-iPhone.xcodeproj/project.pbxproj': '61ff1fb1e6a8ed553b9425eb7deb5bfcc96c485a',
        'Info.plist': '4895eefe19c58d8a23355a499f4e590759c5ba6a',
        'process_symbols.sh': '64e526b1412a23e87b7c7b53bc53049a09073e68',
    }
    for name, blob in blobs.items():
        data = subprocess.run(['git', 'cat-file', 'blob', blob], cwd=ROOT, capture_output=True, check=True).stdout
        if name.endswith('pbxproj'):
            # Never write inherited service credentials into the test workspace.
            data = re.sub(rb'USYM_UPLOAD_AUTH_TOKEN = [^;]*;', b'USYM_UPLOAD_AUTH_TOKEN = "fixture-token";', data)
        path = export / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (export / 'process_symbols.sh').chmod(0o755)
    return export


def test_configure_first_apply_and_reapply_preserve_valid_complete_linkage(tmp_path):
    export = configuration_export(tmp_path)
    symbols = export / 'process_symbols.sh'
    initial_symbols_mode = symbols.stat().st_mode & 0o777
    result = run_patch(export, CONFIGURE)
    assert result.returncode == 0, result.stderr
    files = [p for p in export.rglob('*') if p.is_file()]
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in files}
    assert b'fixture-token' not in (export / 'Unity-iPhone.xcodeproj/project.pbxproj').read_bytes()
    assert plistlib.loads((export / 'Info.plist').read_bytes())['ITSAppUsesNonExemptEncryption'] is True
    second = run_patch(export, CONFIGURE)
    assert second.returncode == 0, second.stderr
    assert {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in files} == before
    assert symbols.stat().st_mode & 0o777 == initial_symbols_mode


@pytest.mark.parametrize('broken_edge', ['framework', 'target', 'project', 'product', 'local-path', 'symbols'])
def test_configure_rejects_partial_integration_before_any_write(tmp_path, broken_edge):
    export = configuration_export(tmp_path)
    assert run_patch(export, CONFIGURE).returncode == 0
    project = export / 'Unity-iPhone.xcodeproj/project.pbxproj'
    text = project.read_text()
    mutations = {
        'framework': ('\t\t\t\tA7E700000000000000000001 /* Week7Native in Frameworks */,\n', ''),
        'target': ('packageProductDependencies = (A7E700000000000000000003 /* Week7Native */, );', 'packageProductDependencies = ();'),
        'project': ('packageReferences = (A7E700000000000000000002 /* XCLocalSwiftPackageReference "../Week7Native" */, );', 'packageReferences = ();'),
        'product': ('productName = Week7Native;', 'productName = DifferentProduct;'),
        'local-path': ('relativePath = ../Week7Native;', 'relativePath = ../DifferentPackage;'),
    }
    if broken_edge == 'symbols':
        symbols = export / 'process_symbols.sh'
        symbols.write_text(symbols.read_text().replace('    exit 0\nfi', '    :\nfi', 1))
    else:
        old, new = mutations[broken_edge]
        assert text.count(old) == 1
        project.write_text(text.replace(old, new, 1))
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in export.rglob('*') if p.is_file()}
    result = run_patch(export, CONFIGURE)
    assert result.returncode != 0
    assert {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before} == before
    assert 'Traceback' not in result.stderr


def test_configure_rejects_bad_plist_without_partial_project_changes(tmp_path):
    export = configuration_export(tmp_path)
    (export / 'Info.plist').write_bytes(b'not a plist')
    before = {p: p.read_bytes() for p in export.rglob('*') if p.is_file()}
    result = run_patch(export, CONFIGURE)
    assert result.returncode != 0
    assert {p: p.read_bytes() for p in before} == before
    assert 'Traceback' not in result.stderr


def test_compiled_receiver_hooks_poll_bounded_native_snapshots(tmp_path, baseline):
    compiler = shutil.which("clang++") or shutil.which("g++")
    if compiler is None:
        pytest.skip("A C++ compiler is required to execute the generated receiver hooks")
    export, source = create_export(tmp_path, baseline)
    applied = run_patch(export)
    assert applied.returncode == 0, applied.stderr
    patched = source.read_text(encoding="utf-8-sig")
    hooks, names = [], {}
    for lifecycle in ["Start", "ListenLoop", "Update", "OnDestroy"]:
        match = re.search(
            r"IL2CPP_EXTERN_C IL2CPP_METHOD_ATTR void (TlsDataReceiver_" + lifecycle
            + r"_m[A-F0-9]+) \([^\n]+\) \n", patched,
        )
        assert match is not None
        end = patched.index("\n// Method Definition Index:", match.end())
        hooks.append(patched[match.start():end])
        names[lifecycle] = match.group(1)
    harness = r'''
#include <cassert>
#include <cstdint>
#include <cstring>
#include <string>
#define IL2CPP_EXTERN_C extern "C"
#define IL2CPP_METHOD_ATTR
struct RuntimeMethod {};
struct RuntimeClass {};
using String_t = std::string;
struct Object_tC12DECB6760A7F2CBF65D9DCF18D044C2D97152C {};
struct Vector2_t1FD6F485C871E832B347AB2DC8CBA08B739D8DF7 { float ___x = 0, ___y = 0; };
struct RectTransform_t6C5DA5E41A89E0F488B001E45E58963480E543A5 {
    Vector2_t1FD6F485C871E832B347AB2DC8CBA08B739D8DF7 anchorMin, anchorMax, offsetMin, offsetMax;
};
struct TMP_Text_tE8D677872D43AD4B2AAF0D6101692A17D0B251A9
    : Object_tC12DECB6760A7F2CBF65D9DCF18D044C2D97152C {
    std::string text; int writes = 0;
    RectTransform_t6C5DA5E41A89E0F488B001E45E58963480E543A5 rect;
    float size = 45, minSize = 18, maxSize = 72; bool autoSize = false;
};
struct TlsDataReceiver_t47A6D7DD24307D9353B230F8ADB4F931DBCB4C6E {
    TMP_Text_tE8D677872D43AD4B2AAF0D6101692A17D0B251A9* ___displayText;
};
RuntimeClass* Object_tC12DECB6760A7F2CBF65D9DCF18D044C2D97152C_il2cpp_TypeInfo_var;
void il2cpp_codegen_initialize_runtime_metadata(uintptr_t*) {}
void il2cpp_codegen_runtime_class_init_inline(RuntimeClass*) {}
bool Object_op_Inequality_mD0BE578448EAA61948F25C32F8DD55AB1F778602(
    Object_tC12DECB6760A7F2CBF65D9DCF18D044C2D97152C* a,
    Object_tC12DECB6760A7F2CBF65D9DCF18D044C2D97152C* b, const RuntimeMethod*) { return a != b; }
RectTransform_t6C5DA5E41A89E0F488B001E45E58963480E543A5* TMP_Text_get_rectTransform_m22DC10116809BEB2C66047A55337A588ED023EBF(
    TMP_Text_tE8D677872D43AD4B2AAF0D6101692A17D0B251A9* label, const RuntimeMethod*) { return &label->rect; }
#define RECT_SETTER(name, property) \
    void name(RectTransform_t6C5DA5E41A89E0F488B001E45E58963480E543A5* rect, \
        Vector2_t1FD6F485C871E832B347AB2DC8CBA08B739D8DF7 value, const RuntimeMethod*) { rect->property = value; }
RECT_SETTER(RectTransform_set_anchorMin_m931442ABE3368D6D4309F43DF1D64AB64B0F52E3, anchorMin)
RECT_SETTER(RectTransform_set_anchorMax_m52829ABEDD229ABD3DA20BCA676FA1DCA4A39B7D, anchorMax)
RECT_SETTER(RectTransform_set_offsetMin_m07F38B4105C7CA9CC9FBDC9ED0DB008602880AB9, offsetMin)
RECT_SETTER(RectTransform_set_offsetMax_m5514D09D86516F2C0E25FA6D11A3A4274D3D002D, offsetMax)
#define FONT_SETTER(name, property, type) \
    void name(TMP_Text_tE8D677872D43AD4B2AAF0D6101692A17D0B251A9* label, type value, const RuntimeMethod*) { label->property = value; }
FONT_SETTER(TMP_Text_set_fontSize_m1C3A3BA2BC88E5E1D89375FD35A0AA91E75D3AAD, size, float)
FONT_SETTER(TMP_Text_set_fontSizeMin_mEAF970BB9CA053DF953AF83E638EA0F1D885358F, minSize, float)
FONT_SETTER(TMP_Text_set_fontSizeMax_mC84B7090F5CE69BA63556A71FD63ABD67C911750, maxSize, float)
FONT_SETTER(TMP_Text_set_enableAutoSizing_mDD34BC7AA735EEBEB916FF5C9791B1502F65FBCA, autoSize, bool)
String_t* il2cpp_codegen_string_new_wrapper(const char* input) {
    static String_t text; text = input; return &text;
}
template<typename T> struct VirtualActionInvoker1 {
    static void Invoke(int slot, TMP_Text_tE8D677872D43AD4B2AAF0D6101692A17D0B251A9* target, T value) {
        assert(slot == 66); assert(target); target->text = *value; ++target->writes;
    }
};
int starts = 0, stops = 0, polls = 0, nextLength = 0;
extern "C" void Week7Start(void) { ++starts; }
extern "C" void Week7Stop(void) { ++stops; }
extern "C" int32_t Week7CopyDisplay(char* buffer, int32_t capacity) {
    ++polls; assert(capacity == 2048);
    if (nextLength > 0 && nextLength < capacity) {
        std::memset(buffer, 'x', static_cast<size_t>(nextLength));
        if (nextLength == 4) std::memcpy(buffer, "OPEN", 4);
    }
    return nextLength;
}
'''
    harness += "\n".join(hooks)
    harness += r'''
int main() {
    TMP_Text_tE8D677872D43AD4B2AAF0D6101692A17D0B251A9 label;
    TlsDataReceiver_t47A6D7DD24307D9353B230F8ADB4F931DBCB4C6E receiver{&label};
    START(&receiver, nullptr);
    assert(starts == 1);
    const auto& rect = label.rect;
    const float width = (rect.anchorMax.___x - rect.anchorMin.___x) * 1280 + rect.offsetMax.___x - rect.offsetMin.___x;
    const float height = (rect.anchorMax.___y - rect.anchorMin.___y) * 720 + rect.offsetMax.___y - rect.offsetMin.___y;
    assert(width > 1151 && width < 1153 && height > 503 && height < 505);
    assert(rect.anchorMin.___x > 0 && rect.anchorMin.___y > 0 && rect.anchorMax.___x < 1 && rect.anchorMax.___y <= 0.8f);
    assert(label.autoSize && label.minSize == 18 && label.maxSize == 36 && label.size == 36);
    LISTEN(&receiver, nullptr); // A dormant legacy entry point cannot open a server.
    assert(starts == 1 && polls == 0);
    UPDATE(&receiver, nullptr);
    assert(label.writes == 0);
    nextLength = 4;
    UPDATE(&receiver, nullptr);
    assert(label.writes == 1 && label.text == "OPEN");
    nextLength = 0;
    UPDATE(&receiver, nullptr);
    assert(label.writes == 1 && label.text == "OPEN");
    nextLength = -1;
    UPDATE(&receiver, nullptr);
    nextLength = 2048;
    UPDATE(&receiver, nullptr);
    nextLength = 3000;
    UPDATE(&receiver, nullptr);
    assert(label.writes == 1);
    nextLength = 2047;
    UPDATE(&receiver, nullptr);
    assert(label.writes == 2 && label.text.size() == 2047);
    receiver.___displayText = nullptr;
    nextLength = 4;
    UPDATE(&receiver, nullptr);
    assert(label.writes == 2);
    STOP(&receiver, nullptr);
    assert(stops == 1);
}
'''
    for placeholder, lifecycle in [("START", "Start"), ("LISTEN", "ListenLoop"), ("UPDATE", "Update"), ("STOP", "OnDestroy")]:
        harness = harness.replace(placeholder + "(", names[lifecycle] + "(")
    cpp = tmp_path / "receiver.cpp"
    cpp.write_text(harness)
    executable = tmp_path / "receiver-hooks"
    built = subprocess.run(
        [compiler, "-std=c++11", "-Wall", "-Wextra", "-Werror", str(cpp), "-o", str(executable)],
        capture_output=True, text=True, check=False,
    )
    assert built.returncode == 0, built.stderr
    executed = subprocess.run([str(executable)], capture_output=True, text=True, check=False)
    assert executed.returncode == 0, executed.stderr
