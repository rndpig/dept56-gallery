/**
 * Data Review Component for Department 56 Browser
 * Admin-only interface for reviewing scraped product data
 */

import { useEffect, useState } from "react";
import { supabase } from "./lib/supabase";

interface StagedHouse {
  id: string;
  original_house_id: string | null;
  item_number: string;
  name: string;
  intro_year: number | null;
  retire_year: number | null;
  description: string | null;
  dimensions: string | null;
  primary_image_url: string | null;
  additional_images: string[];
  dept56_official_url: string | null;
  dept56_retired_url: string | null;
  replacements_url: string | null;
  discovered_series: string | null;
  discovered_collection: string | null;
  name_match_score: number;
  details_confidence_score: number;
  overall_confidence_score: number;
  status: string;
  created_at: string;
}

interface OriginalHouse {
  id: string;
  name: string;
  year: number | null;
  sku: string | null;
  notes: string | null;
  photo_url: string | null;
}

interface ApprovalHistory {
  id: string;
  staged_house_id: string;
  original_house_id: string | null;
  original_name: string | null;
  original_year: number | null;
  original_sku: string | null;
  original_notes: string | null;
  original_photo_url: string | null;
  new_name: string | null;
  new_year: number | null;
  new_sku: string | null;
  new_notes: string | null;
  new_photo_url: string | null;
  approved_by: string;
  approved_at: string;
  undone_at: string | null;
  undone_by: string | null;
}

export function DataReviewTab() {
  const [stagedHouses, setStagedHouses] = useState<StagedHouse[]>([]);
  const [originalHouses, setOriginalHouses] = useState<Map<string, OriginalHouse>>(new Map());
  const [loading, setLoading] = useState(true);
  const [processingIds, setProcessingIds] = useState<Set<string>>(new Set());
  const [viewMode, setViewMode] = useState<'all' | 'high' | 'medium' | 'low'>('all');
  const [showOnlyChanges, setShowOnlyChanges] = useState(false);
  const [recentApprovals, setRecentApprovals] = useState<ApprovalHistory[]>([]);
  const [showRecentApprovals, setShowRecentApprovals] = useState(false);

  // Load staged houses
  useEffect(() => {
    loadStagedHouses();
    loadRecentApprovals();
  }, []);

  async function loadRecentApprovals() {
    try {
      // Only show approvals from the last 24 hours
      const oneDayAgo = new Date();
      oneDayAgo.setDate(oneDayAgo.getDate() - 1);

      const { data, error } = await supabase
        .from("approval_history")
        .select("*")
        .is("undone_at", null)
        .gte("approved_at", oneDayAgo.toISOString())
        .order("approved_at", { ascending: false })
        .limit(10);

      if (error) throw error;
      setRecentApprovals(data || []);
    } catch (err) {
      console.error("Error loading approval history:", err);
    }
  }

  async function loadStagedHouses() {
    try {
      setLoading(true);
      
      console.log('🔍 DataReviewTab: Loading staged houses...');
      console.log('Current user:', (await supabase.auth.getUser()).data.user);
      
      // Get pending staged houses
      const { data: staged, error } = await supabase
        .from("staged_houses")
        .select("*")
        .eq("status", "pending")
        .order("overall_confidence_score", { ascending: false });

      console.log('Query result:', { staged, error });
      
      if (error) throw error;

      setStagedHouses(staged || []);

      // Load original houses for comparison
      const originalIds = (staged || [])
        .map(s => s.original_house_id)
        .filter(Boolean) as string[];

      if (originalIds.length > 0) {
        const { data: originals, error: origError } = await supabase
          .from("houses")
          .select("id, name, year, sku, notes, photo_url")
          .in("id", originalIds);

        if (origError) throw origError;

        const map = new Map<string, OriginalHouse>();
        (originals || []).forEach(h => map.set(h.id, h));
        setOriginalHouses(map);
      }
    } catch (err) {
      console.error("Error loading staged houses:", err);
      alert("Failed to load staged data");
    } finally {
      setLoading(false);
    }
  }

  async function handleApprove(item: StagedHouse) {
    if (!confirm(`Approve and apply changes for "${item.name}"?`)) return;

    setProcessingIds(prev => new Set(prev).add(item.id));

    try {
      console.log("🚀 Starting approval for:", item.name);
      await applyApproval(item);
      console.log("✅ Approval successful, reloading data...");
      await loadStagedHouses();
      await loadRecentApprovals();
      alert(`✅ Successfully approved "${item.name}"!`);
    } catch (err: any) {
      console.error("❌ Error approving item:", err);
      const errorMessage = err?.message || err?.toString() || "Unknown error";
      alert(`❌ Failed to approve item:\n\n${errorMessage}\n\nCheck browser console for details.`);
    } finally {
      setProcessingIds(prev => {
        const next = new Set(prev);
        next.delete(item.id);
        return next;
      });
    }
  }

  async function applyApproval(item: StagedHouse) {
    console.log("🔄 Starting approval process for:", item.name);
    console.log("📋 Item details:", { 
      id: item.id, 
      original_house_id: item.original_house_id,
      name: item.name,
      intro_year: item.intro_year 
    });

    if (item.original_house_id) {
      // Step 1: Get original values for backup
      console.log("📖 Step 1: Fetching original house data...");
      const { data: originalHouse, error: fetchError } = await supabase
        .from("houses")
        .select("name, year, sku, notes, photo_url")
        .eq("id", item.original_house_id)
        .single();

      console.log("📖 Original house fetch result:", { data: originalHouse, error: fetchError });
      if (fetchError) {
        console.error("❌ Failed to fetch original house:", fetchError);
        throw fetchError;
      }

      const userEmail = (await supabase.auth.getUser()).data.user?.email || "unknown";
      const newNotes = item.description ? 
        `${item.description}\n\nSeries: ${item.discovered_series || 'Unknown'}\nRetired: ${item.retire_year || 'Unknown'}` : 
        null;

      // Step 2: Create backup in approval_history
      console.log("💾 Step 2: Creating backup in approval_history...");
      const backupData = {
        staged_house_id: item.id,
        original_house_id: item.original_house_id,
        original_name: originalHouse.name,
        original_year: originalHouse.year,
        original_sku: originalHouse.sku,
        original_notes: originalHouse.notes,
        original_photo_url: originalHouse.photo_url,
        new_name: item.name,
        new_year: item.intro_year,
        new_sku: item.item_number,
        new_notes: newNotes,
        new_photo_url: item.primary_image_url,
        approved_by: userEmail,
      };
      console.log("💾 Backup data:", backupData);

      const { data: historyData, error: historyError } = await supabase
        .from("approval_history")
        .insert(backupData)
        .select();

      console.log("💾 Backup result:", { data: historyData, error: historyError });
      if (historyError) {
        console.error("❌ Failed to create backup:", historyError);
        throw new Error(`Backup failed: ${historyError.message}`);
      }
      console.log("✅ Backup created successfully!");

      // Step 3: Update existing house
      console.log("📝 Step 3: Updating houses table...");
      const updateData = {
        name: item.name,
        year: item.intro_year,
        sku: item.item_number,
        notes: newNotes,
        photo_url: item.primary_image_url,
      };
      console.log("📝 Update data:", updateData);

      const { data: updateResult, error: updateError } = await supabase
        .from("houses")
        .update(updateData)
        .eq("id", item.original_house_id)
        .select();

      console.log("📝 Update result:", { data: updateResult, error: updateError });
      if (updateError) {
        console.error("❌ Failed to update house:", updateError);
        throw new Error(`Update failed: ${updateError.message}`);
      }
      console.log("✅ House updated successfully!");
    } else {
      // Create new house (if implementing new imports)
      throw new Error("New house import not yet implemented");
    }

    // Step 4: Mark as approved
    console.log("✔️ Step 4: Marking staged_houses as approved...");
    const { data: statusData, error: statusError } = await supabase
      .from("staged_houses")
      .update({
        status: "approved",
        reviewed_at: new Date().toISOString(),
        reviewed_by: (await supabase.auth.getUser()).data.user?.email || "unknown",
      })
      .eq("id", item.id)
      .select();

    console.log("✔️ Status update result:", { data: statusData, error: statusError });
    if (statusError) {
      console.error("❌ Failed to update status:", statusError);
      throw new Error(`Status update failed: ${statusError.message}`);
    }
    
    console.log("🎉 Approval process completed successfully!");
  }

  async function handleBulkApprove(items: StagedHouse[]) {
    const count = items.length;
    if (!confirm(`Auto-approve ${count} high-confidence items?\n\nThese items scored ≥90% confidence with complete data.`)) return;

    setProcessingIds(prev => {
      const next = new Set(prev);
      items.forEach(item => next.add(item.id));
      return next;
    });

    try {
      let succeeded = 0;
      let failed = 0;

      for (const item of items) {
        try {
          await applyApproval(item);
          succeeded++;
        } catch (err) {
          console.error(`Failed to approve ${item.name}:`, err);
          failed++;
        }
      }

      await loadStagedHouses();
      alert(`Bulk approval complete!\n✅ Approved: ${succeeded}\n❌ Failed: ${failed}`);
      await loadRecentApprovals();
    } catch (err) {
      console.error("Bulk approval error:", err);
      alert("Bulk approval encountered errors");
    } finally {
      setProcessingIds(new Set());
    }
  }

  function hasChanges(item: StagedHouse, original: OriginalHouse | null): boolean {
    if (!original) return true;
    
    return (
      original.name !== item.name ||
      original.year !== item.intro_year ||
      original.sku !== item.item_number ||
      (item.description !== null && original.notes !== item.description) ||
      (item.primary_image_url !== null && original.photo_url !== item.primary_image_url)
    );
  }

  async function handleReject(item: StagedHouse) {
    const reason = prompt(`Why are you rejecting "${item.name}"?`);
    if (!reason) return;

    setProcessingIds(prev => new Set(prev).add(item.id));

    try {
      await supabase
        .from("staged_houses")
        .update({
          status: "rejected",
          reviewed_at: new Date().toISOString(),
          reviewed_by: (await supabase.auth.getUser()).data.user?.email || "unknown",
          moderator_notes: reason,
        })
        .eq("id", item.id);

      await loadStagedHouses();
    } catch (err) {
      console.error("Error rejecting item:", err);
      alert("Failed to reject item");
    } finally {
      setProcessingIds(prev => {
        const next = new Set(prev);
        next.delete(item.id);
        return next;
      });
    }
  }

  async function handleUndo(approval: ApprovalHistory) {
    if (!approval.original_house_id) {
      alert("Cannot undo: Original house not found");
      return;
    }

    if (!confirm(`Undo approval for "${approval.new_name}"?\n\nThis will restore the original values.`)) return;

    try {
      // Step 1: Restore original values to houses table
      const { error: restoreError } = await supabase
        .from("houses")
        .update({
          name: approval.original_name,
          year: approval.original_year,
          sku: approval.original_sku,
          notes: approval.original_notes,
          photo_url: approval.original_photo_url,
        })
        .eq("id", approval.original_house_id);

      if (restoreError) throw restoreError;

      // Step 2: Mark approval as undone
      const userEmail = (await supabase.auth.getUser()).data.user?.email || "unknown";
      const { error: undoError } = await supabase
        .from("approval_history")
        .update({
          undone_at: new Date().toISOString(),
          undone_by: userEmail,
        })
        .eq("id", approval.id);

      if (undoError) throw undoError;

      // Step 3: Reset staged_houses status back to pending
      const { error: resetError } = await supabase
        .from("staged_houses")
        .update({
          status: "pending",
          reviewed_at: null,
          reviewed_by: null,
        })
        .eq("id", approval.staged_house_id);

      if (resetError) throw resetError;

      alert("✅ Changes undone successfully!");
      await loadStagedHouses();
      await loadRecentApprovals();
    } catch (err) {
      console.error("Error undoing approval:", err);
      alert("Failed to undo changes");
    }
  }

  function getConfidenceBadge(score: number) {
    if (score >= 0.9) return <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-sm font-medium">Excellent ({(score * 100).toFixed(0)}%)</span>;
    if (score >= 0.8) return <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm font-medium">Good ({(score * 100).toFixed(0)}%)</span>;
    if (score >= 0.7) return <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-sm font-medium">Fair ({(score * 100).toFixed(0)}%)</span>;
    return <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-sm font-medium">Low ({(score * 100).toFixed(0)}%)</span>;
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading staged data...</div>
      </div>
    );
  }

  if (stagedHouses.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <div className="text-6xl mb-4">✅</div>
        <div className="text-xl font-semibold text-gray-700">All caught up!</div>
        <div className="text-gray-500 mt-2">No pending items to review</div>
        <div className="text-sm text-gray-400 mt-4">
          Run the Python scraper to queue more items for review
        </div>
      </div>
    );
  }

  // Categorize items by confidence
  const highConfidence = stagedHouses.filter(h => h.overall_confidence_score >= 0.90);
  const mediumConfidence = stagedHouses.filter(h => h.overall_confidence_score >= 0.80 && h.overall_confidence_score < 0.90);
  const lowConfidence = stagedHouses.filter(h => h.overall_confidence_score < 0.80);

  // Filter items based on view mode
  let displayedItems = stagedHouses;
  if (viewMode === 'high') displayedItems = highConfidence;
  else if (viewMode === 'medium') displayedItems = mediumConfidence;
  else if (viewMode === 'low') displayedItems = lowConfidence;

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Data Review Queue</h2>
        <p className="text-gray-600 mb-4">
          Review and approve scraped product data before applying to your collection
        </p>
        
        {/* Statistics */}
        <div className="flex gap-6 text-sm mb-4">
          <div>
            <span className="font-semibold text-gray-700">Total Pending:</span>{" "}
            <span className="text-blue-600">{stagedHouses.length} items</span>
          </div>
          <div>
            <span className="font-semibold text-gray-700">High Confidence (≥90%):</span>{" "}
            <span className="text-green-600">{highConfidence.length} items</span>
          </div>
          <div>
            <span className="font-semibold text-gray-700">Medium (80-89%):</span>{" "}
            <span className="text-yellow-600">{mediumConfidence.length} items</span>
          </div>
          <div>
            <span className="font-semibold text-gray-700">Needs Review (&lt;80%):</span>{" "}
            <span className="text-red-600">{lowConfidence.length} items</span>
          </div>
        </div>

        {/* View Mode Filters */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setViewMode('all')}
            className={`px-4 py-2 rounded text-sm font-medium ${
              viewMode === 'all' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All Items ({stagedHouses.length})
          </button>
          <button
            onClick={() => setViewMode('high')}
            className={`px-4 py-2 rounded text-sm font-medium ${
              viewMode === 'high' 
                ? 'bg-green-600 text-white' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            High Confidence ({highConfidence.length})
          </button>
          <button
            onClick={() => setViewMode('medium')}
            className={`px-4 py-2 rounded text-sm font-medium ${
              viewMode === 'medium' 
                ? 'bg-yellow-600 text-white' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Medium ({mediumConfidence.length})
          </button>
          <button
            onClick={() => setViewMode('low')}
            className={`px-4 py-2 rounded text-sm font-medium ${
              viewMode === 'low' 
                ? 'bg-red-600 text-white' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Needs Review ({lowConfidence.length})
          </button>
        </div>

        {/* Toggle: Show only changes */}
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={showOnlyChanges}
            onChange={(e) => setShowOnlyChanges(e.target.checked)}
            className="rounded"
          />
          <span>Show only fields with changes</span>
        </label>
      </div>

      {/* Recent Approvals - Collapsible Undo Section */}
      {recentApprovals.length > 0 && (
        <div className="bg-blue-50 border-2 border-blue-200 rounded-lg mb-6">
          <button
            onClick={() => setShowRecentApprovals(!showRecentApprovals)}
            className="w-full p-4 flex items-center justify-between hover:bg-blue-100 transition-colors"
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">⏮️</span>
              <div className="text-left">
                <h3 className="text-lg font-bold text-blue-900">
                  Recent Approvals - Undo Available ({recentApprovals.length})
                </h3>
                <p className="text-blue-700 text-sm">
                  Click to {showRecentApprovals ? 'hide' : 'show'} items you can revert (last 24 hours)
                </p>
              </div>
            </div>
            <span className="text-2xl text-blue-700">
              {showRecentApprovals ? '▼' : '▶'}
            </span>
          </button>
          
          {showRecentApprovals && (
            <div className="p-6 pt-0 space-y-2">
              {recentApprovals.map(approval => (
                <div key={approval.id} className="bg-white rounded border border-blue-200 p-3 flex items-center justify-between">
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{approval.new_name}</div>
                    <div className="text-sm text-gray-500">
                      Approved {new Date(approval.approved_at).toLocaleString()} by {approval.approved_by}
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      Changed: {approval.original_name !== approval.new_name && 'Name, '}
                      {approval.original_year !== approval.new_year && 'Year, '}
                      {approval.original_sku !== approval.new_sku && 'SKU, '}
                      {approval.original_notes !== approval.new_notes && 'Notes, '}
                      {approval.original_photo_url !== approval.new_photo_url && 'Photo'}
                    </div>
                  </div>
                  <button
                    onClick={() => handleUndo(approval)}
                    className="bg-orange-600 text-white px-4 py-2 rounded hover:bg-orange-700 font-medium text-sm ml-4"
                  >
                    ⏮️ Undo
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* High Confidence - Bulk Approval Section */}
      {highConfidence.length > 0 && viewMode === 'all' && (
        <div className="bg-green-50 border-2 border-green-200 rounded-lg p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-lg font-bold text-green-900 flex items-center gap-2">
                <span className="text-2xl">⚡</span>
                Excellent Matches - Bulk Approval Available
              </h3>
              <p className="text-green-700 text-sm mt-1">
                {highConfidence.length} {highConfidence.length === 1 ? 'item has' : 'items have'} ≥90% confidence with complete data - these appear to be perfect matches
              </p>
            </div>
            <button
              onClick={() => handleBulkApprove(highConfidence)}
              disabled={processingIds.size > 0}
              className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-md whitespace-nowrap"
            >
              ✓ Approve All {highConfidence.length}
            </button>
          </div>
          
          <div className="bg-white rounded border border-green-200 p-4">
            <div className="text-sm text-gray-700 space-y-2">
              {highConfidence.map(item => (
                <div key={item.id} className="flex items-center justify-between py-1">
                  <div className="flex-1">
                    <span className="font-medium">{item.name}</span>
                    <span className="text-gray-500 ml-2">SKU: {item.item_number}</span>
                    {item.discovered_series && (
                      <span className="text-blue-600 ml-2 text-xs">📚 {item.discovered_series}</span>
                    )}
                  </div>
                  <span className="text-green-700 font-medium">{(item.overall_confidence_score * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Item List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {displayedItems.map(item => {
          const original = item.original_house_id ? originalHouses.get(item.original_house_id) : null;
          const isProcessing = processingIds.has(item.id);
          const itemHasChanges = hasChanges(item, original || null);

          return (
            <div
              key={item.id}
              className="bg-white rounded-lg shadow-sm border-2 border-gray-200 hover:border-blue-300 transition-colors"
            >
              {/* Header */}
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg text-gray-900">{item.name}</h3>
                    <div className="text-sm text-gray-500">SKU: {item.item_number}</div>
                  </div>
                  {getConfidenceBadge(item.overall_confidence_score)}
                </div>
                
                {item.discovered_series && (
                  <div className="text-sm text-blue-600 font-medium">
                    📚 {item.discovered_series}
                  </div>
                )}
              </div>

              {/* Comparison */}
              <div className="p-4 space-y-3">
                {/* Name - only show if changed */}
                {(!showOnlyChanges || (original && original.name !== item.name)) && (
                  <div>
                    <div className="text-gray-500 text-sm font-medium">Name</div>
                    <div className="font-semibold">
                      {original?.name && original.name !== item.name && (
                        <div className="text-red-500 line-through text-sm">{original.name}</div>
                      )}
                      <span className={original?.name !== item.name ? "text-green-600" : "text-gray-900"}>
                        {item.name}
                      </span>
                    </div>
                  </div>
                )}

                {/* SKU - only show if changed */}
                {(!showOnlyChanges || (original && original.sku !== item.item_number)) && (
                  <div>
                    <div className="text-gray-500 text-sm font-medium">SKU</div>
                    <div className="font-semibold">
                      {original?.sku && original.sku !== item.item_number && (
                        <span className="text-red-500 line-through mr-2 text-sm">{original.sku}</span>
                      )}
                      <span className={original?.sku !== item.item_number ? "text-green-600" : "text-gray-900"}>
                        {item.item_number}
                      </span>
                    </div>
                  </div>
                )}

                {/* Years */}
                {(!showOnlyChanges || (original && original.year !== item.intro_year) || item.retire_year) && (
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <div className="text-gray-500 font-medium">Introduced</div>
                      <div className="font-semibold">
                        {original?.year && original.year !== item.intro_year && (
                          <span className="text-red-500 line-through mr-2">{original.year}</span>
                        )}
                        <span className={original?.year !== item.intro_year ? "text-green-600" : "text-gray-900"}>
                          {item.intro_year || "Unknown"}
                        </span>
                      </div>
                    </div>
                    {item.retire_year && (
                      <div>
                        <div className="text-gray-500 font-medium">Retired</div>
                        <div className="font-semibold text-green-600">{item.retire_year}</div>
                      </div>
                    )}
                  </div>
                )}

                {/* Description - only show if present and (not filtered OR changed) */}
                {item.description && (!showOnlyChanges || !original || original.notes !== item.description) && (
                  <div>
                    <div className="text-gray-500 text-sm font-medium">
                      Description {original?.notes !== item.description && <span className="text-green-600">(New)</span>}
                    </div>
                    <div className="text-sm text-gray-700 line-clamp-3">{item.description}</div>
                  </div>
                )}

                {/* Series - only show if present */}
                {item.discovered_series && !showOnlyChanges && (
                  <div>
                    <div className="text-gray-500 text-sm font-medium">Series</div>
                    <div className="text-sm text-blue-600 font-medium">📚 {item.discovered_series}</div>
                  </div>
                )}

                {/* Image - only show if changed */}
                {item.primary_image_url && (!showOnlyChanges || !original || original.photo_url !== item.primary_image_url) && (
                  <div>
                    <div className="text-gray-500 text-sm font-medium mb-2">
                      Image {original?.photo_url !== item.primary_image_url && <span className="text-green-600">(Updated)</span>}
                    </div>
                    <img
                      src={item.primary_image_url}
                      alt={item.name}
                      className="w-full h-48 object-cover rounded"
                    />
                  </div>
                )}

                {/* No changes indicator */}
                {showOnlyChanges && !itemHasChanges && (
                  <div className="text-center py-4 text-gray-500 italic">
                    ✓ All data matches existing record
                  </div>
                )}

                {/* Source */}
                <div className="text-xs text-gray-400">
                  Source:{" "}
                  {item.dept56_retired_url && (
                    <a
                      href={item.dept56_retired_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-500 hover:underline"
                    >
                      Retired Products
                    </a>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="p-4 bg-gray-50 border-t border-gray-200 flex gap-3">
                <button
                  onClick={() => handleApprove(item)}
                  disabled={isProcessing}
                  className="flex-1 bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  {isProcessing ? "Processing..." : "✓ Approve & Apply"}
                </button>
                <button
                  onClick={() => handleReject(item)}
                  disabled={isProcessing}
                  className="flex-1 bg-red-600 text-white py-2 px-4 rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  {isProcessing ? "Processing..." : "✗ Reject"}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
