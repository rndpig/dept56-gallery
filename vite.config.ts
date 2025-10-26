import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { spawn } from 'child_process'
import { createReadStream, createWriteStream } from 'fs'
import path from 'path'

// Simple API handler for import functionality
function createImportApiHandler() {
  return {
    name: 'import-api',
    configureServer(server: any) {
      server.middlewares.use('/api/import-houses', async (req: any, res: any, next: any) => {
        if (req.method !== 'POST') {
          res.statusCode = 405;
          res.end('Method Not Allowed');
          return;
        }

        let body = '';
        req.on('data', (chunk: any) => body += chunk);
        req.on('end', async () => {
          try {
            const data = JSON.parse(body);
            
            // Spawn Python script
            const scriptPath = path.join(process.cwd(), 'scripts', 'bulk_import_scraper.py');
            const python = spawn('python', [scriptPath], {
              stdio: ['pipe', 'pipe', 'pipe']
            });

            // Send input data to Python script
            python.stdin.write(JSON.stringify(data));
            python.stdin.end();

            let output = '';
            let error = '';
            
            python.stdout.on('data', (data) => {
              output += data.toString();
            });
            
            python.stderr.on('data', (data) => {
              error += data.toString();
            });

            python.on('close', (code) => {
              if (code === 0) {
                try {
                  const result = JSON.parse(output);
                  res.setHeader('Content-Type', 'application/json');
                  res.end(JSON.stringify(result));
                } catch (e) {
                  res.statusCode = 500;
                  res.end(JSON.stringify({ error: 'Invalid response from scraper', success: false }));
                }
              } else {
                console.error('Python script error:', error);
                res.statusCode = 500;
                res.end(JSON.stringify({ error: 'Scraper execution failed', success: false }));
              }
            });

          } catch (e) {
            res.statusCode = 400;
            res.end(JSON.stringify({ error: 'Invalid JSON', success: false }));
          }
        });
      });
    }
  };
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), createImportApiHandler()],
  server: {
    port: 3000,
  },
})
