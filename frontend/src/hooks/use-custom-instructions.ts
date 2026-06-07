"use client";

import { useCallback } from "react";
import { toast } from "sonner";
import { apiClient } from "@/lib/api-client";
import { useInstructionStore } from "@/stores";
import type {
  CustomInstruction,
  InstructionCreate,
  InstructionUpdate,
  InstructionListResponse,
} from "@/types/custom-instruction";

export function useCustomInstructions() {
  const {
    instructions, isLoading, error,
    setInstructions, addInstruction, updateInstruction, removeInstruction,
    setLoading, setError,
  } = useInstructionStore();

  const fetchInstructions = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiClient.get<InstructionListResponse>("/v1/custom-instructions");
      setInstructions(data.items);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to fetch instructions";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [setInstructions, setLoading, setError]);

  const createInstruction = useCallback(async (data: InstructionCreate) => {
    try {
      const created = await apiClient.post<CustomInstruction>("/v1/custom-instructions", data);
      addInstruction(created);
      toast.success("Instruction created");
      return created;
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to create instruction";
      toast.error(msg);
      return null;
    }
  }, [addInstruction]);

  const updateExisting = useCallback(async (id: string, data: InstructionUpdate) => {
    try {
      const updated = await apiClient.patch<CustomInstruction>(
        `/v1/custom-instructions/${id}`, data
      );
      updateInstruction(id, updated);
      toast.success("Instruction updated");
      return updated;
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to update instruction";
      toast.error(msg);
      return null;
    }
  }, [updateInstruction]);

  const deleteInstruction = useCallback(async (id: string) => {
    try {
      await apiClient.delete(`/v1/custom-instructions/${id}`);
      removeInstruction(id);
      toast.success("Instruction deleted");
      return true;
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to delete instruction";
      toast.error(msg);
      return false;
    }
  }, [removeInstruction]);

  return {
    instructions, isLoading, error,
    fetchInstructions, createInstruction,
    updateInstruction: updateExisting, deleteInstruction,
  };
}
