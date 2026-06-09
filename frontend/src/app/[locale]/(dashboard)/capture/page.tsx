"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowDownToLine, Check, Zap } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiClient } from "@/lib/api-client";

export default function CapturePage() {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const contentRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    contentRef.current?.focus();
  }, []);

  const handleSave = async () => {
    if (!content.trim()) return;
    setSaving(true);
    try {
      await apiClient.post("/v1/notes", {
        title: title.trim() || content.slice(0, 60) + "...",
        content: content.trim(),
        tags: ["quick-capture"],
      });
      setTitle("");
      setContent("");
      setSaved(true);
      toast.success("Captured");
      setTimeout(() => setSaved(false), 1500);
      contentRef.current?.focus();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save";
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      handleSave();
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-12rem)] flex-col items-center justify-center px-4">
      <div className="w-full max-w-lg space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="size-4 text-brand" />
            <h1 className="text-lg font-semibold tracking-tight">Quick Capture</h1>
          </div>
          <span className="text-[11px] text-muted-foreground font-mono">⌘+Enter to save</span>
        </div>

        <Input
          placeholder="Title (optional)"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={handleKeyDown}
          className="text-base border-foreground/10"
        />

        <textarea
          ref={contentRef}
          placeholder="What's on your mind?"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={6}
          className="w-full rounded-xl border border-foreground/10 bg-foreground/[0.02] p-4 text-base resize-none focus:outline-none focus:ring-2 focus:ring-brand/20 placeholder:text-muted-foreground/50"
        />

        <Button
          onClick={handleSave}
          disabled={!content.trim() || saving}
          className="w-full"
          size="lg"
        >
          {saving ? (
            "Saving..."
          ) : saved ? (
            <>
              <Check className="mr-2 size-4" /> Saved
            </>
          ) : (
            <>
              <ArrowDownToLine className="mr-2 size-4" /> Capture
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
