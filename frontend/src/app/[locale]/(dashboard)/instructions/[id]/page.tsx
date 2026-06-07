"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Spinner } from "@/components/ui";
import { useCustomInstructions } from "@/hooks/use-custom-instructions";

export default function EditInstructionPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { instructions, fetchInstructions, updateInstruction, deleteInstruction } = useCustomInstructions();
  const [name, setName] = useState("");
  const [content, setContent] = useState("");
  const [isActive, setIsActive] = useState(false);
  const [saving, setSaving] = useState(false);
  const instruction = instructions.find((i) => i.id === id);

  useEffect(() => { if (instructions.length === 0) fetchInstructions(); }, []);
  useEffect(() => {
    if (instruction) { setName(instruction.name); setContent(instruction.content); setIsActive(instruction.is_active); }
  }, [instruction, instructions]);

  const handleSave = async () => {
    if (!name.trim() || !content.trim()) return;
    setSaving(true);
    const result = await updateInstruction(id, { name: name.trim(), content: content.trim(), is_active: isActive });
    setSaving(false);
    if (result) router.push("/instructions");
  };

  const handleDelete = async () => { const ok = await deleteInstruction(id); if (ok) router.push("/instructions"); };

  if (!instructions.length) return <div className="flex items-center justify-center py-20"><Spinner /></div>;
  if (!instruction) return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <h2 className="text-xl font-semibold">Instruction not found</h2>
      <Button variant="outline" className="mt-4" onClick={() => router.push("/instructions")}><ArrowLeft className="mr-2 size-4" />Back</Button>
    </div>
  );

  return (
    <div className="flex flex-col gap-6 max-w-2xl">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={() => router.push("/instructions")}><ArrowLeft className="size-4" /></Button>
        <h1 className="text-2xl font-bold tracking-tight">Edit Instruction</h1>
      </div>
      <div className="grid gap-4">
        <div className="grid gap-2">
          <Label htmlFor="name">Name</Label>
          <Input id="name" value={name} onChange={(e) => setName(e.target.value)} maxLength={255} />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="content">Instruction Content</Label>
          <Textarea id="content" value={content} onChange={(e) => setContent(e.target.value)} rows={8} maxLength={5000} />
          <p className="text-xs text-muted-foreground text-right">{content.length}/5000</p>
        </div>
        <div className="flex items-center gap-2">
          <Checkbox id="is_active" checked={isActive} onCheckedChange={(c) => setIsActive(c === true)} />
          <Label htmlFor="is_active" className="cursor-pointer">Active</Label>
        </div>
        <div className="flex items-center justify-between pt-4">
          <Button variant="destructive" onClick={handleDelete}>Delete</Button>
          <Button onClick={handleSave} disabled={saving || !name.trim() || !content.trim()}>
            <Save className="mr-2 size-4" />{saving ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </div>
    </div>
  );
}
