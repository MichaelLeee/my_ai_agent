"use client";

import { Pencil, Trash2, Link2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";

interface NoteCardProps {
  note: {
    id: string;
    title: string;
    content: string;
    tags: string[] | null;
    is_archived: boolean;
    created_at: string;
  };
  onEdit: (note: any) => void;
  onDelete: (id: string) => void;
}

export function NoteCard({ note, onEdit, onDelete }: NoteCardProps) {
  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold line-clamp-1">{note.title}</h3>
        </div>
        {note.tags && note.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {note.tags.map((tag) => (
              <Badge key={tag} variant="secondary" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </CardHeader>
      <CardContent className="flex-1 pb-2">
        <p className="text-sm text-muted-foreground line-clamp-4 whitespace-pre-wrap">
          {note.content}
        </p>
      </CardContent>
      <CardFooter className="flex justify-between pt-0">
        <span className="text-xs text-muted-foreground">
          {new Date(note.created_at).toLocaleDateString()}
        </span>
        <div className="flex gap-1">
          <Button variant="ghost" size="icon" onClick={() => onEdit(note)}>
            <Pencil className="size-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={() => onDelete(note.id)}>
            <Trash2 className="size-4 text-destructive" />
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}
