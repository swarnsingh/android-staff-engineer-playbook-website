"""Review aid for added lesson prose; the quarter-length target is not a gate.

Count visible narrative and inline identifiers. Exclude fenced examples, figures,
animations, SVGs, scripts and style content. Ordinary tables and Q&A count as
prose. Repeated navigation labels and generated UI chrome are excluded. Cross-reference stubs are reported separately, never treated as long lessons.
"""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import build

WORDS=re.compile(r"\b\w+(?:[’'-]\w+)*\b")
VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}


class Narrative(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack=[]
        self.bits=[]
    def handle_starttag(self,tag,attrs):
        classes=dict(attrs).get('class','').split()
        skip=tag in {'figure','pre','script','style','svg'} or 'pb-figure' in classes or 'blend-label' in classes
        inherited=self.stack[-1][1] if self.stack else False
        if tag not in VOID:self.stack.append((tag,skip or inherited))
        if not inherited:self.bits.append(' ')
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag:
                self.stack=self.stack[:i]
                break
        if not self.stack or not self.stack[-1][1]:self.bits.append(' ')
    def handle_data(self,text):
        if not self.stack or not self.stack[-1][1]:self.bits.append(text)


def words(markdown):
    parser=Narrative()
    parser.feed(build.MD.render(markdown))
    return len(WORDS.findall(''.join(parser.bits)))


def inventory():
    rows=[]
    for path in build.PAGES:
        if '/' not in path:continue
        raw=(build.ROOT/path).read_text()
        chapter=build.corrected(raw,path)[0]
        blocks=build.load_blend(path)
        parts={str(key):words(text) for key,text in blocks.items() if key[0]!='part'}
        # The short hero description is authored site prose even when a blend supplies the opening.
        hero=words(build.intro(path))
        # Shared walkthrough prompts are prose too, even though they are not blend files.
        if build.walkthrough.listed(path):
            tokens=build.MD.parse(chapter)
            names=[(build.clean(tokens[i+1].content),'heading')
                   for i,t in enumerate(tokens) if t.type=='heading_open' and t.tag=='h2']
            for step in build.walkthrough.plan(path,names) or []:
                if step['role'] in build.walkthrough.TRY_FIRST:
                    parts['shared-prompt:'+step['role']]=words(build.walkthrough.try_first(step['role']))
        if path.endswith('/coroutines.md'):
            # Legacy authored additions rendered directly by build.py, outside the blend registry.
            for name in ('coroutine-internals.html','coroutine-policies.html','coroutine-experiment.html'):
                parts['shared-content:'+name]=words((build.WEB/'content'/name).read_text())
            import inspect
            source=inspect.getsource(build.render_chapter)
            import ast
            tree=ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='added' and len(node.args)>1:
                    literals=[n.value for n in ast.walk(node.args[1]) if isinstance(n,ast.Constant) and isinstance(n.value,str) and '<' in n.value]
                    if literals:parts['shared-wrapper:'+str(node.lineno)]=sum(words(t) for t in literals)
        added=sum(parts.values())+hero
        original=words(chapter)
        stub='cross-reference stub' in raw
        rows.append(dict(path=path,original_prose=original,added_prose=added,hero_prose=hero,
                         ratio=round(added/original,3) if original else None,stub=stub,
                         above_target=not stub and added>original/4,parts=parts))
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    rows=inventory()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n')
    flagged=sorted([r for r in rows if r['above_target']],key=lambda r:-r['ratio'])
    print(f'{len(rows)} chapters; {sum(r["stub"] for r in rows)} cross-reference stubs; {len(flagged)} above the working target.')
    for row in flagged:print(f'{row["ratio"]:.1%} {row["added_prose"]}/{row["original_prose"]} {row["path"]}')


if __name__=='__main__':main()
