#!/usr/bin/env python3
"""Compile exact corrected service Flow and focused official-contract regressions.

Uses installed Kotlin 2.4.21/coroutines 1.11.0 dependencies, without Gradle.
Android/Compose framework examples are API/source-reviewed, not Android-compiled here.
"""
from pathlib import Path
import os,re,subprocess,tempfile
from check_kotlin_examples import jar,ROOT,KOTLIN,COROUTINES
import build

java_home=os.environ.get('KOTLIN_JAVA_HOME')
java=str(Path(java_home)/'bin/java') if java_home else 'java'
compiler=os.pathsep.join(jar(*a) for a in [
 ('org.jetbrains.kotlin','kotlin-compiler-embeddable',KOTLIN),('org.jetbrains.kotlin','kotlin-stdlib',KOTLIN),
 ('org.jetbrains.kotlin','kotlin-script-runtime',KOTLIN),('org.jetbrains.kotlin','kotlin-reflect','1.6.10'),
 ('org.jetbrains.kotlin','kotlin-daemon-embeddable',KOTLIN),('org.jetbrains.intellij.deps','trove4j','1.0.20200330'),
 ('org.jetbrains','annotations','13.0'),('org.jetbrains.kotlinx','kotlinx-coroutines-core-jvm',COROUTINES)])
libraries=os.pathsep.join(jar(*a) for a in [('org.jetbrains.kotlin','kotlin-stdlib',KOTLIN),('org.jetbrains.kotlinx','kotlinx-coroutines-core-jvm',COROUTINES),('org.jetbrains.kotlinx','kotlinx-coroutines-test-jvm',COROUTINES)])
path='android/concurrency/services.md';source,_=build.corrected((ROOT/path).read_text(),path)
function=re.search(r'    fun processAudioFile\(fileUri: Uri\): Flow<Int> = flow \{.*?\n    }\.flowOn\(Dispatchers.IO\)[^\n]*',source,re.S)[0]
fixture=(ROOT/'website/tests/VerifiedReviewRegression.kt').read_text().replace('/* SERVICE_FUNCTION */',function)
base=[java,'-Xmx1g','-cp',compiler,'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler','-no-stdlib','-no-reflect','-classpath',libraries]
with tempfile.TemporaryDirectory(prefix='playbook-verified-review-') as td:
 target=Path(td);kt=target/'VerifiedReviewRegression.kt';kt.write_text(fixture)
 subprocess.run(base+['-d',td,str(kt)],check=True)
 subprocess.run([java,'-cp',td+os.pathsep+libraries,'VerifiedReviewRegressionKt'],check=True,timeout=30)
 bad=target/'DelegatedSmartCastMustFail.kt';bad.write_text('import kotlin.reflect.KProperty\nclass Delegate { operator fun getValue(thisRef: Any?, p: KProperty<*>): String? = "x" }\nfun invalid(): Int { val message by Delegate(); if(message != null) return message.length; return 0 }\n')
 result=subprocess.run(base+['-d',str(target/'negative'),str(bad)],capture_output=True,text=True)
 assert result.returncode and 'smart cast' in (result.stderr+result.stdout).lower(),result.stderr
 print('PASS delegated nullable property smart-cast rejection')
