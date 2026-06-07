"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import type { CustomInstruction, InstructionCreate, InstructionUpdate } from "@/types/custom-instruction";

interface InstructionEditorProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  instruction?: CustomInstruction | null;
  onSave: (data: InstructionCreate | InstructionUpdate) => Promise<CustomInstruction | null>;
}

export function InstructionEditor({ open, onOpenChange, instruction, onSave }: InstructionEditorProps) {
  const [name, setName] = useState("");
  const [content, setContent] = useState("");
  const [isActive, setIsActive] = useState(false);
  const [saving, setSaving] = useState(false);
  const isEditing = !!instruction;

  useEffect(() => {
    if (open) {
      setName(instruction?.name ?? "");
      setContent(instruction?.content ?? "");
      setIsActive(instruction?.is_active ?? false);
    }
  }, [open, instruction]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !content.trim()) return;
    setSaving(true);
    try {
      await onSave({ name: name.trim(), content: content.trim(), is_active: isActive });
      onOpenChange(false);
    } finally { setSaving(false); }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{isEditing ? "Edit Instruction" : "New Instruction"}</DialogTitle>
            <DialogDescription>Create a system prompt override that the AI agent will follow when active.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Name</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g., Pirate Mode" maxLength={255} required />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="content">Instruction Content</Label>
              <Textarea id="content" value={content} onChange={(e) => setContent(e.target.value)} placeholder="Always respond like a pirate. Use nautical metaphors..." rows={6} maxLength={5000} required />
              <p className="text-xs text-muted-foreground text-right">{content.length}/5000</p>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox id="is_active" checked={isActive} onCheckedChange={(c) => setIsActive(c === true)} />
              <Label htmlFor="is_active" className="cursor-pointer">
                Activate immediately
                <span className="block text-xs text-muted-foreground">Deactivates any other active instruction</span>
              </Label>
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={saving}>Cancel</Button>
            <Button type="submit" disabled={saving || !name.trim() || !content.trim()}>{saving ? "Saving..." : "Save"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
