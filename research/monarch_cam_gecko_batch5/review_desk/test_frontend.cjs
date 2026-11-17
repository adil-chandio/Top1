// Dependency-free DOM harness; NOT a browser/media playback test.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(__dirname+'/index.html','utf8');
class Element{
 constructor(){this.value='';this.children=[];this.currentTime=0;this.duration=66;this.playbackRate=1;this.textContent='';}
 append(...children){this.children.push(...children);for(const c of children)if(c.id)nodes[c.id]=c;}
 setAttribute(){}pause(){this.paused=true;}play(){this.paused=false;return Promise.resolve();}click(){this.clicked=true;}
}
const nodes={},store=new Map();let blob;
const document={getElementById(id){return nodes[id]??=(new Element());},createElement(){return new Element();}};
const context=vm.createContext({document,localStorage:{getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v),removeItem:k=>store.delete(k)},Blob,URL:{createObjectURL:b=>{blob=b;return 'blob:test';},revokeObjectURL(){}},setTimeout:fn=>fn(),confirm:()=>true,console});
vm.runInContext(html.split('<script>')[1].split('</script>')[0],context);
assert.equal(nodes.checks.children.length,8);
for(const id of ['terms','negation','seam','hyperextension','hook','continuity','whole','biology'])assert.equal(nodes[id+'-result'].value,'');
// Real browsers choose first option automatically; model that default for this mock.
for(const c of nodes.checks.children){const select=c.children[4];select.value='unreviewed';}
const negation=nodes.checks.children[1];negation.children[2].onclick();
assert.equal(nodes.film.currentTime,20);assert.equal(nodes.film.paused,true);assert.equal(nodes['negation-result'].value,'unreviewed');
nodes['negation-result'].value='issue_found';nodes['negation-notes'].value='Negation uncertain at 20.5s';nodes['negation-result'].onchange();assert.equal(store.size,1);
// Even unanimous favorable observations must never clear project/publication holds.
for(const c of nodes.checks.children)c.children[4].value='no_issue_observed';
nodes.export.onclick();
(async()=>{const exported=JSON.parse(await blob.text());assert.equal(exported.observations.length,8);assert.equal(exported.final_signoff,false);assert.equal(exported.project_holds_cleared,false);assert.equal(exported.publication_authorized,false);assert.equal(exported.candidate_version,'v6');nodes.clear.onclick();assert.equal(store.size,0);assert.equal(nodes['negation-result'].value,'unreviewed');console.log('Frontend harness: 8 fields; seek != review; local draft/export/reset and hold invariants PASS. Not a native-browser playback check.');})().catch(e=>{console.error(e);process.exitCode=1;});
