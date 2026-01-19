// Import Supabase data to Firestore with field name transformations
import admin from 'firebase-admin';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Initialize Firebase Admin
const serviceAccountPath = path.join(__dirname, '..', 'firebase-service-account.json');
if (!fs.existsSync(serviceAccountPath)) {
  console.error('❌ firebase-service-account.json not found');
  console.error('Please download it from Firebase Console → Project Settings → Service Accounts');
  process.exit(1);
}

const serviceAccount = JSON.parse(fs.readFileSync(serviceAccountPath, 'utf8'));
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  projectId: 'dept56-gallery'
});

const db = admin.firestore();

// Field name mapping (snake_case → camelCase)
const FIELD_MAPPINGS = {
  user_id: 'userId',
  photo_url: 'photoUrl',
  retired_year: 'retiredYear',
  intro_year: 'introYear',
  purchased_year: 'purchasedYear',
  purchased_date: 'purchasedDate',
  created_at: 'createdAt',
  updated_at: 'updatedAt',
  house_id: 'houseId',
  accessory_id: 'accessoryId',
  collection_id: 'collectionId',
  tag_id: 'tagId',
  confidence_score: 'confidenceScore'
};

// Collection name mapping (snake_case → camelCase)
const COLLECTION_MAPPINGS = {
  house_accessory_links: 'houseAccessoryLinks',
  house_collections: 'houseCollections',
  accessory_collections: 'accessoryCollections',
  house_tags: 'houseTags',
  accessory_tags: 'accessoryTags'
};

// Transform field names from snake_case to camelCase
function transformRecord(record) {
  const transformed = {};
  
  for (const [key, value] of Object.entries(record)) {
    // Map field name
    const newKey = FIELD_MAPPINGS[key] || key;
    
    // Convert date strings to Firestore Timestamps
    if ((key === 'created_at' || key === 'updated_at' || key === 'purchased_date') && value) {
      transformed[newKey] = admin.firestore.Timestamp.fromDate(new Date(value));
    } else {
      transformed[newKey] = value;
    }
  }
  
  return transformed;
}

async function importCollection(collectionName, records) {
  console.log(`\n📥 Importing ${collectionName}...`);
  
  if (!records || records.length === 0) {
    console.log(`   ⏭️  No records to import`);
    return { imported: 0, failed: 0 };
  }
  
  const targetCollection = COLLECTION_MAPPINGS[collectionName] || collectionName;
  const batch = db.batch();
  let batchCount = 0;
  let imported = 0;
  let failed = 0;
  const batchSize = 500; // Firestore batch limit
  
  for (const record of records) {
    try {
      const docId = record.id;
      const transformedData = transformRecord(record);
      
      // Remove 'id' field as it's stored as document ID
      delete transformedData.id;
      
      const docRef = db.collection(targetCollection).doc(docId);
      batch.set(docRef, transformedData);
      
      batchCount++;
      
      // Commit batch when it reaches limit
      if (batchCount === batchSize) {
        await batch.commit();
        imported += batchCount;
        console.log(`   ✓ Committed batch of ${batchCount} (total: ${imported})`);
        batchCount = 0;
      }
    } catch (error) {
      console.error(`   ❌ Error importing record ${record.id}:`, error.message);
      failed++;
    }
  }
  
  // Commit remaining records
  if (batchCount > 0) {
    await batch.commit();
    imported += batchCount;
    console.log(`   ✓ Committed final batch of ${batchCount}`);
  }
  
  console.log(`   ✅ Imported ${imported} records to ${targetCollection}`);
  
  if (failed > 0) {
    console.log(`   ⚠️  Failed: ${failed} records`);
  }
  
  return { imported, failed };
}

async function importAll() {
  console.log('🚀 Starting Firestore import...\n');
  console.log('=' .repeat(60));
  
  // Load exported data
  const inputFile = path.join(__dirname, 'migration-data', 'supabase-export.json');
  
  if (!fs.existsSync(inputFile)) {
    console.error('❌ Export file not found:', inputFile);
    console.error('Please run export-supabase.js first');
    process.exit(1);
  }
  
  const exportData = JSON.parse(fs.readFileSync(inputFile, 'utf8'));
  console.log(`📂 Loaded export from: ${exportData.exportedAt}\n`);
  
  // Import in order (respecting dependencies)
  const importOrder = [
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
  
  const stats = {
    totalImported: 0,
    totalFailed: 0,
    collections: {}
  };
  
  try {
    for (const tableName of importOrder) {
      const records = exportData.tables[tableName];
      const result = await importCollection(tableName, records);
      
      stats.totalImported += result.imported;
      stats.totalFailed += result.failed;
      stats.collections[tableName] = result;
    }
    
    console.log('\n' + '=' .repeat(60));
    console.log('✅ IMPORT COMPLETE!');
    console.log('=' .repeat(60));
    console.log('\n📊 Summary:');
    
    for (const [table, result] of Object.entries(stats.collections)) {
      const targetName = COLLECTION_MAPPINGS[table] || table;
      console.log(`   ${targetName.padEnd(30)} ${result.imported.toString().padStart(6)} imported`);
    }
    
    console.log(`\n   ${'TOTAL'.padEnd(30)} ${stats.totalImported.toString().padStart(6)} records`);
    
    if (stats.totalFailed > 0) {
      console.log(`   ${'FAILED'.padEnd(30)} ${stats.totalFailed.toString().padStart(6)} records`);
    }
    
    console.log('\n✨ Data migration to Firestore complete!');
    console.log('💡 Next: Run verify-migration.js to validate the migration');
    
    process.exit(0);
    
  } catch (error) {
    console.error('\n❌ Import failed:', error);
    process.exit(1);
  }
}

importAll();
