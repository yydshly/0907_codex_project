import {createServer} from 'node:http';
import {readFile,stat} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=fileURLToPath(new URL('../../docs/',import.meta.url));
const types={'.html':'text/html; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.js':'text/javascript','.css':'text/css'};
createServer(async(req,res)=>{
  try {
    let file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
    const relative=path.relative(root,file);
    if(relative.startsWith('..')||path.isAbsolute(relative)) {res.writeHead(403).end();return;}
    if((await stat(file)).isDirectory()) file=path.join(file,'index.html');
    res.writeHead(200,{'Content-Type':types[path.extname(file)]||'application/octet-stream'});
    res.end(await readFile(file));
  } catch {res.writeHead(404).end('Not found');}
}).listen(5187,'127.0.0.1',()=>console.log('http://127.0.0.1:5187/demos/007-cozyclay/'));
