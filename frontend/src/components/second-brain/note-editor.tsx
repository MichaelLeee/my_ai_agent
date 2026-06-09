"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

interface NoteEditorProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  note?: { id?: string; title?: string; content?: string; tags?: string[] | null; is_archived?: boolean } | null;
  onSave: (data: { title: string; content: string; tags: string; is_archived: boolean }) => Promise<any>;
}

export function NoteEditor({ open, onOpenChange, note, onSave }: NoteEditorProps) {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [tags, setTags] = useState("");
  const [isArchived, setIsArchived] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) {
      setTitle(note?.title ?? "");
      setContent(note?.content ?? "");
      setTags(note?.tags?.join(", ") ?? "");
      setIsArchived(note?.is_archived ?? false);
    }
  }, [open, note]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;
    setSaving(true);
    try {
      const tagList = tags.split(",").map((t) => t.trim()).filter(Boolean);
      await onSave({ title: title.trim(), content: content.trim(), tags: tagList.join(","), is_archived: isArchived });
      onOpenChange(false);
    } finally { setSaving(false); }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{note?.id ? "Edit Note" : "New Note"}</DialogTitle>
            <DialogDescription>Save an idea, thought, or reference to your Second Brain.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="title">Title</Label>
              <Input id="title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Note title" maxLength={500} required />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="content">Content</Label>
              <Textarea id="content" value={content} onChange={(e) => setContent(e.target.value)} placeholder="Write your note..." rows={8} required />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="tags">Tags (comma-separated)</Label>
              <Input id="tags" value={tags} onChange={(e) => setTags(e.target.value)} placeholder="e.g., journal, devops, ideas" />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={saving}>Cancel</Button>
            <Button type="submit" disabled={saving || !title.trim() || !content.trim()}>{saving ? "Saving..." : "Save"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
