/**
 * Data Review Component for Department 56 Browser
 * Admin-only interface for reviewing scraped product data
 */

import React, { useEffect, useState } from "react";
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

export function DataReviewTab() {
  const [stagedHouses, setStagedHouses] = useState<StagedHouse[]>([]);
  const [originalHouses, setOriginalHouses] = useState<Map<string, OriginalHouse>>(new Map());
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState<StagedHouse | null>(null);
  const [processingIds, setProcessingIds] = useState<Set<string>>(new Set());

  // Load staged houses
  useEffect(() => {
    loadStagedHouses();
  }, []);

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
      if (item.original_house_id) {
        // Update existing house
        await supabase
          .from("houses")
          .update({
            name: item.name,
            year: item.intro_year,
            sku: item.item_number,
            notes: item.description ? 
              `${item.description}\n\nSeries: ${item.discovered_series || 'Unknown'}\nRetired: ${item.retire_year || 'Unknown'}` : 
              null,
            photo_url: item.primary_image_url,
          })
          .eq("id", item.original_house_id);
      } else {
        // Create new house (if implementing new imports)
        alert("New house import not yet implemented");
        return;
      }

      // Mark as approved
      await supabase
        .from("staged_houses")
        .update({
          status: "approved",
          reviewed_at: new Date().toISOString(),
          reviewed_by: (await supabase.auth.getUser()).data.user?.email || "unknown",
        })
        .eq("id", item.id);

      // Reload
      await loadStagedHouses();
      setSelectedItem(null);
    } catch (err) {
      console.error("Error approving item:", err);
      alert("Failed to approve item");
    } finally {
      setProcessingIds(prev => {
        const next = new Set(prev);
        next.delete(item.id);
        return next;
      });
    }
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
      setSelectedItem(null);
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

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Data Review Queue</h2>
        <p className="text-gray-600">
          Review and approve scraped product data before applying to your collection
        </p>
        <div className="mt-4 flex gap-4 text-sm">
          <div>
            <span className="font-semibold text-gray-700">Pending:</span>{" "}
            <span className="text-blue-600">{stagedHouses.length} items</span>
          </div>
          <div>
            <span className="font-semibold text-gray-700">High Confidence:</span>{" "}
            <span className="text-green-600">
              {stagedHouses.filter(s => s.overall_confidence_score >= 0.8).length} items
            </span>
          </div>
        </div>
      </div>

      {/* Item List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {stagedHouses.map(item => {
          const original = item.original_house_id ? originalHouses.get(item.original_house_id) : null;
          const isProcessing = processingIds.has(item.id);

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
                {/* Years */}
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
                  <div>
                    <div className="text-gray-500 font-medium">Retired</div>
                    <div className="font-semibold text-green-600">{item.retire_year || "Current"}</div>
                  </div>
                </div>

                {/* Description */}
                {item.description && (
                  <div>
                    <div className="text-gray-500 text-sm font-medium">Description</div>
                    <div className="text-sm text-gray-700 line-clamp-3">{item.description}</div>
                  </div>
                )}

                {/* Image */}
                {item.primary_image_url && (
                  <div>
                    <img
                      src={item.primary_image_url}
                      alt={item.name}
                      className="w-full h-48 object-cover rounded"
                    />
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
