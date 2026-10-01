const {test}=require('node:test'),assert=require('node:assert/strict');
const {digest,validateRows}=require('./audit_manifest.cjs');
const m={'index.html':'page','assets/site.css':'css'},manifests={root:m};
const valid={mode:'root',size:'desktop',page:'index.html',pageSha256:'page',responseSha256:'page',treeSha256:digest(m)};
test('unchanged bound result can be reused',()=>validateRows([valid],manifests));
for(const [name,rows,current] of [
 ['legacy unbound result',[{mode:'root',size:'desktop',page:'index.html'}],manifests],
 ['changed HTML',[valid],{root:{...m,'index.html':'new'}}],
 ['changed shared CSS',[valid],{root:{...m,'assets/site.css':'new'}}],
 ['changed served response',[{...valid,responseSha256:'wrong'}],manifests],
 ['changed page fingerprint',[{...valid,pageSha256:'wrong'}],manifests],
])test(name+' cannot be reused',()=>assert.throws(()=>validateRows(rows,current),/Unbound or stale/));
