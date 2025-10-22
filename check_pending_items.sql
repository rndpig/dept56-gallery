-- Check what's currently pending review
SELECT 
  id,
  original_house_id,
  name,
  item_number as sku,
  intro_year,
  discovered_series,
  overall_confidence_score,
  created_at
FROM staged_houses
WHERE status = 'pending'
ORDER BY overall_confidence_score DESC;

-- Also check if any pending items have NULL original_house_id (new items)
SELECT 
  COUNT(*) as new_items_count,
  COUNT(CASE WHEN original_house_id IS NULL THEN 1 END) as items_without_match
FROM staged_houses
WHERE status = 'pending';
