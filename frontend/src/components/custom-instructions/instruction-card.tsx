"use client";

import { Pencil, Trash2 } from "lucide-react";
import type { CustomInstruction } from "@/types/custom-instruction";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";

interface InstructionCardProps {
  instruction: CustomInstruction;
  onEdit: (instruction: CustomInstruction) => void;
  onDelete: (id: string) => void;
  onToggle: (id: string, isActive: boolean) => void;
}

export function InstructionCard({ instruction, onEdit, onDelete, onToggle }: InstructionCardProps) {
  return (
    <Card className={instruction.is_active ? "border-primary/50" : ""}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <h3 className="font-semibold truncate">{instruction.name}</h3>
            {instruction.is_active && <Badge variant="default" className="shrink-0">Active</Badge>}
          </div>
        </div>
      </CardHeader>
      <CardContent className="pb-2">
        <p className="text-sm text-muted-foreground line-clamp-3 whitespace-pre-wrap">
          {instruction.content}
        </p>
      </CardContent>
      <CardFooter className="flex justify-between pt-0">
        <Button variant="ghost" size="sm" onClick={() => onToggle(instruction.id, !instruction.is_active)}>
          {instruction.is_active ? "Deactivate" : "Activate"}
        </Button>
        <div className="flex gap-1">
          <Button variant="ghost" size="icon" onClick={() => onEdit(instruction)}>
            <Pencil className="size-4" /><span className="sr-only">Edit</span>
          </Button>
          <Button variant="ghost" size="icon" onClick={() => onDelete(instruction.id)}>
            <Trash2 className="size-4 text-destructive" /><span className="sr-only">Delete</span>
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}
