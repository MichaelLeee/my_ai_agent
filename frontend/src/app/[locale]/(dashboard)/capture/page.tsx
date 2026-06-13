"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { ArrowDownToLine, Check, Mic, MicOff, Zap } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiClient } from "@/lib/api-client";

const SpeechRecognitionAPI =
  typeof window !== "undefined"
    ? (window as unknown as Record<string, unknown>).SpeechRecognition ||
      (window as unknown as Record<string, unknown>).webkitSpeechRecognition
    : null;

export default function CapturePage() {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [listening, setListening] = useState(false);
  const contentRef = useRef<HTMLTextAreaElement>(null);
  const recognitionRef = useRef<InstanceType<typeof SpeechRecognitionAPI> | null>(null);

  const hasSpeech = !!SpeechRecognitionAPI;

  useEffect(() => {
    contentRef.current?.focus();
  }, []);

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
    setListening(false);
  }, []);

  const startListening = useCallback(() => {
    if (!SpeechRecognitionAPI) return;
    const recognition = new (SpeechRecognitionAPI as new () => SpeechRecognition)() as SpeechRecognition & {
      onresult?: (e: SpeechRecognitionEvent) => void;
      onerror?: (e: SpeechRecognitionErrorEvent) => void;
      onend?: () => void;
    };
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onresult = (e: SpeechRecognitionEvent) => {
      let interim = "";
      let final = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const transcript = e.results[i][0].transcript;
        if (e.results[i].isFinal) {
          final += transcript + " ";
        } else {
          interim += transcript;
        }
      }
      setContent((prev) => {
        const base = prev.replace(/\[listening...\]\s*$/, "").trim();
        const added = final ? (base ? base + " " + final : final) : base;
        return interim ? added + " [listening...]" : added;
      });
    };

    recognition.onerror = (e: SpeechRecognitionErrorEvent) => {
      if (e.error !== "no-speech") {
        toast.error("Voice recognition error");
      }
      setListening(false);
    };

    recognition.onend = () => {
      setContent((prev) => prev.replace(/\[listening...\]\s*$/, "").trim());
      setListening(false);
    };

    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  }, []);

  const toggleMic = () => {
    if (listening) {
      stopListening();
    } else {
      startListening();
    }
  };

  const handleSave = async () => {
    if (!content.trim()) return;
    setSaving(true);
    try {
      await apiClient.post("/v1/notes", {
        title: title.trim() || content.slice(0, 60).replace(/\[listening...\]/, "").trim() + "...",
        content: content.trim().replace(/\[listening...\]/, "").trim(),
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

        <div className="flex gap-2">
          <Button
            onClick={handleSave}
            disabled={!content.trim() || saving}
            className="flex-1"
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

          {hasSpeech && (
            <Button
              onClick={toggleMic}
              variant={listening ? "default" : "outline"}
              size="lg"
              className={listening ? "animate-pulse bg-red-500 hover:bg-red-600" : ""}
            >
              {listening ? (
                <MicOff className="size-4" />
              ) : (
                <Mic className="size-4" />
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
