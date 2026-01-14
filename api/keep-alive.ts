import { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // This endpoint is completely public for monitoring services
  // It only reads one record from the database, so it's safe
  
  try {
    const supabaseUrl = process.env.VITE_SUPABASE_URL;
    const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY;

    if (!supabaseUrl || !supabaseKey) {
      return res.status(500).json({
        success: false,
        error: 'Supabase credentials not configured',
        timestamp: new Date().toISOString()
      });
    }

    // Make a simple query to the houses table to keep the database active
    const response = await fetch(`${supabaseUrl}/rest/v1/houses?limit=1`, {
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
      },
    });

    const data = await response.json();

    if (response.ok) {
      return res.status(200).json({
        success: true,
        message: 'Supabase database pinged successfully',
        status: response.status,
        recordCount: Array.isArray(data) ? data.length : 0,
        timestamp: new Date().toISOString(),
        nextRun: 'In 3 days'
      });
    } else {
      return res.status(200).json({
        success: false,
        message: 'Supabase query failed but endpoint is running',
        status: response.status,
        error: data,
        timestamp: new Date().toISOString()
      });
    }
  } catch (error) {
    console.error('Keep-alive error:', error);
    return res.status(200).json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString()
    });
  }
}
