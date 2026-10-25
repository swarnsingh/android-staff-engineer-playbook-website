#!/usr/bin/env python3
"""Compile the exact CH4 proposal and exercise lifecycle/boxing regressions.

Uses already-installed Maven/Gradle artifacts; never runs Gradle or downloads dependencies.
KOTLIN_COMPILER_CP and KOTLIN_TEST_CP may override automatic local-cache discovery.
"""
from pathlib import Path
import json, os, re, shutil, subprocess, tempfile

ROOT = Path(__file__).resolve().parents[2]
KOTLIN = '2.4.21'
COROUTINES = '1.11.0'


def jar(group, artifact, version):
    roots = [Path.home()/'.gradle/caches/modules-2/files-2.1'/group/artifact/version,
             Path.home()/'.m2/repository'/group.replace('.', '/')/artifact/version]
    for root in roots:
        matches = sorted(root.rglob(f'{artifact}-{version}.jar')) if root.exists() else []
        if matches:
            return str(matches[0])
    raise SystemExit(f'Missing cached dependency {group}:{artifact}:{version}; configure KOTLIN_COMPILER_CP / KOTLIN_TEST_CP with installed artifacts.')


def main():
    java_home = os.environ.get('KOTLIN_JAVA_HOME')
    java = str(Path(java_home)/'bin/java') if java_home else shutil.which('java')
    if not java:
        raise SystemExit('JDK 17 is required; set KOTLIN_JAVA_HOME to an installed JDK 17.')
    version = subprocess.run([java, '-version'], capture_output=True, text=True, check=True)
    version_text = version.stderr + version.stdout
    if not re.search(r'version "17[.\"]', version_text):
        raise SystemExit('These regression fixtures require JDK 17. Set KOTLIN_JAVA_HOME. Found: ' + version_text.splitlines()[0])
    print(f'Kotlin {KOTLIN}, coroutines {COROUTINES}; {version_text.splitlines()[0]}', flush=True)
    compiler = os.environ.get('KOTLIN_COMPILER_CP')
    if not compiler:
        compiler = os.pathsep.join(jar(*args) for args in [
            ('org.jetbrains.kotlin','kotlin-compiler-embeddable',KOTLIN),
            ('org.jetbrains.kotlin','kotlin-stdlib',KOTLIN),
            ('org.jetbrains.kotlin','kotlin-script-runtime',KOTLIN),
            ('org.jetbrains.kotlin','kotlin-reflect','1.6.10'),  # compiler 2.4.21 POM runtime dependency
            ('org.jetbrains.kotlin','kotlin-daemon-embeddable',KOTLIN),
            ('org.jetbrains.intellij.deps','trove4j','1.0.20200330'),
            ('org.jetbrains','annotations','13.0'),
            ('org.jetbrains.kotlinx','kotlinx-coroutines-core-jvm',COROUTINES)])
    libraries = os.environ.get('KOTLIN_TEST_CP') or os.pathsep.join(jar(*args) for args in [
        ('org.jetbrains.kotlin','kotlin-stdlib',KOTLIN),
        ('org.jetbrains.kotlinx','kotlinx-coroutines-core-jvm',COROUTINES),
        ('org.jetbrains.kotlinx','kotlinx-coroutines-test-jvm',COROUTINES)])
    proposals = json.loads((ROOT/'website/reviews/corrections-with-edits.json').read_text())
    fix = next(row for row in proposals if row['id'] == 'CH4')
    original = (ROOT/fix['path']).read_text()
    assert original.count(fix['old']) == 1, 'CH4 original has drifted'
    command_types = re.search(r'```kotlin\n(sealed interface CartCommand.*?\n})\n\nclass CartActor', original, re.S)[1]
    source = (ROOT/'website/tests/CartActorRegression.kt').read_text().replace('/* ACTOR_FROM_PROPOSAL */',command_types+'\n\n'+fix['new'])
    with tempfile.TemporaryDirectory(prefix='playbook-kotlin-regressions-') as directory:
        target = Path(directory)
        fixture = target/'CartActorRegression.kt';fixture.write_text(source)
        subprocess.run([java,'-Xmx1g','-cp',compiler,'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler','-no-stdlib','-no-reflect','-classpath',libraries,'-d',str(target),str(fixture)],check=True)
        subprocess.run([java,'-cp',str(target)+os.pathsep+libraries,'CartActorRegressionKt'],check=True,timeout=30)
        rejected = target/'ValueClassIdentityMustFail.kt'
        rejected.write_text('@JvmInline value class Meters(val value: Double)\nfun invalid(a: Meters, b: Meters) = a === b\n')
        negative = subprocess.run([java,'-Xmx1g','-cp',compiler,'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler','-no-stdlib','-no-reflect','-classpath',libraries,'-d',str(target/'negative'),str(rejected)],capture_output=True,text=True,timeout=30)
        diagnostic = negative.stderr + negative.stdout
        if negative.returncode == 0 or 'identity equality' not in diagnostic or 'prohibited' not in diagnostic:
            raise AssertionError('Value-class identity must fail specifically because identity equality is prohibited: ' + diagnostic)
        print('Negative compilation: Meters === Meters rejected as expected.')


if __name__ == '__main__':
    main()
