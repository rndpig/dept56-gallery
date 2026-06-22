// Verify data migration from Supabase to Firestore
import { createClient } from '@supabase/supabase-js';
import admin from 'firebase-admin';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.join(__dirname, '..', '.env.local') });

// Initialize Supabase
const supabase = createClient(
  process.env.VITE_SUPABASE_URL,
  process.env.VITE_SUPABASE_ANON_KEY
);

// Initialize Firebase Admin
const serviceAccountPath = path.join(__dirname, '..', 'firebase-service-account.json');
if (!fs.existsSync(serviceAccountPath)) {
  console.error('❌ firebase-service-account.json not found');
  process.exit(1);
}

const serviceAccount = JSON.parse(fs.readFileSync(serviceAccountPath, 'utf8'));
if (!admin.apps.length) {
  admin.initializeApp({
    credential: admin.credential.cert(serviceAccount),
    projectId: 'dept56-gallery'
  });
}

const db = admin.firestore();

// Collection mappings
const COLLECTION_MAPPINGS = {
  house_accessory_links: 'houseAccessoryLinks',
  house_collections: 'houseCollections',
  accessory_collections: 'accessoryCollections',
  house_tags: 'houseTags',
  accessory_tags: 'accessoryTags'
};

async function countSupabaseTable(tableName) {
  const { count, error } = await supabase
    .from(tableName)
    .select('*', { count: 'exact', head: true });
  
  if (error) throw error;
  return count || 0;
}

async function countFirestoreCollection(collectionName) {
  const snapshot = await db.collection(collectionName).count().get();
  return snapshot.data().count;
}

async function verifyAll() {
  console.log('🔍 Verifying data migration...\n');
  console.log('=' .repeat(60));
  
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
  
  const results = [];
  let allMatch = true;
  
  for (const table of tables) {
    const firestoreCollection = COLLECTION_MAPPINGS[table] || table;
    
    try {
      console.log(`\n📊 ${table}:`);
      const supabaseCount = await countSupabaseTable(table);
      const firestoreCount = await countFirestoreCollection(firestoreCollection);
      
      const match = supabaseCount === firestoreCount;
      if (!match) allMatch = false;
      
      const status = match ? '✅' : '❌';
      console.log(`   Supabase:  ${supabaseCount.toString().padStart(6)} records`);
      console.log(`   Firestore: ${firestoreCount.toString().padStart(6)} records`);
      console.log(`   ${status} ${match ? 'Match!' : 'Mismatch!'}`);
      
      results.push({
        table,
        firestoreCollection,
        supabaseCount,
        firestoreCount,
        match
      });
      
    } catch (error) {
      console.error(`   ❌ Error: ${error.message}`);
      results.push({
        table,
        firestoreCollection,
        error: error.message,
        match: false
      });
      allMatch = false;
    }
  }
  
  console.log('\n' + '=' .repeat(60));
  
  if (allMatch) {
    console.log('✅ VERIFICATION PASSED!');
    console.log('=' .repeat(60));
    console.log('\n🎉 All record counts match between Supabase and Firestore!');
    console.log('\n📊 Summary:');
    
    let totalSupabase = 0;
    let totalFirestore = 0;
    
    for (const result of results) {
      if (!result.error) {
        totalSupabase += result.supabaseCount;
        totalFirestore += result.firestoreCount;
        console.log(`   ${result.firestoreCollection.padEnd(30)} ${result.firestoreCount.toString().padStart(6)} ✓`);
      }
    }
    
    console.log(`\n   ${'TOTAL'.padEnd(30)} ${totalFirestore.toString().padStart(6)} records`);
    console.log('\n✨ Migration verified successfully!');
    console.log('💡 Next: Test the app with Firestore data');
    
  } else {
    console.log('❌ VERIFICATION FAILED!');
    console.log('=' .repeat(60));
    console.log('\n⚠️  Some record counts do not match:\n');
    
    for (const result of results) {
      if (!result.match) {
        if (result.error) {
          console.log(`   ${result.table}: Error - ${result.error}`);
        } else {
          const diff = result.firestoreCount - result.supabaseCount;
          console.log(`   ${result.table}: Firestore has ${diff > 0 ? '+' : ''}${diff} records`);
        }
      }
    }
    
    console.log('\n💡 Check the import logs for errors');
  }
  
  process.exit(allMatch ? 0 : 1);
}

verifyAll().catch((error) => {
  console.error('\n❌ Verification failed:', error);
  process.exit(1);
});
