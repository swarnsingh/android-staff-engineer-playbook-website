#!/usr/bin/env python3
"""Compile the exact pilot consumer with fake local transaction contracts.

No database, network, Android or external-service integration is exercised.
Uses cached compiler artifacts only; never invokes Gradle or downloads.
"""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,tempfile
from check_kotlin_examples import KOTLIN,COROUTINES,jar
ROOT=Path(__file__).resolve().parents[2]

def main():
    chapter=ROOT/'distributed-systems/delivery-semantics.md'
    fragment=next(b for b in re.findall(r'```kotlin\n(.*?)```',chapter.read_text(),re.S) if 'class IdempotentConsumer' in b)
    fixture='''import kotlinx.coroutines.*
import kotlinx.coroutines.sync.*
import kotlin.time.Duration
import kotlin.time.Duration.Companion.days
data class Message(val idempotencyKey:String)
data class Result(val effect:Int)
class BusinessDatabase {
 val lock=Mutex(); val records=mutableMapOf<String,Result>();var effects=0
 suspend fun get(key:String)=lock.withLock{records[key]}
 suspend fun <T> serializableTransaction(body:suspend Tx.()->T):T=lock.withLock{Tx(this).body()}
 class Tx(val db:BusinessDatabase){fun get(key:String)=db.records[key];fun put(key:String,result:Result,ttl:Duration){db.records[key]=result}}
}
class MessageHandler {suspend fun applyLocalEffect(tx:BusinessDatabase.Tx,message:Message):Result {delay(1);return Result(++tx.db.effects)}}
'''+fragment+'''
fun main()=runBlocking {
 val db=BusinessDatabase();val c=IdempotentConsumer(db,MessageHandler())
 check(c.consume(Message("one"))==Result(1));check(c.consume(Message("one"))==Result(1));check(db.effects==1)
 val results=(1..8).map{async(Dispatchers.Default){c.consume(Message("two"))}}.awaitAll()
 check(results.all{it==Result(2)});check(db.effects==2);check(db.records.size==2)
 println("PASS: 6 assertions; duplicate and 8 concurrent deliveries share a local result")
}
'''
    java_home=os.environ.get('KOTLIN_JAVA_HOME')
    java=str(Path(java_home)/'bin/java') if java_home else str(Path('/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin/java'))
    if not Path(java).exists():java=shutil.which('java')
    version=subprocess.run([java,'-version'],capture_output=True,text=True,check=True)
    version_text=version.stderr+version.stdout
    assert re.search(r'version "17[.\"]',version_text),version_text
    compiler=os.environ.get('KOTLIN_COMPILER_CP') or os.pathsep.join(jar(*a) for a in [
        ('org.jetbrains.kotlin','kotlin-compiler-embeddable',KOTLIN),('org.jetbrains.kotlin','kotlin-stdlib',KOTLIN),
        ('org.jetbrains.kotlin','kotlin-script-runtime',KOTLIN),('org.jetbrains.kotlin','kotlin-reflect','1.6.10'),
        ('org.jetbrains.kotlin','kotlin-daemon-embeddable',KOTLIN),('org.jetbrains.intellij.deps','trove4j','1.0.20200330'),
        ('org.jetbrains','annotations','13.0'),('org.jetbrains.kotlinx','kotlinx-coroutines-core-jvm',COROUTINES)])
    libraries=os.environ.get('KOTLIN_TEST_CP') or os.pathsep.join(jar(*a) for a in [
        ('org.jetbrains.kotlin','kotlin-stdlib',KOTLIN),('org.jetbrains.kotlinx','kotlinx-coroutines-core-jvm',COROUTINES)])
    with tempfile.TemporaryDirectory(prefix='delivery-consumer-') as directory:
        target=Path(directory);file=target/'Delivery.kt';file.write_text(fixture)
        subprocess.run([java,'-cp',compiler,'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler','-no-stdlib','-no-reflect','-jvm-target','17','-cp',libraries,'-d',str(target),str(file)],check=True,timeout=90)
        result=subprocess.run([java,'-cp',str(target)+os.pathsep+libraries,'DeliveryKt'],check=True,capture_output=True,text=True,timeout=30)
    report={'status':'passed','assertions':6,'kotlin':KOTLIN,'coroutines':COROUTINES,'jdk':version_text.splitlines()[0],
        'chapter_sha256':hashlib.sha256(chapter.read_bytes()).hexdigest(),'fragment_sha256':hashlib.sha256(fragment.encode()).hexdigest(),
        'output':result.stdout.strip(),'limits':'Fake Mutex-backed transaction and handler only. Does not prove database isolation, rollback, account/payload checks, TTL or real-service effects. Other chapter fragments were not compiled in this pilot check.'}
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
