#!/usr/bin/env python3
"""Revalida evidência JSON contra o DOCX real, sem confiar só em declarações.

Aprovação significa SOMENTE que as verificações estruturais/tipográficas
cobertas foram reexecutadas sobre o arquivo indicado. Não autentica origem
nem anterioridade histórica do relatório e não libera gates humanos.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Optional

from audit_docx import audit

SUPPORTED_PROFILES = ('none', 'institutional-v3.4', 'institutional-v3.5')
COVER_KEYS = ('checked', 'metadata_table_found', 'responsavel_present',
              'autoria_present', 'separate_fields', 'values_present')


def inspect(docx: Path, report: Path, require_cover_roles: bool = False,
            expected_profile: Optional[str] = None):
    """Valida o registro e REAUDITA o DOCX; falha fechado se não houver cobertura."""
    errors = []
    initial_sha = hashlib.sha256(docx.read_bytes()).hexdigest()
    data = json.loads(report.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('Relatório JSON precisa ser um objeto')
    if data.get('artifact_sha256') != initial_sha:
        errors.append('SHA-256 do relatório não corresponde ao DOCX atual')

    profile = data.get('profile')
    if not isinstance(profile, str) or not profile.strip():
        errors.append('Perfil da auditoria ausente')
    elif profile not in SUPPORTED_PROFILES:
        errors.append('Perfil não verificável pelo auditor empacotado: ' + profile)
    if expected_profile is not None and profile != expected_profile:
        errors.append('Perfil declarado difere do perfil exigido: ' + str(expected_profile))
    if not any(isinstance(data.get(k), str) and data[k].strip()
               for k in ('auditor', 'auditor_version')):
        errors.append('Identificador do auditor ausente')
    if not isinstance(data.get('ok'), bool):
        errors.append('Campo ok booleano ausente')
    elif not data['ok']:
        errors.append('Auditoria reportou ok=false; gate não aprovado')
    issues = data.get('issues')
    if not isinstance(issues, list):
        errors.append('Lista issues ausente (normalizar relatório de auditor independente)')
    elif any(not isinstance(i, dict) or not isinstance(i.get('severity'), str)
             for i in issues):
        errors.append('Lista issues deve conter objetos com severity')
    elif any(i['severity'].lower() == 'error' for i in issues):
        errors.append('Auditoria contém erros estruturais reportados')
    limits = data.get('gate_limits') or data.get('limitations')
    if not isinstance(limits, list) or not limits or any(
            not isinstance(v, str) or not v.strip() for v in limits):
        errors.append('Lista de limitações da auditoria ausente ou inválida')
    if require_cover_roles:
        cr = data.get('cover_roles')
        if not isinstance(cr, dict):
            errors.append('Evidência cover_roles ausente')
        elif any(cr.get(k) is not True for k in COVER_KEYS):
            errors.append('Identificação da capa não comprovada pelo relatório')
        elif not isinstance(cr.get('method'), str) or not cr['method'].strip():
            errors.append('Método de verificação de capa ausente')

    # Comparação independente com bytes reais, não apenas hash de um JSON.
    recheck = None
    if isinstance(profile, str) and profile in SUPPORTED_PROFILES:
        target_profile = expected_profile or profile
        try:
            recheck = audit(docx, profile=target_profile,
                            check_cover_identification=require_cover_roles)
            if not recheck['ok']:
                codes = ', '.join(sorted({i['code'] for i in recheck['issues']
                                          if i['severity'] == 'error'}))
                errors.append('Reauditoria do DOCX falhou: ' + codes)
            if require_cover_roles:
                actual = recheck.get('cover_roles')
                if not isinstance(actual, dict) or any(actual.get(k) is not True for k in COVER_KEYS):
                    errors.append('Capa real não satisfaz os papéis exigidos')
                cr = data.get('cover_roles')
                if isinstance(cr, dict) and isinstance(actual, dict):
                    for key in COVER_KEYS:
                        if cr.get(key) != actual.get(key):
                            errors.append('Relatório diverge da reauditoria de capa: ' + key)
            # A ferramenta independente não pode ocultar defeitos detectados
            # pela auditoria empacotada. Ausência de códigos idênticos nos dois
            # auditores não é tratada como equivalência de cobertura.
        except Exception as exc:
            errors.append('Reauditoria indisponível/falhou: ' + type(exc).__name__ + ': ' + str(exc))
    after_sha = hashlib.sha256(docx.read_bytes()).hexdigest()
    if after_sha != initial_sha:
        errors.append('DOCX modificado durante a verificação; reexecutar gate')
    return {
        'ok': not errors,
        'artifact_sha256': after_sha,
        'report_sha256': data.get('artifact_sha256'),
        'report': str(report),
        'profile': profile,
        'expected_profile': expected_profile,
        'issues_reported': len(issues) if isinstance(issues, list) else None,
        'cover_check_required': require_cover_roles,
        'recheck_performed': recheck is not None,
        'recheck_ok': recheck['ok'] if recheck is not None else None,
        'recheck_errors': [i for i in (recheck['issues'] if recheck else [])
                           if i['severity'] == 'error'],
        'recheck_warnings': [i for i in (recheck['issues'] if recheck else [])
                             if i['severity'] == 'warning'],
        'errors': errors,
        'limits': [
            'Verificação independente limitada às regras cobertas por audit_docx.py',
            'Hash e reauditoria não autenticam o histórico nem a anterioridade da auditoria',
            'Não substitui gate de conteúdo, inspeção visual, decisões institucionais e Word para Web'
        ]
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('docx', type=Path)
    ap.add_argument('report', type=Path)
    ap.add_argument('--require-cover-roles', action='store_true')
    ap.add_argument('--expected-profile', choices=SUPPORTED_PROFILES,
                    help='Falha se o perfil declarado não corresponder ao exigido')
    args = ap.parse_args()
    try:
        result = inspect(args.docx, args.report,
                         args.require_cover_roles, args.expected_profile)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print('ERRO:', exc, file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
