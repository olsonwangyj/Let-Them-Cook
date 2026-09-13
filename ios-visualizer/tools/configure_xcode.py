#!/usr/bin/env python3
"""Wire the local native Swift package into this inspected Unity export.

Does not regenerate the import manifest or select a signing team. Reapplying is
idempotent. The original export remains the provenance source in Git history.
"""
from pathlib import Path
import argparse
import plistlib
import re
import os
import stat
import sys
import tempfile


def _without_comments(text):
    return re.sub(r'/\*.*?\*/', '', text, flags=re.S)


def _object(text, identifier):
    """Read one pinned PBX object, respecting quoted strings and nested braces."""
    # TargetAttributes also uses target IDs as dictionary keys; only the actual
    # PBX object has an isa field immediately after its opening brace.
    matches = list(re.finditer(r'^\s*' + identifier + r'\s*(?:/\*[^\n]*?\*/\s*)?=\s*\{(?=\s*isa\s*=)', text, re.M))
    if len(matches) != 1:
        raise ValueError('Unknown or duplicate Xcode object: ' + identifier)
    start = matches[0].end()
    depth, quoted, escaped = 1, False, False
    for position in range(start, len(text)):
        character = text[position]
        if quoted:
            if escaped:
                escaped = False
            elif character == '\\':
                escaped = True
            elif character == '"':
                quoted = False
        elif character == '"':
            quoted = True
        elif character == '{':
            depth += 1
        elif character == '}':
            depth -= 1
            if depth == 0:
                return _without_comments(text[start:position])
    raise ValueError('Incomplete Xcode object: ' + identifier)


def _scalar(body, field, expected):
    values = re.findall(r'\b' + field + r'\s*=\s*([^;]*);', body)
    if len(values) != 1 or values[0].strip().strip('"') != expected:
        raise ValueError('Unknown Xcode integration value: ' + field)


def _list_reference(body, field, identifier):
    values = re.findall(r'\b' + field + r'\s*=\s*\((.*?)\);', body, flags=re.S)
    if len(values) != 1 or re.findall(r'\b[A-F0-9]{24}\b', values[0]).count(identifier) != 1:
        raise ValueError('Incomplete Xcode integration reference: ' + field)


def validate_linkage(text):
    """Verify every edge from the active project/target through the local product."""
    project = _object(text, '29B97313FDCFA39411CA2CEA')
    target = _object(text, '9D25AB9C213FB47800354C27')
    framework = _object(text, '9D25AB99213FB47800354C27')
    build = _object(text, 'A7E700000000000000000001')
    local = _object(text, 'A7E700000000000000000002')
    product = _object(text, 'A7E700000000000000000003')
    _scalar(_without_comments(text), 'rootObject', '29B97313FDCFA39411CA2CEA')
    _scalar(project, 'isa', 'PBXProject')
    _list_reference(project, 'targets', '9D25AB9C213FB47800354C27')
    _list_reference(project, 'packageReferences', 'A7E700000000000000000002')
    _scalar(target, 'isa', 'PBXNativeTarget')
    _scalar(target, 'name', 'UnityFramework')
    _list_reference(target, 'buildPhases', '9D25AB99213FB47800354C27')
    _list_reference(target, 'packageProductDependencies', 'A7E700000000000000000003')
    _scalar(framework, 'isa', 'PBXFrameworksBuildPhase')
    _list_reference(framework, 'files', 'A7E700000000000000000001')
    _scalar(build, 'isa', 'PBXBuildFile')
    _scalar(build, 'productRef', 'A7E700000000000000000003')
    _scalar(local, 'isa', 'XCLocalSwiftPackageReference')
    _scalar(local, 'relativePath', '../Week7Native')
    _scalar(product, 'isa', 'XCSwiftPackageProductDependency')
    _scalar(product, 'productName', 'Week7Native')


def _replace_files(prepared):
    """Stage all validated changes before replacing files; retain executable bits."""
    staged = []
    try:
        for path, before, after in prepared:
            if before == after:
                continue
            with tempfile.NamedTemporaryFile(prefix='.week7-configure-', dir=path.parent, delete=False) as stream:
                temporary = Path(stream.name)
                staged.append((path, temporary))
                stream.write(after)
                stream.flush()
                os.fsync(stream.fileno())
            temporary.chmod(stat.S_IMODE(path.stat().st_mode))
        if any(path.read_bytes() != before for path, before, _ in prepared):
            raise ValueError('Xcode export changed during validation; configuration was not applied')
        for path, temporary in staged:
            os.replace(temporary, path)
    finally:
        for _, temporary in staged:
            temporary.unlink(missing_ok=True)


def configure(export):
    project = export / 'Unity-iPhone.xcodeproj/project.pbxproj'
    symbols = export / 'process_symbols.sh'
    info = export / 'Info.plist'
    project_before, symbols_before, info_before = (path.read_bytes() for path in (project, symbols, info))
    text = project_before.decode('utf-8')
    # Export contains Unity service tokens and target-level teammate signing
    # attributes in addition to the already-cleared build settings.
    text = re.sub(r'USYM_UPLOAD_AUTH_TOKEN = [^;]*;', 'USYM_UPLOAD_AUTH_TOKEN = "";', text)
    text = re.sub(r'DevelopmentTeam = [^;]*;', 'DevelopmentTeam = "";', text)
    if 'Week7Native' not in text and 'A7E70000000000000000000' not in text:
        def replace_once(old, new):
            nonlocal text
            if text.count(old) != 1:
                raise ValueError('Unexpected Xcode export anchor; inspect before adapting')
            text = text.replace(old, new, 1)
        replace_once('/* End PBXBuildFile section */',
            '\t\tA7E700000000000000000001 /* Week7Native in Frameworks */ = {isa = PBXBuildFile; productRef = A7E700000000000000000003 /* Week7Native */; };\n/* End PBXBuildFile section */')
        anchor = '\t\t\t\t00000000008063A1000160D3 /* UnityRuntime.framework in Frameworks */,'
        replace_once(anchor, '\t\t\t\tA7E700000000000000000001 /* Week7Native in Frameworks */,\n' + anchor)
        replace_once('\t\t\tname = UnityFramework;\n\t\t\tproductName = UnityFramework;',
            '\t\t\tname = UnityFramework;\n\t\t\tpackageProductDependencies = (A7E700000000000000000003 /* Week7Native */, );\n\t\t\tproductName = UnityFramework;')
        replace_once('\t\t\tprojectDirPath = "";', '\t\t\tpackageReferences = (A7E700000000000000000002 /* XCLocalSwiftPackageReference "../Week7Native" */, );\n\t\t\tprojectDirPath = "";')
        replace_once('/* End PBXProject section */', '''/* End PBXProject section */

/* Begin XCLocalSwiftPackageReference section */
        A7E700000000000000000002 /* XCLocalSwiftPackageReference "../Week7Native" */ = {
            isa = XCLocalSwiftPackageReference;
            relativePath = ../Week7Native;
        };
/* End XCLocalSwiftPackageReference section */

/* Begin XCSwiftPackageProductDependency section */
        A7E700000000000000000003 /* Week7Native */ = {
            isa = XCSwiftPackageProductDependency;
            productName = Week7Native;
        };
/* End XCSwiftPackageProductDependency section */''')
    validate_linkage(text)
    script = symbols_before.decode('utf-8')
    if 'WEEK7_ALLOW_SYMBOL_UPLOAD' not in script:
        if not script.startswith('#!/bin/sh\n'):
            raise ValueError('Unknown symbol-upload script preamble')
        script = script.replace('#!/bin/sh', '#!/bin/sh\n\n# Local builds do not upload to an inherited Unity account.\nif [ "${WEEK7_ALLOW_SYMBOL_UPLOAD:-NO}" != "YES" ]; then\n    exit 0\nfi', 1)
    if not re.match(r'\A#!/bin/sh\n(?:\n|#[^\n]*\n)*if \[ "\$\{WEEK7_ALLOW_SYMBOL_UPLOAD:-NO\}" != "YES" \]; then\n[ \t]+exit 0\nfi\n', script):
        raise ValueError('Unknown or incomplete symbol-upload guard')
    data = plistlib.loads(info_before)
    if not isinstance(data, dict) or not {'arm64', 'metal', 'arkit'}.issubset(data.get('UIRequiredDeviceCapabilities', [])):
        raise ValueError('Unknown Unity app Info.plist')
    data['CFBundleDisplayName'] = 'Week 7 Visualizer'
    data['CFBundleVersion'] = '1'
    data['NSLocalNetworkUsageDescription'] = 'Connect to the Week 7 board using this iPhone’s own verified SSH and TLS connection.'
    # NIOSSH/NIOSSL contain non-Apple cryptography. This is a declaration, not an
    # export-compliance determination; distribution remains a separate action.
    data['ITSAppUsesNonExemptEncryption'] = True
    _replace_files([
        (project, project_before, text.encode('utf-8')),
        (symbols, symbols_before, script.encode('utf-8')),
        (info, info_before, plistlib.dumps(data, sort_keys=False)),
    ])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', type=Path, default=Path(__file__).resolve().parents[1] / 'xcode-export')
    args = parser.parse_args()
    try:
        configure(args.export)
    except (OSError, ValueError, plistlib.InvalidFileException) as error:
        print('XCODE_CONFIGURE_FAILED: ' + str(error), file=sys.stderr)
        sys.exit(1)
    print('Configured local Week7Native package; signing stays operator-owned.')
