#!/usr/bin/env python3
"""Compile the exact Java variants shown on Computer Science pages using Java 17 APIs."""
import argparse, hashlib, json, pathlib, subprocess, tempfile
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

if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--guava',required=True,type=pathlib.Path)
    args=parser.parse_args(); check(args.guava)
