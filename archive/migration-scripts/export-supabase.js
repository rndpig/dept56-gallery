// Export all data from Supabase
import { createClient } from '@supabase/supabase-js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.join(__dirname, '..', '.env.local') });

const supabase = createClient(
  process.env.VITE_SUPABASE_URL,
  process.env.VITE_SUPABASE_ANON_KEY
);

async function exportTable(tableName) {
  console.log(`\n📦 Exporting ${tableName}...`);
  
  let allData = [];
  let from = 0;
  const batchSize = 1000;
  
  while (true) {
    const { data, error } = await supabase
      .from(tableName)
      .select('*')
      .range(from, from + batchSize - 1)
      .order('created_at', { ascending: true });
    
    if (error) {
      console.error(`   ❌ Error: ${error.message}`);
      throw error;
    }
    
    if (!data || data.length === 0) break;
    
    allData = allData.concat(data);
    console.log(`   ✓ Fetched ${data.length} records (total: ${allData.length})`);
    
    if (data.length < batchSize) break;
    from += batchSize;
  }
  
  console.log(`   ✅ Exported ${allData.length} records from ${tableName}`);
  return allData;
}

async function exportAll() {
  console.log('🚀 Starting Supabase data export...\n');
  console.log('=' .repeat(60));
  
  const exportData = {
    exportedAt: new Date().toISOString(),
    tables: {}
  };
  
  // Define tables to export in order (respecting dependencies)
  const tables = [
    'houses',
    'accessories',
    'collections',
    'tags',
    'house_accessory_links',
    'house_collections',
    'accessory_collections',
    'house_tags',
    'accessory_tags'
  ];
  
  try {
    for (const table of tables) {
      exportData.tables[table] = await exportTable(table);
    }
    
    // Save to JSON file
    const outputDir = path.join(__dirname, 'migration-data');
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }
    
    const outputFile = path.join(outputDir, 'supabase-export.json');
    fs.writeFileSync(outputFile, JSON.stringify(exportData, null, 2));
    
    console.log('\n' + '=' .repeat(60));
    console.log('✅ EXPORT COMPLETE!');
    console.log('=' .repeat(60));
    console.log('\n📊 Summary:');
    
    let totalRecords = 0;
    for (const [table, data] of Object.entries(exportData.tables)) {
      const count = data.length;
      totalRecords += count;
      console.log(`   ${table.padEnd(30)} ${count.toString().padStart(6)} records`);
    }
    
    console.log(`\n   ${'TOTAL'.padEnd(30)} ${totalRecords.toString().padStart(6)} records`);
    console.log(`\n📁 Exported to: ${outputFile}`);
    console.log(`📦 File size: ${(fs.statSync(outputFile).size / 1024 / 1024).toFixed(2)} MB`);
    console.log('\n✨ Ready for import to Firestore!');
    
  } catch (error) {
    console.error('\n❌ Export failed:', error);
    process.exit(1);
  }
}

exportAll();
