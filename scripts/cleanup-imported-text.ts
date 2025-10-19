/**
 * Cleanup Utility: Remove "Imported from DOCX" text from database
 * 
 * This script connects to Supabase and removes the "Imported from DOCX" text
 * that was added during the initial data import.
 * 
 * Run this once to clean up your data.
 */

import { supabase } from '../src/lib/supabase';

async function cleanupImportedText() {
  console.log('🧹 Starting cleanup of "Imported from DOCX" text...\n');

  try {
    // 1. Fetch all houses
    console.log('📦 Fetching houses...');
    const { data: houses, error: housesError } = await supabase
      .from('houses')
      .select('*');

    if (housesError) throw housesError;
    console.log(`   Found ${houses?.length || 0} houses`);

    // 2. Fetch all accessories
    console.log('📦 Fetching accessories...');
    const { data: accessories, error: accessoriesError } = await supabase
      .from('accessories')
      .select('*');

    if (accessoriesError) throw accessoriesError;
    console.log(`   Found ${accessories?.length || 0} accessories\n`);

    let housesUpdated = 0;
    let accessoriesUpdated = 0;

    // 3. Clean houses
    if (houses) {
      for (const house of houses) {
        let needsUpdate = false;
        const updates: any = {};

        if (house.notes?.includes('Imported from DOCX')) {
          updates.notes = house.notes.replace(/Imported from DOCX/g, '').trim() || null;
          needsUpdate = true;
        }

        if (house.description?.includes('Imported from DOCX')) {
          updates.description = house.description.replace(/Imported from DOCX/g, '').trim() || null;
          needsUpdate = true;
        }

        if (needsUpdate) {
          const { error } = await supabase
            .from('houses')
            .update(updates)
            .eq('id', house.id);

          if (error) {
            console.error(`   ❌ Error updating house ${house.name}:`, error);
          } else {
            housesUpdated++;
            console.log(`   ✅ Cleaned: ${house.name}`);
          }
        }
      }
    }

    // 4. Clean accessories
    if (accessories) {
      for (const accessory of accessories) {
        let needsUpdate = false;
        const updates: any = {};

        if (accessory.notes?.includes('Imported from DOCX')) {
          updates.notes = accessory.notes.replace(/Imported from DOCX/g, '').trim() || null;
          needsUpdate = true;
        }

        if (accessory.description?.includes('Imported from DOCX')) {
          updates.description = accessory.description.replace(/Imported from DOCX/g, '').trim() || null;
          needsUpdate = true;
        }

        if (needsUpdate) {
          const { error } = await supabase
            .from('accessories')
            .update(updates)
            .eq('id', accessory.id);

          if (error) {
            console.error(`   ❌ Error updating accessory ${accessory.name}:`, error);
          } else {
            accessoriesUpdated++;
            console.log(`   ✅ Cleaned: ${accessory.name}`);
          }
        }
      }
    }

    console.log('\n✨ Cleanup complete!');
    console.log(`   Houses updated: ${housesUpdated}`);
    console.log(`   Accessories updated: ${accessoriesUpdated}`);
    console.log(`   Total records cleaned: ${housesUpdated + accessoriesUpdated}`);

  } catch (error) {
    console.error('❌ Error during cleanup:', error);
  }
}

// Run the cleanup
cleanupImportedText();
