// Check Supabase Storage Usage
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

const supabase = createClient(
  process.env.VITE_SUPABASE_URL,
  process.env.VITE_SUPABASE_ANON_KEY
);

async function checkUsage() {
  console.log('🔍 Checking Supabase storage usage...\n');
  
  const { data, error } = await supabase.storage
    .from('dept56-images')
    .list('', { limit: 1000 });
  
  if (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
  
  const totalSize = data.reduce((sum, file) => sum + (file.metadata?.size || 0), 0);
  const sizeMB = (totalSize / 1024 / 1024).toFixed(2);
  const sizeGB = (totalSize / 1024 / 1024 / 1024).toFixed(3);
  
  console.log('📦 Supabase Storage Usage:');
  console.log(`   Files: ${data.length}`);
  console.log(`   Total Size: ${sizeMB} MB (${sizeGB} GB)`);
  console.log(`\n💡 Firebase Free Tier Limits:`);
  console.log(`   Storage: 5 GB (you're using ${((sizeGB / 5) * 100).toFixed(1)}%)`);
  console.log(`   Download: 1 GB/day`);
  console.log(`\n✅ Recommendation:`);
  
  if (parseFloat(sizeGB) < 3) {
    console.log('   Your usage is well within Firebase free tier limits.');
    console.log('   Safe to migrate to Firebase Storage (requires billing enabled but won\'t be charged).');
  } else {
    console.log('   Consider keeping Supabase Storage to avoid any billing concerns.');
  }
  
  console.log(`\n📊 Supabase Storage Pricing (if you keep it):`);
  console.log(`   First 1 GB free, then $0.021/GB/month`);
  console.log(`   Your estimated cost: $${Math.max(0, (parseFloat(sizeGB) - 1) * 0.021).toFixed(2)}/month`);
}

checkUsage().catch(console.error);
