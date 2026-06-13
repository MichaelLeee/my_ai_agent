"use client";

import { useEffect, useState, useCallback } from "react";
import { Brain, Plus, Search, Share2, X, SlidersHorizontal, CalendarDays } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { NoteCard } from "@/components/second-brain/note-card";
import dynamic from "next/dynamic";
import { NoteEditor } from "@/components/second-brain/note-editor";

const KnowledgeGraph = dynamic(
  () => import("@/components/second-brain/knowledge-graph").then((m) => ({ default: m.KnowledgeGraph })),
  { ssr: false, loading: () => <div className="flex items-center justify-center h-[400px] border rounded-xl bg-muted/20 text-muted-foreground text-sm">Loading graph...</div> }
);
import { apiClient } from "@/lib/api-client";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";

interface Note {
  id: string; title: string; content: string;
  tags: string[] | null; is_archived: boolean;
  created_at: string; updated_at: string | null;
}

type SearchMode = "hybrid" | "semantic" | "keyword";

export default function SecondBrainPage() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchMode, setSearchMode] = useState<SearchMode>("hybrid");
  const [searchTag, setSearchTag] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingNote, setEditingNote] = useState<Note | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [showGraph, setShowGraph] = useState(false);
  const [graphData, setGraphData] = useState<Record<string, unknown> | null>(null);

  const modes: { value: SearchMode; label: string }[] = [
    { value: "hybrid", label: "Smart" },
    { value: "semantic", label: "Meaning" },
    { value: "keyword", label: "Words" },
  ];

  const fetchGraph = useCallback(async () => {
    try {
      const d = await apiClient.get<Record<string, unknown>>("/v1/notes/graph");
      setGraphData(d);
    } catch {
      toast.error("Failed to load knowledge graph");
    }
  }, []);

  const fetchNotes = useCallback(async () => {
    setLoading(true);
    try {
      if (searchQuery) {
        // Full search with mode
        const data = await apiClient.post<Note[] | { items: Note[] }>(
          `/v1/notes/search?query=${encodeURIComponent(searchQuery)}&limit=20&mode=${searchMode}${searchTag ? `&tag=${encodeURIComponent(searchTag)}` : ""}${dateFrom ? `&date_from=${dateFrom}` : ""}${dateTo ? `&date_to=${dateTo}` : ""}`
        );
        const results = Array.isArray(data) ? data : (data as { items: Note[] }).items || [];
        setNotes(results);
      } else {
        // List with optional tag filter
        const params = new URLSearchParams();
        if (searchTag) params.set("tag", searchTag);
        const data = await apiClient.get<{ items: Note[]; total: number }>(
          `/v1/notes?${params.toString()}`);
        setNotes(data.items);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load notes";
      toast.error(msg);
    } finally { setLoading(false); }
  }, [searchQuery, searchMode, searchTag, dateFrom, dateTo]);

  useEffect(() => { fetchNotes(); }, [fetchNotes]);

  const handleSave = async (data: { title: string; content: string; tags: string; is_archived: boolean }) => {
    const tagList = data.tags ? data.tags.split(",").map((t) => t.trim()).filter(Boolean) : null;
    const body = { title: data.title, content: data.content, tags: tagList, is_archived: data.is_archived };
    try {
      if (editingNote?.id) {
        await apiClient.patch(`/v1/notes/${editingNote.id}`, body);
        toast.success("Note updated");
      } else {
        await apiClient.post("/v1/notes", body);
        toast.success("Note created");
      }
      fetchNotes();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save note";
      toast.error(msg);
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await apiClient.delete(`/v1/notes/${deleteId}`);
      toast.success("Note deleted");
      setDeleteId(null);
      fetchNotes();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to delete note";
      toast.error(msg);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Second Brain</h1>
          <p className="text-muted-foreground">Your personal knowledge base with AI-powered search.</p>
        </div>
        <Button onClick={() => { setEditingNote(null); setEditorOpen(true); }}>
          <Plus className="mr-2 size-4" /> New Note
        </Button>
      </div>

      <div className="flex flex-col gap-2">
        {/* Search bar + mode toggle */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              placeholder="Search notes by keyword or meaning..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 pr-9"
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery("")} className="absolute right-3 top-1/2 -translate-y-1/2">
                <X className="size-4 text-muted-foreground" />
              </button>
            )}
          </div>
          <Button variant="ghost" size="icon" onClick={() => setShowFilters(!showFilters)}>
            <SlidersHorizontal className="size-4" />
          </Button>
        </div>

        {/* Search mode toggle */}
        {searchQuery && (
          <div className="flex gap-1">
            {modes.map((m) => (
              <button
                key={m.value}
                onClick={() => setSearchMode(m.value)}
                className={`px-2.5 py-1 text-xs rounded-md transition-colors ${searchMode === m.value ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:bg-muted/80"}`}
              >
                {m.label}
              </button>
            ))}
          </div>
        )}

        {/* Filters panel */}
        {showFilters && (
          <div className="flex flex-wrap gap-3 p-3 rounded-lg border bg-muted/30">
            <div className="flex-1 min-w-[160px]">
              <label className="text-xs text-muted-foreground">Tag filter</label>
              <Input
                placeholder="e.g. journal, devops"
                value={searchTag}
                onChange={(e) => setSearchTag(e.target.value)}
                className="h-8 text-sm"
              />
            </div>
            <div className="w-[150px]">
              <label className="text-xs text-muted-foreground">From</label>
              <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="h-8 text-sm" />
            </div>
            <div className="w-[150px]">
              <label className="text-xs text-muted-foreground">To</label>
              <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="h-8 text-sm" />
            </div>
            {(searchTag || dateFrom || dateTo) && (
              <div className="flex items-end">
                <Button variant="ghost" size="sm" onClick={() => { setSearchTag(""); setDateFrom(""); setDateTo(""); }}>
                  <X className="mr-1 size-3" />Clear
                </Button>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        <Button variant="outline" size="sm"
          onClick={() => { setShowGraph(!showGraph); if (!graphData) fetchGraph(); }}>
          <Share2 className="mr-2 size-4" />
          {showGraph ? "Hide Graph" : "Show Graph"}
        </Button>
        <div className="flex gap-1 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1"><CalendarDays className="size-3" />{notes.length} notes</span>
        </div>
      </div>

      {showGraph && <KnowledgeGraph data={graphData} />}

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-[140px] rounded-xl" />
          ))}
        </div>
      ) : notes.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="rounded-full bg-muted p-4 mb-4">
            <Brain className="size-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold">No notes yet</h3>
          <p className="text-muted-foreground max-w-sm mt-1">
            {searchQuery ? "No notes match your search. Try different keywords or mode." : searchTag ? `No notes found with tag "${searchTag}"` : "Create your first note to start building your Second Brain."}
          </p>
        </div>
      ) : (
        <>
          {searchQuery && (
            <p className="text-sm text-muted-foreground">Search results for &quot;{searchQuery}&quot; — {notes.length} found</p>
          )}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {notes.map((note) => (
              <NoteCard key={note.id} note={note}
                onEdit={(n) => { setEditingNote(n); setEditorOpen(true); }}
                onDelete={(id) => setDeleteId(id)}
              />
            ))}
          </div>
        </>
      )}

      <NoteEditor open={editorOpen} onOpenChange={setEditorOpen} note={editingNote} onSave={handleSave} />

      <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Note</AlertDialogTitle>
            <AlertDialogDescription>This note will be permanently removed.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground">Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
