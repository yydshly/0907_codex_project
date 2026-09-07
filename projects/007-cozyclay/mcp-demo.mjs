import { Client } from '../../upstream/cozyclay/mcp/node_modules/@modelcontextprotocol/sdk/dist/esm/client/index.js';
import { StdioClientTransport } from '../../upstream/cozyclay/mcp/node_modules/@modelcontextprotocol/sdk/dist/esm/client/stdio.js';
import { fileURLToPath } from 'node:url';
import { writeFile } from 'node:fs/promises';
const client = new Client({name:'cozyclay-research-demo',version:'1.0.0'});
await client.connect(new StdioClientTransport({command:process.execPath,args:[fileURLToPath(new URL('../../upstream/cozyclay/mcp/server.mjs',import.meta.url))],env:{...process.env,COZYCLAY_PROJECT_ROOT:fileURLToPath(new URL('.',import.meta.url))},stderr:'pipe'}));
try {
  const catalog = await client.listTools();
  await new Promise(resolve=>setTimeout(resolve,4000));
  const status = await client.callTool({name:'live_status',arguments:{}});
  const report = {date:new Date().toISOString(),toolCount:catalog.tools.length,status,results:[]};
  console.log('LIVE',JSON.stringify(status));
  if (!status.content?.some(c=>c.type==='text' && c.text.includes('Live editor connected.'))) throw new Error('Open the Studio before running this demo.');
  for (const [name,args] of [
    ['frame_shot',{size:'wide shot',view:'front three-quarter',level:'eye',focal_mm:35}],
    ['describe_shot',{}],
    ['save_project',{path:'capability-demo.cclayproject',name:'CozyClay 能力演示',overwrite:true}],
  ]) {
    const result = await client.callTool({name,arguments:args});
    report.results.push({name,result});
    console.log(name,JSON.stringify(result));
    if(result.isError) throw new Error(`${name} failed`);
  }
  await writeFile(new URL('./mcp-verification.json',import.meta.url),JSON.stringify(report,null,2));
} finally { await client.close(); }
