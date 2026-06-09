"use client";

import { useEffect, useState } from "react";
import { BookOpen, Plus, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui";
import { InstructionCard } from "@/components/custom-instructions/instruction-card";
import { InstructionEditor } from "@/components/custom-instructions/instruction-editor";
import { useCustomInstructions } from "@/hooks/use-custom-instructions";
import type { CustomInstruction, InstructionCreate, InstructionUpdate } from "@/types/custom-instruction";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";

export default function InstructionsPage() {
  const { instructions, isLoading, error, fetchInstructions, createInstruction, updateInstruction, deleteInstruction } = useCustomInstructions();
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingInstruction, setEditingInstruction] = useState<CustomInstruction | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => { fetchInstructions(); }, [fetchInstructions]);

  const handleSave = async (data: InstructionCreate | InstructionUpdate) => {
    if (editingInstruction) return await updateInstruction(editingInstruction.id, data as InstructionUpdate);
    return await createInstruction(data as InstructionCreate);
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    setDeleting(true);
    const ok = await deleteInstruction(deleteId);
    if (!ok) toast.error("Failed to delete instruction");
    setDeleting(false);
    setDeleteId(null);
  };

  if (isLoading) return <div className="flex items-center justify-center py-20"><Spinner /></div>;

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="rounded-full bg-destructive/10 p-4 mb-4">
          <AlertTriangle className="size-8 text-destructive" />
        </div>
        <h3 className="text-lg font-semibold">Failed to load instructions</h3>
        <p className="text-muted-foreground max-w-sm mt-1 mb-4">{error}</p>
        <Button variant="outline" onClick={fetchInstructions}>Retry</Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Custom Instructions
            {instructions.length > 0 && (
              <span className="ml-2 inline-flex items-center justify-center rounded-full bg-muted px-2 py-0.5 text-sm font-medium text-muted-foreground">
                {instructions.length}
              </span>
            )}
          </h1>
          <p className="text-muted-foreground">Teach the AI agent how to behave by creating system prompt overrides.</p>
        </div>
        <Button onClick={() => { setEditingInstruction(null); setEditorOpen(true); }}>
          <Plus className="mr-2 size-4" />New Instruction
        </Button>
      </div>

      {instructions.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="rounded-full bg-muted p-4 mb-4"><BookOpen className="size-8 text-muted-foreground" /></div>
          <h3 className="text-lg font-semibold">No instructions yet</h3>
          <p className="text-muted-foreground max-w-sm mt-1">Create your first custom instruction to personalize the AI agent&apos;s behavior.</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {instructions.map((i) => (
            <InstructionCard key={i.id} instruction={i}
              onEdit={(inst) => { setEditingInstruction(inst); setEditorOpen(true); }}
              onDelete={(id) => setDeleteId(id)}
              onToggle={(id, isActive) => updateInstruction(id, { is_active: isActive })}
            />
          ))}
        </div>
      )}

      <InstructionEditor open={editorOpen} onOpenChange={setEditorOpen} instruction={editingInstruction} onSave={handleSave} />

      <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Instruction</AlertDialogTitle>
            <AlertDialogDescription>This instruction will be permanently removed. This action cannot be undone.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} disabled={deleting} className="bg-destructive text-destructive-foreground">
              {deleting ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
