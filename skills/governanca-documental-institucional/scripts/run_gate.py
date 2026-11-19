#!/usr/bin/env python3
"""Orquestra gate OOXML PARCIAL sobre um DOCX final com trilha local sequencial.

Não autoriza sozinho a liberação institucional. Cada execução gera novos arquivos
em uma pasta de saída que não pode existir anteriormente.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
AUDIT = HERE / 'audit_docx.py'
VERIFY = HERE / 'verify_gate_evidence.py'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')


def environment(docx):
    return {
        'python': platform.python_version(),
        'docx_exists': docx.is_file(),
        'docx_readable': docx.is_file() and docx.stat().st_size > 0,
        'auditor_accessible': AUDIT.is_file(),
        'verifier_accessible': VERIFY.is_file(),
        'renderer_libreoffice_available': bool(shutil.which('libreoffice') or shutil.which('soffice')),
        'word_web_tested': False,
        'note': 'LibreOffice disponível não significa inspeção visual realizada; Word para Web depende de teste externo.'
    }


def run(docx, output_dir, profile='institutional-v3.5', cover=True, bookmark_pages=None, exception_reason=None):
    if output_dir.exists():
        raise FileExistsError('A pasta de saída deve ser nova; não sobrescrever evidências: ' + str(output_dir))
    output_dir.mkdir(parents=True, exist_ok=False)
    record = {
        'schema': 'gd-gate-execution-1.0',
        'gate_scope': 'auditoria estrutural e tipográfica PARCIAL; não é aprovação institucional',
        'docx': str(docx),
        'profile': profile,
        'cover_required': cover,
        'cover_exception_reason': exception_reason,
        'environment': environment(docx),
        'started_utc': utc(),
        'events': [],
        'structural_gate': 'not_verifiable',
        'semantic_gate': 'not_evaluated',
        'visual_gate': 'not_evaluated',
        'institutional_release': 'not_authorized',
        'limitations': [
            'Timestamp e ordem são registrados pelo processo local; não são log autenticado do host',
            'Não substitui inspeção visual, gate semântico nem avaliação institucional',
            'Não comprova interoperabilidade no Word para Web'
        ]
    }
    start = time.monotonic_ns()
    def event(phase, **details):
        record['events'].append({'order': len(record['events']) + 1,
                                 'phase': phase, 'at_utc': utc(),
                                 'elapsed_monotonic_ms': (time.monotonic_ns()-start)//1_000_000,
                                 **details})

    def finish():
        record['ended_utc'] = utc()
        (output_dir/'execution.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        return record

    if not docx.is_file():
        event('preflight_failed', reason='DOCX ausente')
        return finish()
    if not AUDIT.is_file() or not VERIFY.is_file():
        event('preflight_failed', reason='Ferramentas de auditoria indisponíveis')
        return finish()
    try:
        initial = sha(docx)
    except OSError as exc:
        event('preflight_failed', reason=str(exc))
        return finish()
    record['artifact_sha256_before'] = initial
    record['auditor_sha256'] = sha(AUDIT)
    record['verifier_sha256'] = sha(VERIFY)
    event('document_frozen', sha256=initial)
    cmd = [sys.executable, str(AUDIT), str(docx), '--profile', profile,
           '--report', str(output_dir/'audit.json'), '--json']
    if cover:
        cmd.append('--check-cover-identification')
    if bookmark_pages is not None:
        cmd.extend(['--bookmark-pages', str(bookmark_pages)])
    event('audit_started', argv=cmd)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    (output_dir/'audit.stderr.txt').write_text(proc.stderr, encoding='utf-8')
    event('audit_finished', returncode=proc.returncode,
          report_created=(output_dir/'audit.json').is_file())
    if proc.returncode not in (0, 1) or not (output_dir/'audit.json').is_file():
        record['failure'] = 'Auditoria não executável ou sem relatório'
        return finish()
    if proc.returncode == 1:
        record['structural_gate'] = 'blocked'
        record['failure'] = 'Auditor identificou problemas bloqueantes'
        return finish()
    event('audit_report_persisted', audit_sha256=sha(output_dir/'audit.json'))
    vcmd = [sys.executable, str(VERIFY), str(docx), str(output_dir/'audit.json'),
            '--expected-profile', profile]
    if cover:
        vcmd.append('--require-cover-roles')
    event('verification_started', argv=vcmd)
    verified = subprocess.run(vcmd, capture_output=True, text=True)
    (output_dir/'verify.stderr.txt').write_text(verified.stderr, encoding='utf-8')
    if verified.stdout.strip():
        try:
            raw = json.loads(verified.stdout)
        except ValueError:
            raw = {'ok': False, 'parse_error': 'Saída do verificador não é JSON'}
        (output_dir/'verification.json').write_text(json.dumps(raw, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    event('verification_finished', returncode=verified.returncode,
          rechecked=(output_dir/'verification.json').is_file())
    final_sha = sha(docx)
    record['artifact_sha256_after'] = final_sha
    event('document_hash_reconfirmed', sha256=final_sha, unchanged=final_sha==initial)
    if verified.returncode == 0 and final_sha == initial:
        record['structural_gate'] = 'passed_partial_scope' if cover else 'pending_cover_exception_review'
    else:
        record['structural_gate'] = 'blocked' if verified.returncode == 1 or final_sha != initial else 'not_verifiable'
        record['failure'] = 'Verificador reprovou, não executou ou DOCX mudou durante a auditoria'
    return finish()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('docx', type=Path)
    ap.add_argument('--output-dir', type=Path)
    ap.add_argument('--profile', default='institutional-v3.5',
                    choices=['none', 'institutional-v3.4', 'institutional-v3.5'])
    ap.add_argument('--no-standard-cover', action='store_true',
                    help='Uso excepcional: não valida capa e exige decisão manual separada; NÃO libera gate completo')
    ap.add_argument('--cover-exception-reason', type=str,
                    help='Justificativa obrigatória quando --no-standard-cover; não implica aprovação')
    ap.add_argument('--bookmark-pages', type=Path, help='Mapa externo verificado; não inferir páginas')
    ap.add_argument('--diagnose', action='store_true', help='Apenas diagnostica capacidades, sem declarar gate aprovado')
    args = ap.parse_args()
    if args.diagnose:
        print(json.dumps(environment(args.docx), ensure_ascii=False, indent=2))
        return 0
    if not args.output_dir:
        ap.error('--output-dir é obrigatório fora de --diagnose')
    if args.no_standard_cover and not (args.cover_exception_reason or '').strip():
        ap.error('--no-standard-cover exige --cover-exception-reason')
    if not args.no_standard_cover and args.cover_exception_reason:
        ap.error('--cover-exception-reason exige --no-standard-cover')
    try:
        result = run(args.docx, args.output_dir, args.profile,
                     not args.no_standard_cover, args.bookmark_pages,
                     args.cover_exception_reason)
    except (OSError, ValueError) as exc:
        print('ERRO:', exc, file=sys.stderr)
        return 2
    print(json.dumps({'structural_gate': result['structural_gate'],
                      'institutional_release': result['institutional_release'],
                      'artifact_sha256': result.get('artifact_sha256_after', result.get('artifact_sha256_before')),
                      'execution_record': str(args.output_dir/'execution.json'),
                      'errors': result.get('failure')}, ensure_ascii=False, indent=2))
    if args.no_standard_cover:
        # O gate não pode ser considerado completo sob exceção não verificada.
        return 1
    return 0 if result['structural_gate'] == 'passed_partial_scope' else 1


if __name__ == '__main__':
    sys.exit(main())
