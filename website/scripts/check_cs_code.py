#!/usr/bin/env python3
"""Compile the exact Java variants shown on Computer Science pages using Java 17 APIs."""
import argparse, hashlib, json, pathlib, subprocess, tempfile, re, os
from urllib.request import urlretrieve
import build

def check(guava):
    pairs = build.CODE_PAIRS
    exceptions = json.loads((build.WEB/'content/code-kotlin-only.json').read_text())
    count = 0
    imports = 'import java.util.*;\nimport java.util.function.*;\nimport java.security.*;\nimport java.nio.*;\nimport java.nio.charset.*;\nimport java.io.*;\n'
    with tempfile.TemporaryDirectory(prefix='cs-java-') as directory:
        files = []
        for path in build.ORDER['computer-science']:
            source = build.corrected((build.ROOT/path).read_text(), path)[0]
            fences = [t for t in build.MD.parse(source) if t.type == 'fence']
            expected = {str(i) for i,t in enumerate(fences) if t.info.strip() == 'kotlin'}
            paired = set(pairs.get(path, {}))
            exempt = set(exceptions.get(path, {}))
            assert expected == paired | exempt and not paired & exempt, (path, 'coverage mismatch', expected-paired-exempt)
            for index, pair in pairs.get(path, {}).items():
                assert fences[int(index)].info.strip() == 'kotlin'
                if 'source_sha256' in pair:
                    assert pair['source_sha256'] == hashlib.sha256(fences[int(index)].content.encode()).hexdigest(), (path,index,'source changed')
                code = pair['java']
                if pair['java_mode'] == 'statements': code = 'void example() {\n'+code+'\n}'
                name = 'Snippet'+str(count)
                test = pair.get('java_test','')
                unit = imports+'final class '+name+' {\n'+pair.get('java_support','')+'\n'+code+'\npublic static void main(String[] args) {\n'+test+'\n}\n}'
                file = pathlib.Path(directory)/(name+'.java')
                file.write_text(unit)
                files.append(str(file)); count += 1
        result = subprocess.run(['javac','--release','17','-Xlint:all','-Werror','-cp',str(guava),'-d',directory,*files],capture_output=True,text=True)
        if result.returncode: raise RuntimeError(result.stderr)
        for index in range(count):
            subprocess.run(['java','-ea','-cp',directory+':'+str(guava),'Snippet'+str(index)],check=True,capture_output=True,text=True)
    print(f'PASS Computer Science: {count} exact Java snippets compile with --release 17; all Kotlin fences paired or explicitly Android/Kotlin-specific')

def check_kotlin(libraries, guava):
    sources = {}
    for path in build.ORDER['computer-science']:
        source = build.corrected((build.ROOT/path).read_text(), path)[0]
        sources[path.split('/')[-1].removesuffix('.md')] = [t.content for t in build.MD.parse(source) if t.type == 'fence']
    def block(chapter,index): return sources[chapter][index]
    support = {
        ('arrays-and-strings',8): 'class Item',
        ('arrays-and-strings',9): 'class Item\ndata class UiState(val items: List<Item>)',
        ('arrays-and-strings',10): 'data class User(val active: Boolean, val name: String)\nval users = emptyList<User>()',
        ('arrays-and-strings',11): 'val input = "KEY"',
        ('hashing',3): 'fun ByteArray.getInt(index: Int): Int = java.nio.ByteBuffer.wrap(this).order(java.nio.ByteOrder.LITTLE_ENDIAN).getInt(index)',
        ('hashing',6): 'val userId = "user"',
        ('hashing',7): 'val cacheDir = File(".")\nval url = "https://example.com"',
        ('linked-lists-stacks-queues',6): 'class Upload',
        ('trees',10): block('trees',6)+'\ndata class Location(val name: String)\nval locations = emptyList<Location>()',
        ('system-complexity',1): 'data class Input(val isValid: Boolean, val isRelevant: Boolean, val items: List<Input>)\ndata class Result(val values: List<Result>)\nval results = mutableListOf<Result>()'
    }
    for i in [4,5,6]: support['graphs',i] = block('graphs',3)
    for i in [2,3,4]: support['greedy-and-intervals',i] = block('greedy-and-intervals',1)
    support['recursion-backtracking',2] = block('recursion-backtracking',1)
    for i in [0,1,6]:
        support['sorting-and-searching',i] = 'data class User(val isPremium: Boolean, val lastActiveAtMillis: Long, val id: String)\nval users = emptyList<User>()\nval userId = "id"'
    support['sorting-and-searching',4] = block('sorting-and-searching',2)+block('sorting-and-searching',3)
    support['sorting-and-searching',5] = 'data class Tab(val selected: Boolean)'
    support['sorting-and-searching',8] = 'data class Post(val score: Double, val createdAtMillis: Long, val id: String)'
    statements = {('arrays-and-strings',i) for i in [1,2,3,10,11]} | {('heaps-and-priority-queues',2)}
    imports = 'import java.util.PriorityQueue\nimport java.util.Locale\nimport java.security.MessageDigest\nimport java.io.File\n'
    with tempfile.TemporaryDirectory(prefix='cs-kotlin-') as directory:
        files = []
        for path, pairs in build.CODE_PAIRS.items():
            chapter = path.split('/')[-1].removesuffix('.md')
            for index in pairs:
                key = (chapter,int(index))
                code = block(*key)
                extra_imports = '\n'.join(re.findall(r'^import .*$',code,re.M))
                code = re.sub(r'^import .*\n','',code,flags=re.M)
                if key in statements: code = 'fun example() {\n'+code+'\n}'
                file = pathlib.Path(directory)/('Snippet'+str(len(files))+'.kt')
                merged_imports = '\n'.join(dict.fromkeys((imports+extra_imports).splitlines()))
                file.write_text(merged_imports+'\nobject Snippet'+str(len(files))+' {\n'+support.get(key,'')+'\n'+code+'\n}')
                files.append(str(file))
        stdlib = next(libraries.glob('kotlin-stdlib-*.jar'))
        cp = str(stdlib)+':'+str(guava)
        result = subprocess.run(['java','-cp',str(libraries/'*'),'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler',
                                 '-no-stdlib','-no-reflect','-language-version','2.0','-api-version','2.0',
                                 '-jvm-target','17','-classpath',cp,'-d',directory,*files],capture_output=True,text=True)
        if result.returncode: raise RuntimeError(result.stderr)
    print(f'PASS {len(files)} exact Kotlin counterparts compile with language/API version 2.0')

if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--guava',type=pathlib.Path)
    parser.add_argument('--kotlin-libraries',type=pathlib.Path)
    args=parser.parse_args()
    if not args.guava:
        candidates = list(pathlib.Path.home().glob('.gradle/wrapper/dists/*/*/*/lib/guava-33.4.6-jre.jar'))
        args.guava = candidates[0] if candidates else build.CACHE/'code-validation/guava-33.4.6-jre.jar'
        if not args.guava.exists():
            args.guava.parent.mkdir(parents=True,exist_ok=True)
            urlretrieve('https://repo.maven.apache.org/maven2/com/google/guava/guava/33.4.6-jre/guava-33.4.6-jre.jar',args.guava)
    check(args.guava)
    if args.kotlin_libraries: check_kotlin(args.kotlin_libraries,args.guava)
