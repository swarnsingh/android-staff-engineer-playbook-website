#!/usr/bin/env python3
"""Check compiler-specific completion claims with the pinned Kotlin compiler."""
from pathlib import Path
import os,re,subprocess,tempfile,json
from check_kotlin_examples import jar,KOTLIN,COROUTINES,ROOT
import build
java_home=Path(os.environ['KOTLIN_JAVA_HOME']);java=str(java_home/'bin/java');javap=str(java_home/'bin/javap')
compiler=os.pathsep.join(jar(*a) for a in [('org.jetbrains.kotlin','kotlin-compiler-embeddable',KOTLIN),('org.jetbrains.kotlin','kotlin-stdlib',KOTLIN),('org.jetbrains.kotlin','kotlin-script-runtime',KOTLIN),('org.jetbrains.kotlin','kotlin-reflect','1.6.10'),('org.jetbrains.kotlin','kotlin-daemon-embeddable',KOTLIN),('org.jetbrains.intellij.deps','trove4j','1.0.20200330'),('org.jetbrains','annotations','13.0'),('org.jetbrains.kotlinx','kotlinx-coroutines-core-jvm',COROUTINES)])
libraries=os.pathsep.join(jar(*a) for a in [('org.jetbrains.kotlin','kotlin-stdlib',KOTLIN),('org.jetbrains.kotlinx','kotlinx-coroutines-core-jvm',COROUTINES)])
path='kotlin/version-updates/kotlin-2-4-update.md';text=build.corrected((ROOT/path).read_text(),path)[0]
session=next(c for c in re.findall(r'```kotlin\n(.*?)```',text,re.S) if 'class Session {' in c and 'field = MutableStateFlow' in c)
fixture='''import kotlinx.coroutines.flow.*
'''+session+'''
internal fun String.internalExtension()=length
fun isEven(value:Int)=value%2==0
fun filtered(values:List<Int>)=values.filter(::isEven)
class User(val name:String) { fun greeting()="Hello, $name" }
fun main() {
 val session=Session();check(session.token.value==null);session.authenticate("ok");check(session.token.value=="ok")
 check(filtered(listOf(1,2,3,4))==listOf(2,4));check(User("Ada").greeting()=="Hello, Ada")
 println("PASS exact explicit backing-field Session, inline filter and field accessor behavior")
}
'''
base=[java,'-Xmx1g','-cp',compiler,'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler','-no-stdlib','-no-reflect','-classpath',libraries]
with tempfile.TemporaryDirectory(prefix='completion-kotlin-') as td:
 d=Path(td);src=d/'Completion.kt';src.write_text(fixture)
 subprocess.run(base+['-d',td,str(src)],check=True,capture_output=True,text=True)
 subprocess.run([java,'-cp',td+os.pathsep+libraries,'CompletionKt'],check=True)
 code=subprocess.run([javap,'-c','-p','-classpath',td,'CompletionKt','User'],capture_output=True,text=True,check=True).stdout
 filtered=code[code.index('filtered('):code.index('public static final void main(')]
 assert 'public static final int internalExtension(java.lang.String)' in code
 assert 'internalExtension$' not in code
 assert 'FunctionReference' not in filtered and 'Function1' not in filtered and 'isEven:' in filtered
 user=code[code.index('public final java.lang.String greeting();'):]
 assert 'getfield' in user and 'getName:' not in user
 print('PASS javap internal top-level extension has no module-name suffix')
 print('PASS javap inline filter has no function object; greeting reads the field directly')
 bad=d/'Invalid.kt';bad.write_text('class Invalid { var token: String?\n field = null\n private set\n}\n')
 result=subprocess.run(base+['-d',str(d/'negative'),str(bad)],capture_output=True,text=True)
 assert result.returncode and "only 'val' properties" in result.stderr
 print('PASS mutable explicit backing field is rejected by Kotlin '+KOTLIN)
