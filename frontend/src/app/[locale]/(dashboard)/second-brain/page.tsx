"use client";

import { useEffect, useState, useCallback } from "react";
import { Brain, Plus, Search, Share2, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui";
import { NoteCard } from "@/components/second-brain/note-card";
import { KnowledgeGraph } from "@/components/second-brain/knowledge-graph";
import { NoteEditor } from "@/components/second-brain/note-editor";
import { apiClient } from "@/lib/api-client";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";

interface Note {
  id: string; title: string; content: string;
  tags: string[] | null; is_archived: boolean;
  created_at: string; updated_at: string | null;
}

export default function SecondBrainPage() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTag, setSearchTag] = useState("");
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingNote, setEditingNote] = useState<Note | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [showGraph, setShowGraph] = useState(false);
  const [graphData, setGraphData] = useState<any>(null);

  const fetchGraph = useCallback(async () => {
    try {
      const d = await apiClient.get<any>("/v1/notes/graph");
      setGraphData(d);
    } catch {}
  }, []);

  const fetchNotes = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchTag) params.set("tag", searchTag);
      const data = await apiClient.get<{ items: Note[]; total: number }>(
        `/v1/notes?${params.toString()}`);
      setNotes(data.items);
    } catch (err: any) {
      toast.error(err.message || "Failed to load notes");
    } finally { setLoading(false); }
  }, [searchTag]);

  useEffect(() => { fetchNotes(); }, [fetchNotes]);

  const handleSave = async (data: { title: string; content: string; tags: string; is_archived: boolean }) => {
    const tagList = data.tags ? data.tags.split(",").map((t) => t.trim()).filter(Boolean) : null;
    const body = { title: data.title, content: data.content, tags: tagList, is_archived: data.is_archived };
    if (editingNote?.id) {
      await apiClient.patch(`/v1/notes/${editingNote.id}`, body);
      toast.success("Note updated");
    } else {
      await apiClient.post("/v1/notes", body);
      toast.success("Note created");
    }
    fetchNotes();
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await apiClient.delete(`/v1/notes/${deleteId}`);
      toast.success("Note deleted");
      setDeleteId(null);
      fetchNotes();
    } catch (err: any) {
      toast.error(err.message || "Failed to delete note");
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

      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input
            placeholder="Filter by tag (e.g., journal, devops)..."
            value={searchTag}
            onChange={(e) => setSearchTag(e.target.value)}
            className="pl-9"
          />
        </div>
        {searchTag && (
          <Button variant="ghost" size="icon" onClick={() => setSearchTag("")}>
            <X className="size-4" />
          </Button>
        )}
      </div>

      <Button variant="outline" size="sm" className="self-start"
        onClick={() => { setShowGraph(!showGraph); if (!graphData) fetchGraph(); }}>
        <Share2 className="mr-2 size-4" />
        {showGraph ? "Hide Graph" : "Show Graph"}
      </Button>

      {showGraph && <KnowledgeGraph data={graphData} />}

      {loading ? (
        <div className="flex items-center justify-center py-20"><Spinner /></div>
      ) : notes.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="rounded-full bg-muted p-4 mb-4">
            <Brain className="size-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold">No notes yet</h3>
          <p className="text-muted-foreground max-w-sm mt-1">
            {searchTag ? `No notes found with tag "${searchTag}"` : "Create your first note to start building your Second Brain."}
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {notes.map((note) => (
            <NoteCard key={note.id} note={note}
              onEdit={(n) => { setEditingNote(n); setEditorOpen(true); }}
              onDelete={(id) => setDeleteId(id)}
            />
          ))}
        </div>
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
