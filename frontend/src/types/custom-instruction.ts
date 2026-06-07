export interface CustomInstruction {
  id: string;
  user_id: string;
  name: string;
  content: string;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface InstructionCreate {
  name: string;
  content: string;
  is_active?: boolean;
}

export interface InstructionUpdate {
  name?: string | null;
  content?: string | null;
  is_active?: boolean | null;
}

export interface InstructionListResponse {
  items: CustomInstruction[];
  total: number;
}
