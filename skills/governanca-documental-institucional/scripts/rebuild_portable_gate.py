#!/usr/bin/env python3
"""Manutenção determinística do payload incorporado ao gate portátil (somente build).

--check valida equivalência dos três scripts oficiais com o payload recuperável.
--write regenera o payload e o hash do recurso no manifesto, sem alterar normas.
"""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile

SCRIPTS=Path(__file__).resolve().parent
SKILL=SCRIPTS.parent
NAMES=('audit_docx.py','verify_gate_evidence.py','run_gate.py')
BOOT=SCRIPTS/'portable_gate.py'
MANIFEST=SKILL/'manifest.json'
FRAGMENT=re.compile(r"^CORE_SHA256 = [^\n]+\n^ZIP_SHA256 = [^\n]+\n^PAYLOAD_B85 = \(\n.*?^\)$",re.M|re.S)


def build_parts():
    scripts={name:(SCRIPTS/name).read_bytes() for name in NAMES}
    sha={name:hashlib.sha256(raw).hexdigest() for name,raw in scripts.items()}
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,raw in scripts.items():
            info=zipfile.ZipInfo(name,date_time=(2026,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o600<<16
            z.writestr(info,raw,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    raw=stream.getvalue()
    chars=base64.b85encode(raw).decode('ascii')
    body='\n'.join('    '+repr(chars[i:i+120]) for i in range(0,len(chars),120))
    fragment=f'CORE_SHA256 = {repr(sha)}\nZIP_SHA256 = {repr(hashlib.sha256(raw).hexdigest())}\nPAYLOAD_B85 = (\n{body}\n)'
    return fragment, sha, hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check',action='store_true')
    mode.add_argument('--write',action='store_true')
    args=parser.parse_args()
    current=BOOT.read_text(encoding='utf-8')
    parts=list(FRAGMENT.finditer(current))
    if len(parts)!=1:
        raise ValueError('O bootstrap deve conter um único bloco de payload')
    fragment,sha,zip_sha=build_parts()
    regenerated=current[:parts[0].start()]+fragment+current[parts[0].end():]
    checksum=hashlib.sha256(regenerated.encode('utf-8')).hexdigest()
    m=json.loads(MANIFEST.read_text(encoding='utf-8'))
    runtime=m.get('runtime_bootstrap')
    if not isinstance(runtime,dict):
        raise ValueError('Manifesto sem runtime_bootstrap')
    expected={'path':'scripts/portable_gate.py','sha256':checksum,
              'payload_zip_sha256':zip_sha,'core_files_sha256':sha}
    if args.check:
        if current!=regenerated:
            print('ERRO: payload portátil difere dos scripts distribuídos',file=sys.stderr)
            return 1
        for k,v in expected.items():
            if runtime.get(k)!=v:
                print('ERRO: runtime_bootstrap divergente no manifesto: '+k,file=sys.stderr)
                return 1
        print('OK: payload, script portátil, hashes e manifesto sincronizados')
        return 0
    BOOT.write_text(regenerated,encoding='utf-8')
    m['runtime_bootstrap'].update(expected)
    MANIFEST.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Payload e manifesto regenerados:',checksum)
    return 0

if __name__=='__main__':
    sys.exit(main())
