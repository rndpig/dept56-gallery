import { VercelRequest, VercelResponse } from '@vercel/node';
import { spawn } from 'child_process';
import path from 'path';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method Not Allowed', success: false });
    return;
  }

  try {
    const data = req.body;
    
    // In Vercel, we need to use the absolute path to the script
    const scriptPath = path.join(process.cwd(), 'scripts', 'bulk_import_scraper.py');
    
    return new Promise((resolve, reject) => {
      // Spawn Python script
      const python = spawn('python3', [scriptPath], {
        stdio: ['pipe', 'pipe', 'pipe'],
        cwd: process.cwd()
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
            res.status(200).json(result);
            resolve(result);
          } catch (e) {
            console.error('Parse error:', e, 'Output:', output);
            res.status(500).json({ error: 'Invalid response from scraper', success: false });
            resolve(null);
          }
        } else {
          console.error('Python script error. Code:', code, 'Error:', error);
          res.status(500).json({ error: 'Scraper execution failed', success: false, details: error });
          resolve(null);
        }
      });

      python.on('error', (err) => {
        console.error('Failed to start Python process:', err);
        res.status(500).json({ error: 'Failed to start scraper process', success: false });
        resolve(null);
      });
    });

  } catch (e) {
    console.error('Request processing error:', e);
    res.status(400).json({ error: 'Invalid request', success: false });
  }
}