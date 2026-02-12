#!/usr/bin/env python
"""
Quality Scoring System for Empirical Finance Research

Calculates objective quality scores (0-100) based on defined rubrics.
Enforces quality gates: 80 (commit), 90 (PR), 95 (excellence).

Supports: Python scripts (.py), Stata do-files (.do), LaTeX manuscripts (.tex)

Usage:
    python scripts/quality_score.py src/py/01_clean.py
    python scripts/quality_score.py src/stata/01_setup.do
    python scripts/quality_score.py Overleaf/main.tex
    python scripts/quality_score.py src/py/*.py --summary
"""

import sys
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
import re
import json

# ==============================================================================
# SCORING RUBRICS (from .claude/rules/quality-gates.md)
# ==============================================================================

PYTHON_RUBRIC = {
    'critical': {
        'syntax_error': {'points': 100, 'auto_fail': True},
        'hardcoded_path': {'points': 20},
        'overwrites_raw_data': {'points': 20},
        'domain_bug': {'points': 30},
    },
    'major': {
        'missing_seed': {'points': 10},
        'missing_manifest': {'points': 10},
        'missing_log': {'points': 5},
        'missing_error_handling': {'points': 5},
    },
    'minor': {
        'style_violation': {'points': 1},
        'missing_docstring': {'points': 2},
        'long_line': {'points': 1},
    }
}

STATA_RUBRIC = {
    'critical': {
        'does_not_run': {'points': 100, 'auto_fail': True},
        'missing_version': {'points': 15},
        'overwrites_raw_data': {'points': 20},
        'wrong_clustering': {'points': 30},
    },
    'major': {
        'missing_set_more_off': {'points': 10},
        'missing_log': {'points': 10},
        'unchecked_merge': {'points': 10},
        'hardcoded_path': {'points': 10},
    },
    'minor': {
        'missing_header': {'points': 3},
        'missing_comments': {'points': 1},
    }
}

MANUSCRIPT_RUBRIC = {
    'critical': {
        'compilation_failure': {'points': 100, 'auto_fail': True},
        'undefined_citation': {'points': 15},
        'equation_typo': {'points': 10},
    },
    'major': {
        'overfull_hbox': {'points': 5},
        'notation_inconsistency': {'points': 5},
        'missing_table_notes': {'points': 3},
    },
    'minor': {
        'grammar_typo': {'points': 1},
        'citation_style_inconsistency': {'points': 1},
    }
}

THRESHOLDS = {
    'commit': 80,
    'pr': 90,
    'excellence': 95
}

# ==============================================================================
# ISSUE DETECTION
# ==============================================================================

class IssueDetector:
    """Detect common issues for quality scoring."""

    @staticmethod
    def check_python_syntax(filepath: Path) -> Tuple[bool, str]:
        """Check if Python file has syntax errors via py_compile."""
        try:
            result = subprocess.run(
                ['python', '-m', 'py_compile', str(filepath)],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                return False, result.stderr
            return True, ""
        except subprocess.TimeoutExpired:
            return False, "Syntax check timeout"
        except FileNotFoundError:
            return False, "Python not found"

    @staticmethod
    def check_hardcoded_paths(content: str) -> List[int]:
        """Detect absolute paths in code."""
        issues = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Skip comments
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('*') or stripped.startswith('//'):
                continue
            # Check for Windows absolute paths or Unix absolute paths
            if re.search(r'["\'][A-Za-z]:[/\\]', line):
                if not re.search(r'http:|https:', line):
                    issues.append(i)
            # Also check for Unix-style absolute paths in non-comment context
            if re.search(r'["\']/(?:Users|home|tmp|var)', line):
                issues.append(i)

        return issues

    @staticmethod
    def check_python_seed(content: str) -> bool:
        """Check if SEED is defined at module top."""
        lines = content.split('\n')
        # Check first 30 lines for SEED definition
        header = '\n'.join(lines[:30])
        return bool(re.search(r'^SEED\s*=\s*\d+', header, re.MULTILINE))

    @staticmethod
    def check_python_manifest(content: str) -> bool:
        """Check if script writes a manifest JSON."""
        return 'manifest' in content.lower() and 'json' in content.lower()

    @staticmethod
    def check_python_raw_data_writes(content: str) -> List[int]:
        """Check for writes to the raw data/ directory."""
        issues = []
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if re.search(r'\.to_csv|\.to_parquet|\.to_excel|\.to_stata|write_text|open\(', line):
                if re.search(r'["\']data/', line) and not re.search(r'data_processed', line):
                    issues.append(i)
        return issues

    @staticmethod
    def check_python_docstring(content: str) -> bool:
        """Check if module has a docstring."""
        stripped = content.lstrip()
        return stripped.startswith('"""') or stripped.startswith("'''")

    @staticmethod
    def check_stata_version(content: str) -> bool:
        """Check if do-file starts with version declaration."""
        lines = content.split('\n')
        for line in lines[:10]:
            if re.match(r'\s*version\s+\d+', line.strip()):
                return True
        return False

    @staticmethod
    def check_stata_set_more_off(content: str) -> bool:
        """Check for set more off."""
        return 'set more off' in content

    @staticmethod
    def check_stata_log(content: str) -> bool:
        """Check if do-file creates a log."""
        return 'log using' in content

    @staticmethod
    def check_stata_unchecked_merge(content: str) -> List[int]:
        """Check for merge commands without subsequent _merge check."""
        issues = []
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('merge ') or stripped.startswith('merge\t'):
                # Look ahead 5 lines for _merge check
                lookahead = '\n'.join(lines[i:i+5])
                if '_merge' not in lookahead:
                    issues.append(i)
        return issues

    @staticmethod
    def check_stata_raw_data_writes(content: str) -> List[int]:
        """Check for saves to raw data/ directory."""
        issues = []
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if re.search(r'save\s+.*["\']?\$?.*data/', line, re.IGNORECASE):
                if 'data_processed' not in line and 'DATA_PROCESSED' not in line:
                    issues.append(i)
        return issues

    @staticmethod
    def check_stata_header(content: str) -> bool:
        """Check for header block with purpose, author, date."""
        header = '\n'.join(content.split('\n')[:20])
        has_purpose = bool(re.search(r'purpose|Purpose|PURPOSE', header, re.IGNORECASE))
        has_author = bool(re.search(r'author|Author|AUTHOR', header, re.IGNORECASE))
        return has_purpose and has_author

    @staticmethod
    def check_latex_syntax(content: str) -> List[Dict]:
        """Check for common LaTeX syntax issues without compiling."""
        issues = []
        lines = content.split('\n')

        env_stack = []
        for i, line in enumerate(lines, 1):
            stripped = line.split('%')[0] if '%' in line else line

            for match in re.finditer(r'\\begin\{(\w+)\}', stripped):
                env_stack.append((match.group(1), i))

            for match in re.finditer(r'\\end\{(\w+)\}', stripped):
                env_name = match.group(1)
                if env_stack and env_stack[-1][0] == env_name:
                    env_stack.pop()
                elif env_stack:
                    issues.append({
                        'line': i,
                        'description': f'Mismatched environment: \\end{{{env_name}}} '
                                       f'but expected \\end{{{env_stack[-1][0]}}} '
                                       f'(opened at line {env_stack[-1][1]})',
                    })
                else:
                    issues.append({
                        'line': i,
                        'description': f'\\end{{{env_name}}} without matching \\begin',
                    })

        for env_name, line_num in env_stack:
            issues.append({
                'line': line_num,
                'description': f'Unclosed environment: \\begin{{{env_name}}} never closed',
            })

        return issues

    @staticmethod
    def check_broken_citations(content: str, bib_file: Path) -> List[str]:
        """Check for citation keys not in bibliography."""
        cite_pattern = r'\\cite[a-z]*\{([^}]+)\}'
        cited_keys = set()
        for match in re.finditer(cite_pattern, content):
            keys = match.group(1).split(',')
            cited_keys.update(k.strip() for k in keys)

        if not bib_file.exists():
            return list(cited_keys) if cited_keys else []

        bib_content = bib_file.read_text(encoding='utf-8')
        bib_keys = set(re.findall(r'@\w+\{([^,]+),', bib_content))

        broken = cited_keys - bib_keys
        return list(broken)

    @staticmethod
    def check_equation_overflow(content: str) -> List[int]:
        """Detect equations with single lines likely to overflow."""
        overflows = []
        lines = content.split('\n')
        in_math = False
        math_delim = None

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            if '$$' in stripped and math_delim != 'env':
                if not in_math:
                    in_math = True
                    math_delim = '$$'
                    if stripped.count('$$') >= 2:
                        inner = stripped.split('$$')[1]
                        if len(inner.strip()) > 120:
                            overflows.append(i)
                        in_math = False
                        math_delim = None
                    continue
                else:
                    in_math = False
                    math_delim = None
                    continue

            env_begin = re.match(
                r'\\begin\{(equation|align|gather|multline|eqnarray)\*?\}', stripped
            )
            if env_begin and not in_math:
                in_math = True
                math_delim = 'env'
                continue

            if re.match(r'\\end\{(equation|align|gather|multline|eqnarray)\*?\}', stripped):
                in_math = False
                math_delim = None
                continue

            if in_math:
                code_part = line.split('%')[0] if '%' in line else line
                if len(code_part.strip()) > 120:
                    overflows.append(i)

        return overflows


# ==============================================================================
# QUALITY SCORER
# ==============================================================================

class QualityScorer:
    """Calculate quality scores for research project files."""

    def __init__(self, filepath: Path, verbose: bool = False):
        self.filepath = filepath
        self.verbose = verbose
        self.score = 100
        self.issues = {
            'critical': [],
            'major': [],
            'minor': []
        }
        self.auto_fail = False

    def score_python(self) -> Dict:
        """Score Python script quality."""
        content = self.filepath.read_text(encoding='utf-8')

        # Check syntax
        is_valid, error = IssueDetector.check_python_syntax(self.filepath)
        if not is_valid:
            self.auto_fail = True
            self.issues['critical'].append({
                'type': 'syntax_error',
                'description': 'Python syntax error',
                'details': error[:200],
                'points': 100
            })
            self.score = 0
            return self._generate_report()

        # Check hardcoded paths
        path_issues = IssueDetector.check_hardcoded_paths(content)
        for line in path_issues:
            self.issues['critical'].append({
                'type': 'hardcoded_path',
                'description': f'Hardcoded absolute path at line {line}',
                'details': 'Use Path(__file__).resolve().parents[2] for repo root',
                'points': 20
            })
            self.score -= 20

        # Check for raw data overwrites
        raw_writes = IssueDetector.check_python_raw_data_writes(content)
        for line in raw_writes:
            self.issues['critical'].append({
                'type': 'overwrites_raw_data',
                'description': f'Writes to raw data/ directory at line {line}',
                'details': 'Write to data_processed/ or results/ instead',
                'points': 20
            })
            self.score -= 20

        # Check SEED
        has_random = any(fn in content for fn in [
            'random.seed', 'np.random', 'sample(', 'shuffle', 'choice('
        ])
        if has_random and not IssueDetector.check_python_seed(content):
            self.issues['major'].append({
                'type': 'missing_seed',
                'description': 'Missing SEED = 42 at module top',
                'details': 'Add SEED = 42 at top and use for all random operations',
                'points': 10
            })
            self.score -= 10

        # Check manifest
        if not IssueDetector.check_python_manifest(content):
            self.issues['major'].append({
                'type': 'missing_manifest',
                'description': 'No manifest JSON pattern detected',
                'details': 'Write manifest to results/runs/ on every execution',
                'points': 10
            })
            self.score -= 10

        # Check docstring
        if not IssueDetector.check_python_docstring(content):
            self.issues['minor'].append({
                'type': 'missing_docstring',
                'description': 'Missing module docstring',
                'details': 'Add docstring with title, purpose, inputs, outputs',
                'points': 2
            })
            self.score -= 2

        self.score = max(0, self.score)
        return self._generate_report()

    def score_stata(self) -> Dict:
        """Score Stata do-file quality."""
        content = self.filepath.read_text(encoding='utf-8')

        # Check version declaration
        if not IssueDetector.check_stata_version(content):
            self.issues['critical'].append({
                'type': 'missing_version',
                'description': 'Missing version 19.5 declaration',
                'details': 'Add "version 19.5" as first line of do-file',
                'points': 15
            })
            self.score -= 15

        # Check for raw data overwrites
        raw_writes = IssueDetector.check_stata_raw_data_writes(content)
        for line in raw_writes:
            self.issues['critical'].append({
                'type': 'overwrites_raw_data',
                'description': f'Writes to raw data/ directory at line {line}',
                'details': 'Save to data_processed/ or results/ instead',
                'points': 20
            })
            self.score -= 20

        # Check hardcoded paths
        path_issues = IssueDetector.check_hardcoded_paths(content)
        for line in path_issues:
            self.issues['major'].append({
                'type': 'hardcoded_path',
                'description': f'Hardcoded absolute path at line {line}',
                'details': 'Use globals for directory structure',
                'points': 10
            })
            self.score -= 10

        # Check set more off
        if not IssueDetector.check_stata_set_more_off(content):
            self.issues['major'].append({
                'type': 'missing_set_more_off',
                'description': 'Missing "set more off"',
                'details': 'Add "set more off" after version declaration',
                'points': 10
            })
            self.score -= 10

        # Check log file
        if not IssueDetector.check_stata_log(content):
            self.issues['major'].append({
                'type': 'missing_log',
                'description': 'No log file created',
                'details': 'Add log using "logs/[script_name].log", replace',
                'points': 10
            })
            self.score -= 10

        # Check unchecked merges
        unchecked = IssueDetector.check_stata_unchecked_merge(content)
        for line in unchecked:
            self.issues['major'].append({
                'type': 'unchecked_merge',
                'description': f'Merge without _merge check at line {line}',
                'details': 'Add tab _merge and assert after every merge',
                'points': 10
            })
            self.score -= 10

        # Check header
        if not IssueDetector.check_stata_header(content):
            self.issues['minor'].append({
                'type': 'missing_header',
                'description': 'Missing header block (purpose, author, date)',
                'details': 'Add header with title, author, date, purpose, inputs, outputs',
                'points': 3
            })
            self.score -= 3

        self.score = max(0, self.score)
        return self._generate_report()

    def score_manuscript(self) -> Dict:
        """Score LaTeX manuscript quality."""
        content = self.filepath.read_text(encoding='utf-8')

        # Check for LaTeX syntax issues
        syntax_issues = IssueDetector.check_latex_syntax(content)
        if syntax_issues:
            for issue in syntax_issues:
                self.issues['critical'].append({
                    'type': 'compilation_failure',
                    'description': f'LaTeX syntax issue at line {issue["line"]}',
                    'details': issue['description'],
                    'points': 100
                })
            self.auto_fail = True
            self.score = 0
            return self._generate_report()

        # Check for undefined citations
        bib_file = self.filepath.parent / 'references.bib'
        if not bib_file.exists():
            bib_file = self.filepath.parent.parent / 'Overleaf' / 'references.bib'
        broken_citations = IssueDetector.check_broken_citations(content, bib_file)
        for key in broken_citations:
            self.issues['critical'].append({
                'type': 'undefined_citation',
                'description': f'Citation key not in bibliography: {key}',
                'details': 'Add to Overleaf/references.bib or fix key',
                'points': 15
            })
            self.score -= 15

        # Check for equation overflow risk
        equation_overflows = IssueDetector.check_equation_overflow(content)
        for line_num in equation_overflows:
            self.issues['major'].append({
                'type': 'overfull_hbox',
                'description': f'Potential equation overflow at line {line_num}',
                'details': 'Single equation line >120 chars may cause overfull hbox',
                'points': 5
            })
            self.score -= 5

        self.score = max(0, self.score)
        return self._generate_report()

    def _generate_report(self) -> Dict:
        """Generate quality score report."""
        if self.auto_fail:
            status = 'FAIL'
            threshold = 'None (auto-fail)'
        elif self.score >= THRESHOLDS['excellence']:
            status = 'EXCELLENCE'
            threshold = 'excellence'
        elif self.score >= THRESHOLDS['pr']:
            status = 'PR_READY'
            threshold = 'pr'
        elif self.score >= THRESHOLDS['commit']:
            status = 'COMMIT_READY'
            threshold = 'commit'
        else:
            status = 'BLOCKED'
            threshold = 'None (below commit)'

        critical_count = len(self.issues['critical'])
        major_count = len(self.issues['major'])
        minor_count = len(self.issues['minor'])
        total_count = critical_count + major_count + minor_count

        return {
            'filepath': str(self.filepath),
            'score': self.score,
            'status': status,
            'threshold': threshold,
            'auto_fail': self.auto_fail,
            'issues': {
                'critical': self.issues['critical'],
                'major': self.issues['major'],
                'minor': self.issues['minor'],
                'counts': {
                    'critical': critical_count,
                    'major': major_count,
                    'minor': minor_count,
                    'total': total_count
                }
            },
            'thresholds': THRESHOLDS
        }

    def print_report(self, summary_only: bool = False) -> None:
        """Print formatted quality report."""
        report = self._generate_report()

        print(f"\n# Quality Score: {self.filepath.name}\n")

        status_emoji = {
            'EXCELLENCE': '[EXCELLENCE]',
            'PR_READY': '[PASS]',
            'COMMIT_READY': '[PASS]',
            'BLOCKED': '[BLOCKED]',
            'FAIL': '[FAIL]'
        }

        print(f"## Overall Score: {report['score']}/100 {status_emoji.get(report['status'], '')}")

        if report['status'] == 'BLOCKED':
            print(f"\n**Status:** BLOCKED - Cannot commit (score < {THRESHOLDS['commit']})")
        elif report['status'] == 'COMMIT_READY':
            print(f"\n**Status:** Ready for commit (score >= {THRESHOLDS['commit']})")
            gap_to_pr = THRESHOLDS['pr'] - report['score']
            print(f"**Next milestone:** PR threshold ({THRESHOLDS['pr']}+)")
            print(f"**Gap analysis:** Need +{gap_to_pr} points to reach PR quality")
        elif report['status'] == 'PR_READY':
            print(f"\n**Status:** Ready for PR (score >= {THRESHOLDS['pr']})")
            gap_to_excellence = THRESHOLDS['excellence'] - report['score']
            if gap_to_excellence > 0:
                print(f"**Next milestone:** Excellence ({THRESHOLDS['excellence']})")
                print(f"**Gap analysis:** +{gap_to_excellence} points to excellence")
        elif report['status'] == 'EXCELLENCE':
            print(f"\n**Status:** Excellence achieved! (score >= {THRESHOLDS['excellence']})")
        elif report['status'] == 'FAIL':
            print(f"\n**Status:** Auto-fail (compilation/syntax error)")

        if summary_only:
            print(f"\n**Total issues:** {report['issues']['counts']['total']} "
                  f"({report['issues']['counts']['critical']} critical, "
                  f"{report['issues']['counts']['major']} major, "
                  f"{report['issues']['counts']['minor']} minor)")
            return

        # Detailed issues
        print(f"\n## Critical Issues (MUST FIX): {report['issues']['counts']['critical']}")
        if report['issues']['counts']['critical'] == 0:
            print("No critical issues - safe to commit\n")
        else:
            for i, issue in enumerate(report['issues']['critical'], 1):
                print(f"{i}. **{issue['description']}** (-{issue['points']} points)")
                print(f"   - {issue['details']}\n")

        if report['issues']['counts']['major'] > 0:
            print(f"## Major Issues (SHOULD FIX): {report['issues']['counts']['major']}")
            for i, issue in enumerate(report['issues']['major'], 1):
                print(f"{i}. **{issue['description']}** (-{issue['points']} points)")
                print(f"   - {issue['details']}\n")

        if report['issues']['counts']['minor'] > 0 and self.verbose:
            print(f"## Minor Issues (NICE-TO-HAVE): {report['issues']['counts']['minor']}")
            for i, issue in enumerate(report['issues']['minor'], 1):
                print(f"{i}. {issue['description']} (-{issue['points']} points)\n")

        # Recommendations
        if report['status'] == 'BLOCKED':
            print("## Recommended Actions")
            print("1. Fix all critical issues above")
            print(f"2. Re-run quality score (target: >={THRESHOLDS['commit']})")
            print("3. Commit after reaching threshold\n")
        elif report['status'] == 'COMMIT_READY' and report['score'] < THRESHOLDS['pr']:
            print("## Recommended Actions to Reach PR Threshold")
            points_needed = THRESHOLDS['pr'] - report['score']
            print(f"Need +{points_needed} points to reach {THRESHOLDS['pr']}/100")
            if report['issues']['counts']['major'] > 0:
                print("Fix major issues listed above to improve score")


# ==============================================================================
# CLI INTERFACE
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Calculate quality scores for research project files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Score a Python script
  python scripts/quality_score.py src/py/01_clean.py

  # Score a Stata do-file
  python scripts/quality_score.py src/stata/01_setup.do

  # Score the LaTeX manuscript
  python scripts/quality_score.py Overleaf/main.tex

  # Score multiple files
  python scripts/quality_score.py src/py/*.py

  # Summary only
  python scripts/quality_score.py src/py/01_clean.py --summary

  # JSON output
  python scripts/quality_score.py src/py/01_clean.py --json

Quality Thresholds:
  80/100 = Commit threshold (blocks if below)
  90/100 = PR threshold (warning if below)
  95/100 = Excellence (publication-ready)

Exit Codes:
  0 = Score >= 80 (commit allowed)
  1 = Score < 80 (commit blocked)
  2 = Auto-fail (compilation/syntax error)
        """
    )

    parser.add_argument('filepaths', type=Path, nargs='+', help='Path(s) to file(s) to score')
    parser.add_argument('--summary', action='store_true', help='Show summary only')
    parser.add_argument('--verbose', action='store_true', help='Show all issues including minor')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    results = []
    exit_code = 0

    for filepath in args.filepaths:
        if not filepath.exists():
            print(f"Error: File not found: {filepath}")
            exit_code = 1
            continue

        try:
            scorer = QualityScorer(filepath, verbose=args.verbose)

            if filepath.suffix == '.py':
                report = scorer.score_python()
            elif filepath.suffix == '.do':
                report = scorer.score_stata()
            elif filepath.suffix == '.tex':
                report = scorer.score_manuscript()
            else:
                print(f"Error: Unsupported file type: {filepath.suffix} "
                      f"(supported: .py, .do, .tex)")
                continue

            results.append(report)

            if not args.json:
                scorer.print_report(summary_only=args.summary)

            if report['auto_fail']:
                exit_code = max(exit_code, 2)
            elif report['score'] < THRESHOLDS['commit']:
                exit_code = max(exit_code, 1)

        except Exception as e:
            print(f"Error scoring {filepath}: {e}")
            import traceback
            traceback.print_exc()
            exit_code = 1

    if args.json:
        print(json.dumps(results, indent=2))

    sys.exit(exit_code)

if __name__ == '__main__':
    main()
