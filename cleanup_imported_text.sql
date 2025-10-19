-- Clean up "Imported from DOCX" text from the database
-- Run this in Supabase SQL Editor

-- Remove from houses table - notes field
UPDATE houses 
SET notes = TRIM(REPLACE(notes, 'Imported from DOCX', ''))
WHERE notes LIKE '%Imported from DOCX%';

-- Remove from houses table - description field
UPDATE houses 
SET description = TRIM(REPLACE(description, 'Imported from DOCX', ''))
WHERE description LIKE '%Imported from DOCX%';

-- Remove from accessories table - notes field
UPDATE accessories 
SET notes = TRIM(REPLACE(notes, 'Imported from DOCX', ''))
WHERE notes LIKE '%Imported from DOCX%';

-- Remove from accessories table - description field
UPDATE accessories 
SET description = TRIM(REPLACE(description, 'Imported from DOCX', ''))
WHERE description LIKE '%Imported from DOCX%';

-- Clean up any resulting empty strings (set to NULL for cleaner data)
UPDATE houses SET notes = NULL WHERE notes = '' OR notes IS NULL OR TRIM(notes) = '';
UPDATE houses SET description = NULL WHERE description = '' OR description IS NULL OR TRIM(description) = '';
UPDATE accessories SET notes = NULL WHERE notes = '' OR notes IS NULL OR TRIM(notes) = '';
UPDATE accessories SET description = NULL WHERE description = '' OR description IS NULL OR TRIM(description) = '';

-- Verify cleanup
SELECT 'Houses with "Imported from DOCX" in notes' as check_type, COUNT(*) as count FROM houses WHERE notes LIKE '%Imported from DOCX%'
UNION ALL
SELECT 'Houses with "Imported from DOCX" in description', COUNT(*) FROM houses WHERE description LIKE '%Imported from DOCX%'
UNION ALL
SELECT 'Accessories with "Imported from DOCX" in notes', COUNT(*) FROM accessories WHERE notes LIKE '%Imported from DOCX%'
UNION ALL
SELECT 'Accessories with "Imported from DOCX" in description', COUNT(*) FROM accessories WHERE description LIKE '%Imported from DOCX%';
