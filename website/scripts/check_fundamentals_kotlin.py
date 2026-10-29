#!/usr/bin/env python3
"""Compile exact corrected Fundamentals JVM fragments and exercise their contracts.

Uses the locally cached Kotlin/coroutines artifacts; never invokes Gradle or downloads.
Android platform/application fragments remain subject to their documented assumptions.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from check_kotlin_examples import KOTLIN, COROUTINES, jar

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / 'website/reviews/engineering-fundamentals-2026-10-29'


def corrected(path, records):
    text = (ROOT / path).read_text()
    for row in records:
        if row['path'] == path:
            assert text.count(row['old']) == 1, row['id']
            text = text.replace(row['old'], row['new'])
    return text


def main():
    rows = json.loads((ROOT / 'website/content/corrections-engineering-fundamentals.json').read_text())
    fragments = {}
    for path, needles in {
        'engineering-fundamentals/time-and-clocks.md': ['class LamportClock', 'class VectorClock', 'data class HLC'],
        'engineering-fundamentals/caching.md': ['class LRUCache'],
        'engineering-fundamentals/fault-tolerance.md': ['suspend fun <T> withRetry'],
    }.items():
        source = corrected(path, rows)
        blocks = re.findall(r'```kotlin\n(.*?)\n```', source, re.S)
        for needle in needles:
            matched = [block for block in blocks if needle in block]
            assert len(matched) == 1, (path, needle)
            fragments[needle] = matched[0]
    imports, bodies = [], []
    for fragment in fragments.values():
        imports.extend(re.findall(r'^import .+$', fragment, re.M))
        bodies.append(re.sub(r'^import .+\n', '', fragment, flags=re.M))
    fixture_template = (ROOT / 'website/tests/FundamentalsRegression.kt').read_text()
    imports.extend(re.findall(r'^import .+$', fixture_template, re.M))
    fixture_body = re.sub(r'^import .+\n', '', fixture_template, flags=re.M)
    source = '\n'.join(sorted(set(imports))) + '\n' + fixture_body.replace('/* EXACT_CORRECTED_FRAGMENTS */', '\n\n'.join(bodies))
    java_home = os.environ.get('KOTLIN_JAVA_HOME')
    candidates = [Path('/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin/java')]
    java = str(Path(java_home) / 'bin/java') if java_home else next((str(p) for p in candidates if p.exists()), shutil.which('java'))
    assert java, 'Set KOTLIN_JAVA_HOME to an installed JDK 17'
    version = subprocess.run([java, '-version'], capture_output=True, text=True, check=True)
    version_text = version.stderr + version.stdout
    assert re.search(r'version "17[.\"]', version_text), version_text
    compiler = os.environ.get('KOTLIN_COMPILER_CP') or os.pathsep.join(jar(*args) for args in [
        ('org.jetbrains.kotlin', 'kotlin-compiler-embeddable', KOTLIN),
        ('org.jetbrains.kotlin', 'kotlin-stdlib', KOTLIN),
        ('org.jetbrains.kotlin', 'kotlin-script-runtime', KOTLIN),
        ('org.jetbrains.kotlin', 'kotlin-reflect', '1.6.10'),
        ('org.jetbrains.kotlin', 'kotlin-daemon-embeddable', KOTLIN),
        ('org.jetbrains.intellij.deps', 'trove4j', '1.0.20200330'),
        ('org.jetbrains', 'annotations', '13.0'),
        ('org.jetbrains.kotlinx', 'kotlinx-coroutines-core-jvm', COROUTINES),
    ])
    libraries = os.environ.get('KOTLIN_TEST_CP') or os.pathsep.join(jar(*args) for args in [
        ('org.jetbrains.kotlin', 'kotlin-stdlib', KOTLIN),
        ('org.jetbrains.kotlinx', 'kotlinx-coroutines-core-jvm', COROUTINES),
    ])
    with tempfile.TemporaryDirectory(prefix='fundamentals-jvm-') as directory:
        target = Path(directory)
        fixture = target / 'FundamentalsRegression.kt'
        fixture.write_text(source)
        subprocess.run([java, '-Xmx1g', '-cp', compiler, 'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler', '-no-stdlib', '-no-reflect', '-classpath', libraries, '-d', str(target), str(fixture)], check=True, timeout=90)
        result = subprocess.run([java, '-cp', str(target) + os.pathsep + libraries, 'FundamentalsRegressionKt'], check=True, timeout=30, capture_output=True, text=True)
    assertions = json.loads(result.stdout.strip().splitlines()[-1])
    report = {
        'status': 'passed',
        'kotlin': KOTLIN,
        'coroutines': COROUTINES,
        'jdk': version_text.splitlines()[0],
        'fragments': {key: hashlib.sha256(value.encode()).hexdigest() for key, value in fragments.items()},
        'fixture_sha256': hashlib.sha256(fixture_template.encode()).hexdigest(),
        'checks': assertions,
        'limits': [
            'Compiles the exact five corrected JVM fragments (Lamport, vector, HLC, LRU and retry), with imports only.',
            'HLC is tested with a received future timestamp, so local wall time is behind the retained physical component without changing the host clock.',
            'Android cache/clock/ViewModel snippets require their platform APIs and app adapters; network/storage examples are conceptual, not a built Android application.',
            'Manual mobile review remains deferred until all topic trees are integrated.',
        ],
    }
    (REVIEW / 'kotlin-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
