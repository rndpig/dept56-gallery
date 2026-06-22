// Storage Migration Script - Supabase → Firebase Storage
// Run this AFTER Phase 5 (data migration) is complete
// This script downloads images from Supabase Storage and uploads to Firebase Storage

import { createClient } from '@supabase/supabase-js';
import admin from 'firebase-admin';
import fs from 'fs';
import path from 'path';
import https from 'https';
import http from 'http';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables
dotenv.config({ path: path.join(__dirname, '..', '.env.local') });

// Check for required environment variables
if (!process.env.VITE_SUPABASE_URL || !process.env.VITE_SUPABASE_ANON_KEY) {
  console.error('❌ Missing Supabase environment variables');
  console.error('Please ensure VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are set');
  process.exit(1);
}

// Initialize Supabase
const supabase = createClient(
  process.env.VITE_SUPABASE_URL,
  process.env.VITE_SUPABASE_ANON_KEY
);

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
  storageBucket: 'dept56-gallery.firebasestorage.app'
});

const bucket = admin.storage().bucket();
const db = admin.firestore();

// Helper: Download file from URL
function downloadFile(url, filepath) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(filepath);
    const protocol = url.startsWith('https') ? https : http;
    
    protocol.get(url, (response) => {
      if (response.statusCode !== 200) {
        reject(new Error(`Failed to download: ${response.statusCode}`));
        return;
      }
      
      response.pipe(file);
      file.on('finish', () => {
        file.close();
        resolve();
      });
    }).on('error', (err) => {
      fs.unlink(filepath, () => {});
      reject(err);
    });
  });
}

// Helper: Get content type from filename
function getContentType(filename) {
  const ext = path.extname(filename).toLowerCase();
  const types = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.svg': 'image/svg+xml'
  };
  return types[ext] || 'image/jpeg';
}

async function migrateStorage() {
  console.log('🔄 Starting storage migration from Supabase to Firebase...\n');
  
  const stats = {
    housesProcessed: 0,
    housesWithPhotos: 0,
    housesMigrated: 0,
    housesSkipped: 0,
    housesFailed: 0,
    accessoriesProcessed: 0,
    accessoriesWithPhotos: 0,
    accessoriesMigrated: 0,
    accessoriesSkipped: 0,
    accessoriesFailed: 0
  };
  
  const urlMapping = {};
  
  // Create temp directory for downloads
  const tempDir = path.join(__dirname, 'temp-images');
  if (!fs.existsSync(tempDir)) {
    fs.mkdirSync(tempDir, { recursive: true });
  }
  
  console.log('📦 Step 1: Fetching houses from Firestore...');
  const housesSnap = await db.collection('houses').get();
  console.log(`   Found ${housesSnap.size} houses\n`);
  
  console.log('🏠 Step 2: Migrating house photos...');
  for (const houseDoc of housesSnap.docs) {
    stats.housesProcessed++;
    const house = { id: houseDoc.id, ...houseDoc.data() };
    
    // Skip if no photo or already migrated
    if (!house.photoUrl) {
      stats.housesSkipped++;
      continue;
    }
    
    if (!house.photoUrl.includes('supabase')) {
      console.log(`   ⏭️  Skipping ${house.name} (already migrated)`);
      stats.housesSkipped++;
      continue;
    }
    
    stats.housesWithPhotos++;
    
    try {
      console.log(`   📸 Migrating: ${house.name}`);
      
      // Extract filename from URL
      const urlParts = house.photoUrl.split('/');
      const filename = urlParts[urlParts.length - 1];
      const tempPath = path.join(tempDir, filename);
      
      // Download from Supabase
      console.log(`      ⬇️  Downloading...`);
      await downloadFile(house.photoUrl, tempPath);
      
      // Upload to Firebase Storage
      console.log(`      ⬆️  Uploading to Firebase...`);
      const firebasePath = `images/houses/${house.id}-${filename}`;
      await bucket.upload(tempPath, {
        destination: firebasePath,
        metadata: {
          contentType: getContentType(filename),
          metadata: {
            houseId: house.id,
            houseName: house.name,
            migratedFrom: 'supabase',
            migratedAt: new Date().toISOString()
          }
        }
      });
      
      // Make file publicly accessible
      const file = bucket.file(firebasePath);
      await file.makePublic();
      
      // Get public URL
      const publicUrl = `https://storage.googleapis.com/${bucket.name}/${firebasePath}`;
      
      // Store mapping
      urlMapping[house.photoUrl] = publicUrl;
      
      // Update Firestore document
      console.log(`      💾 Updating Firestore...`);
      await db.collection('houses').doc(house.id).update({
        photoUrl: publicUrl
      });
      
      // Clean up temp file
      fs.unlinkSync(tempPath);
      
      stats.housesMigrated++;
      console.log(`      ✅ Success!\n`);
      
    } catch (error) {
      stats.housesFailed++;
      console.error(`      ❌ Error: ${error.message}\n`);
      
      // Clean up temp file if exists
      const tempPath = path.join(tempDir, house.photoUrl.split('/').pop());
      if (fs.existsSync(tempPath)) {
        fs.unlinkSync(tempPath);
      }
    }
  }
  
  console.log('\n📦 Step 3: Fetching accessories from Firestore...');
  const accessoriesSnap = await db.collection('accessories').get();
  console.log(`   Found ${accessoriesSnap.size} accessories\n`);
  
  console.log('🎨 Step 4: Migrating accessory photos...');
  for (const accessoryDoc of accessoriesSnap.docs) {
    stats.accessoriesProcessed++;
    const accessory = { id: accessoryDoc.id, ...accessoryDoc.data() };
    
    // Skip if no photo or already migrated
    if (!accessory.photoUrl) {
      stats.accessoriesSkipped++;
      continue;
    }
    
    if (!accessory.photoUrl.includes('supabase')) {
      console.log(`   ⏭️  Skipping ${accessory.name} (already migrated)`);
      stats.accessoriesSkipped++;
      continue;
    }
    
    stats.accessoriesWithPhotos++;
    
    try {
      console.log(`   📸 Migrating: ${accessory.name}`);
      
      const urlParts = accessory.photoUrl.split('/');
      const filename = urlParts[urlParts.length - 1];
      const tempPath = path.join(tempDir, filename);
      
      console.log(`      ⬇️  Downloading...`);
      await downloadFile(accessory.photoUrl, tempPath);
      
      console.log(`      ⬆️  Uploading to Firebase...`);
      const firebasePath = `images/accessories/${accessory.id}-${filename}`;
      await bucket.upload(tempPath, {
        destination: firebasePath,
        metadata: {
          contentType: getContentType(filename),
          metadata: {
            accessoryId: accessory.id,
            accessoryName: accessory.name,
            migratedFrom: 'supabase',
            migratedAt: new Date().toISOString()
          }
        }
      });
      
      const file = bucket.file(firebasePath);
      await file.makePublic();
      
      const publicUrl = `https://storage.googleapis.com/${bucket.name}/${firebasePath}`;
      
      urlMapping[accessory.photoUrl] = publicUrl;
      
      console.log(`      💾 Updating Firestore...`);
      await db.collection('accessories').doc(accessory.id).update({
        photoUrl: publicUrl
      });
      
      fs.unlinkSync(tempPath);
      
      stats.accessoriesMigrated++;
      console.log(`      ✅ Success!\n`);
      
    } catch (error) {
      stats.accessoriesFailed++;
      console.error(`      ❌ Error: ${error.message}\n`);
      
      const tempPath = path.join(tempDir, accessory.photoUrl.split('/').pop());
      if (fs.existsSync(tempPath)) {
        fs.unlinkSync(tempPath);
      }
    }
  }
  
  // Save URL mapping for reference
  const mappingPath = path.join(__dirname, 'url-mapping.json');
  fs.writeFileSync(mappingPath, JSON.stringify(urlMapping, null, 2));
  
  // Clean up temp directory
  if (fs.existsSync(tempDir)) {
    fs.rmdirSync(tempDir, { recursive: true });
  }
  
  // Print summary
  console.log('\n' + '='.repeat(60));
  console.log('✅ STORAGE MIGRATION COMPLETE!');
  console.log('='.repeat(60));
  console.log('\n📊 HOUSES:');
  console.log(`   Total Processed:    ${stats.housesProcessed}`);
  console.log(`   With Photos:        ${stats.housesWithPhotos}`);
  console.log(`   Successfully Migrated: ${stats.housesMigrated}`);
  console.log(`   Skipped:            ${stats.housesSkipped}`);
  console.log(`   Failed:             ${stats.housesFailed}`);
  
  console.log('\n📊 ACCESSORIES:');
  console.log(`   Total Processed:    ${stats.accessoriesProcessed}`);
  console.log(`   With Photos:        ${stats.accessoriesWithPhotos}`);
  console.log(`   Successfully Migrated: ${stats.accessoriesMigrated}`);
  console.log(`   Skipped:            ${stats.accessoriesSkipped}`);
  console.log(`   Failed:             ${stats.accessoriesFailed}`);
  
  console.log('\n📝 Files Created:');
  console.log(`   URL Mapping: ${mappingPath}`);
  
  console.log('\n🎉 Migration complete! All images are now in Firebase Storage.');
  console.log('💡 Next: Test image loading in the app\n');
  
  // Exit successfully
  process.exit(0);
}

// Run migration with error handling
migrateStorage().catch((error) => {
  console.error('\n❌ Fatal error during migration:');
  console.error(error);
  process.exit(1);
});
