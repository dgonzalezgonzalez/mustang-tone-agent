import {Client} from '@modelcontextprotocol/sdk/client/index.js';
import {StreamableHTTPClientTransport} from '@modelcontextprotocol/sdk/client/streamableHttp.js';
import {readFileSync} from 'node:fs';
import {join} from 'node:path';

const token = readFileSync(join(process.env.LOCALAPPDATA,'MustangToneAgent','access.token'),'utf8').trim();
const client = new Client({name:'mustang-independent-js-client',version:'0.1.0'});
const transport = new StreamableHTTPClientTransport(new URL('http://127.0.0.1:8765/mcp'),{
  requestInit:{headers:{Authorization:'Bearer '+token}}
});
try {
  await client.connect(transport);
  const tools = await client.listTools();
  const result = await client.callTool({name:'get_capabilities',arguments:{}});
  if(result.isError || tools.tools.length<15) throw new Error('MCP verification failed');
  console.log(`Independent JavaScript client: ${tools.tools.length} tools; capability call passed`);
} finally {await client.close();}
