"""只读离线语料扫描器；报告不包含路径或导入正文。

用法：python -m life_engine.compat_scan DIRECTORY [--report TEMP_DIRECTORY/report.json]
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import tempfile

from .import_cards import is_link, parse_card
from .import_ir import CharacterImportIR, Classification, ImportFailure


def inventory(root):
    """私有内存清单中的路径仅用于检测重命名及新增文件。"""
    result = {}
    def fail_walk(error):
        raise error
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=fail_walk):
        dirs.sort()
        for name in list(dirs):
            path = Path(directory) / name
            if is_link(path):
                raise ImportFailure('CORPUS_LINK_DIRECTORY', 'inventory', category=Classification.UNSUPPORTED)
        for name in sorted(files):
            path = Path(directory) / name
            if is_link(path) or not path.is_file():
                raise ImportFailure('CORPUS_NONREGULAR_FILE', 'inventory', category=Classification.UNSUPPORTED)
            with path.open('rb') as handle:
                digest = hashlib.file_digest(handle, 'sha256').hexdigest()
            result[str(path.relative_to(root))] = digest
    return result


def diagnostic(code, source_id, severity='warning', stage='normalize', field='$'):
    return {'code': code, 'severity': severity, 'stage': stage, 'source_id': source_id,
            'field': field, 'message': 'See compatibility code and stage; source text is withheld.'}


def scan(root):
    root = Path(root).absolute()
    if not root.is_dir() or any(is_link(p) for p in (root, *root.parents)):
        raise ImportFailure('CORPUS_DIRECTORY_REQUIRED', 'inventory')
    before = inventory(root)
    rows, versions, counts, formats, namespaces, logical = [], Counter(), Counter(), Counter(), set(), Counter()
    embedded = extensions = linked = 0
    for relative, digest in before.items():
        path = root / relative
        fmt = {'.png': 'PNG', '.json': 'JSON'}.get(path.suffix.lower(), 'OTHER')
        formats[fmt] += 1
        source_id = 'CARD-' + digest[:16].upper()
        row = {'source_id': source_id, 'format': fmt, 'spec': 'UNKNOWN',
               'round_trip': 'NOT_RUN', 'diagnostics': []}
        if fmt == 'OTHER':
            category = Classification.UNSUPPORTED
            row['diagnostics'] = [diagnostic('FILE_TYPE_UNSUPPORTED', source_id, 'error', 'discovery')]
        else:
            try:
                ir = parse_card(path)
                row['format'], row['spec'] = ir.source_format, ir.source_spec
                if ir.source_fingerprint != digest:
                    raise ImportFailure('SOURCE_CHANGED_DURING_SCAN', 'read')
                restored = CharacterImportIR.from_json(ir.to_json())
                if restored != ir:
                    raise AssertionError('round-trip contract')
                row['round_trip'] = 'PASS'
                category = Classification.PASS_WITH_WARNINGS if ir.warnings else Classification.PASS
                row['diagnostics'] = [diagnostic(code, source_id) for code in ir.warnings]
                row['embedded_lore'] = ir.lore is not None
                row['lore_entries'] = len(ir.lore.entries) if ir.lore else 0
                row['extension_count'] = len(ir.extensions.value())
                row['linked_lore'] = bool(ir.lore_references.value())
                embedded += row['embedded_lore']
                extensions += row['extension_count'] > 0
                linked += row['linked_lore']
                namespaces.update(hashlib.sha256(k.encode()).hexdigest() for k in ir.extensions.value()
                                  if k not in ('world', 'extraBooks'))
                logical[ir.payload_fingerprint] += 1
            except ImportFailure as exc:
                category = exc.category
                row['spec'] = getattr(exc, 'source_spec', 'UNKNOWN')
                row['diagnostics'] = [diagnostic(exc.code, source_id, 'error', exc.stage, exc.field)]
            except OSError:
                category = Classification.UNSUPPORTED
                row['diagnostics'] = [diagnostic('FILE_READ_ERROR', source_id, 'error', 'read')]
            except Exception:
                # 内部缺陷不归咎于输入；不得通过异常文本或堆栈泄露角色卡内容。
                category = Classification.INTERNAL_ERROR
                row['diagnostics'] = [diagnostic('PARSER_INTERNAL_ERROR', source_id, 'error', 'import')]
        versions[row['spec']] += 1
        counts[category.value] += 1
        row['classification'] = category.value
        rows.append(row)
    after = inventory(root)
    summary = {'total_scanned': len(before), 'PNG': formats['PNG'], 'JSON': formats['JSON'],
               'other_files': formats['OTHER'], **{v: versions[v] for v in ('V1', 'V2', 'V3', 'UNKNOWN')},
               **{c.value: counts[c.value] for c in Classification}, 'embedded_world_books': embedded,
               'cards_with_extensions': extensions, 'unknown_extension_namespaces': len(namespaces),
               'linked_lore_cards': linked, 'duplicate_logical_cards': sum(v - 1 for v in logical.values()),
               'parser_crash_count': counts['INTERNAL_ERROR'], 'corpus_modified': 'NO' if before == after else 'YES',
               'files_hashed_before': len(before), 'files_hashed_after': len(after)}
    return {'report_version': 1, 'summary': summary, 'cards': rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args(argv)
    try:
        # 读取语料前先校验目标路径；命令行仅在系统临时目录中写入新文件。
        if args.report:
            destination = args.report.resolve()
            if (not destination.is_relative_to(Path(tempfile.gettempdir()).resolve())
                    or destination.is_relative_to(args.directory.resolve()) or destination.exists()):
                raise ImportFailure('REPORT_REQUIRES_NEW_TEMP_PATH', 'report')
        report = scan(args.directory)
        if args.report:
            with destination.open('x', encoding='utf8') as handle:
                json.dump(report, handle, ensure_ascii=True, indent=2)
        print(json.dumps(report['summary'], sort_keys=True))
        return 1 if report['summary']['INTERNAL_ERROR'] or report['summary']['corpus_modified'] != 'NO' else 0
    except (ImportFailure, OSError):
        print(json.dumps({'error': 'SCAN_OR_REPORT_FAILED', 'corpus_integrity': 'NOT_VERIFIED'}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
