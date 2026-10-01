const fs=require('fs'),path=require('path'),crypto=require('crypto');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function manifest(root){const result={};function walk(dir){for(const x of fs.readdirSync(dir,{withFileTypes:true})){const p=path.join(dir,x.name);if(x.isDirectory())walk(p);else if(x.isFile())result[path.relative(root,p).split(path.sep).join('/')]=sha(fs.readFileSync(p));}}walk(root);return Object.fromEntries(Object.entries(result).sort(([a],[b])=>a<b?-1:a>b?1:0));}
const digest=m=>sha(JSON.stringify(Object.entries(m).sort(([a],[b])=>a<b?-1:a>b?1:0)));
function validateRows(rows, manifests){for(const row of rows){const m=manifests[row.mode];if(!m||row.treeSha256!==digest(m)||row.pageSha256!==m[row.page]||row.responseSha256!==m[row.page])throw Error('Unbound or stale browser result: '+row.mode+'/'+row.size+'/'+row.page+'; rerun full audit without merge flags');}}
module.exports={sha,manifest,digest,validateRows};
