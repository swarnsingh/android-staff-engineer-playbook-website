// Disposable regression fixtures for the read-only question/answer audit.
window.runQAFixtures = async () => {
  const report={done:false,ok:false,checks:[]},out=document.querySelector('#qa-fixture-results'),frame=document.querySelector('iframe');
  const save=()=>out.textContent=JSON.stringify(report,null,2);
  const hash=async text=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text.replace(/\s+/g,' ').trim())))].map(b=>b.toString(16).padStart(2,'0')).join('');
  const manifest={fixture:[
    {kind:'heading',text:'Questions',view:'qa'},
    {kind:'text',text:'First question?',view:'qa'},
    {kind:'text',text:'Second question?',view:'qa'},
    {kind:'heading',text:'Answer Key',view:'qa'},
    {kind:'text',text:'First answer.',view:'qa'},
    {kind:'text',text:'Second answer.',view:'qa'},
    {kind:'code',text:'val n = 1',view:'qa'}
  ]};
  const pairs={fixture:[
    {number:1,question_sha256:await hash('First question?'),answer_sha256:await hash('First answer.')},
    {number:2,question_sha256:await hash('Second question?'),answer_sha256:await hash('Second answer.val n = 1')}
  ]};
  const a='<li data-original-section="section-answer-key" data-original-answer-index="1">First answer.</li>';
  const b='<li data-original-section="section-answer-key" data-original-answer-index="2"><p>Second answer.</p><pre><code>val n = 1</code></pre></li>';
  function documentHTML(first=a,second=b){
    const question=(n,text,answer)=>'<li data-qa-question-index="'+n+'">'+text+'<div class="qa-answer-pair"><h3 class="qa-answer-label">Answer</h3><ol start="'+n+'">'+answer+'</ol></div></li>';
    return '<!doctype html><html><head><meta charset="utf-8"><title>QA fixture</title></head><body data-source="fixture"><main><div class="lesson-hero"><h1>Fixture</h1></div><section id="panel-qa"><section id="section-probing-questions" data-source-order="1"><h2>Questions</h2><section id="section-answer-key" data-source-order="2"><h2>Answer Key</h2><ol hidden data-qa-answer-slot="section-answer-key"></ol></section><ol>'+question(1,'First question?',first)+question(2,'Second question?',second)+'</ol></section></section></main><script src="/fx/audit.js"></script></body></html>';
  }
  const base=documentHTML();
  const cases=[
    ['visible paired control',base,true],
    ['missing answer',documentHTML('',b),false],
    ['duplicated answer',documentHTML(a+a,b),false],
    ['swapped original answers',documentHTML(b,a),false],
    ['wrong ordinal',documentHTML(a.replace('index="1"','index="2"'),b),false],
    ['changed answer',documentHTML(a.replace('First answer.','Different answer.'),b),false],
    ['changed code',documentHTML(a,b.replace('val n = 1','val n = 2')),false],
    ['hidden answer',documentHTML(a.replace('<li ','<li style="display:none" '),b),false],
    ['folded answer',documentHTML('<details><summary>Hidden answer</summary>'+a+'</details>',b),false],
    ['hidden question and answer',base.replace('data-qa-question-index="1"','data-qa-question-index="1" style="opacity:0"'),false],
    ['missing original answer heading',base.replace('<h2>Answer Key</h2>',''),false],
    ['changed question',base.replace('First question?','Another question?'),false]
  ];
  try{
    for(const [name,html,expected] of cases){
      const loaded=new Promise(r=>frame.onload=r);frame.srcdoc=html;await loaded;
      const result=await frame.contentWindow.__inspectOriginalContent({},manifest,'qa',pairs);
      const actual=result.problems.length===0;
      report.checks.push({name,expected,actual,ok:actual===expected,problems:result.problems});save();
    }
    // Re-run the older content fixtures too: QA support must not relax the
    // original missing/repeated/hidden-content and failed-diagram detections.
    const legacy=await (await fetch('/fixtures/cases.json')).json();
    for(const fixture of legacy){
      const html=(await (await fetch('/fixtures/'+fixture.file)).text()).replace('</body>','<script src="/fx/audit.js"></script></body>');
      const loaded=new Promise(r=>frame.onload=r);frame.srcdoc=html;await loaded;
      const result=await frame.contentWindow.__inspectOriginalContent(fixture.diagrams,fixture.units,'content');
      const actual=result.problems.length===0;
      report.checks.push({name:'content: '+fixture.name,expected:fixture.expected,actual,ok:actual===(fixture.expected!=='fail'),problems:result.problems});save();
    }
  }catch(error){report.checks.push({name:'runner',ok:false,error:String(error)});}
  report.done=true;report.ok=report.checks.every(c=>c.ok);save();
};
