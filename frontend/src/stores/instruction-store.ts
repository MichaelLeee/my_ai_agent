"use client";

import { create } from "zustand";
import type { CustomInstruction } from "@/types/custom-instruction";

interface InstructionState {
  instructions: CustomInstruction[];
  isLoading: boolean;
  error: string | null;
  setInstructions: (instructions: CustomInstruction[]) => void;
  addInstruction: (instruction: CustomInstruction) => void;
  updateInstruction: (id: string, data: Partial<CustomInstruction>) => void;
  removeInstruction: (id: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useInstructionStore = create<InstructionState>()((set) => ({
  instructions: [],
  isLoading: false,
  error: null,
  setInstructions: (instructions) => set({ instructions, error: null }),
  addInstruction: (instruction) =>
    set((state) => ({ instructions: [instruction, ...state.instructions] })),
  updateInstruction: (id, data) =>
    set((state) => ({
      instructions: state.instructions.map((i) => (i.id === id ? { ...i, ...data } : i)),
    })),
  removeInstruction: (id) =>
    set((state) => ({ instructions: state.instructions.filter((i) => i.id !== id) })),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
}));
