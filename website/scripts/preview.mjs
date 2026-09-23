import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const docsDir = path.resolve(__dirname, '..', '..', 'docs');
const port = 3333;

Bun.serve({
  port,
  fetch(req) {
    const url = new URL(req.url);
    let pathname = decodeURIComponent(url.pathname);

    // Redirect root to /losna-cli/
    if (pathname === '/' || pathname === '') {
      return Response.redirect(`http://localhost:${port}/losna-cli/`, 302);
    }

    if (pathname.startsWith('/losna-cli')) {
      let relativePath = pathname.slice('/losna-cli'.length);
      if (relativePath === '' || relativePath === '/') {
        relativePath = '/index.html';
      }
      
      let fullPath = path.join(docsDir, relativePath);
      
      if (fs.existsSync(fullPath) && fs.statSync(fullPath).isDirectory()) {
        fullPath = path.join(fullPath, 'index.html');
      }

      if (fs.existsSync(fullPath) && fs.statSync(fullPath).isFile()) {
        return new Response(Bun.file(fullPath));
      }
    }

    const notFoundPage = path.join(docsDir, '404.html');
    if (fs.existsSync(notFoundPage)) {
      return new Response(Bun.file(notFoundPage), { status: 404, headers: { 'Content-Type': 'text/html' } });
    }
    return new Response('404 Not Found', { status: 404 });
  }
});

console.log(`\n🚀 Preview server running at http://localhost:${port}/losna-cli/\n`);
