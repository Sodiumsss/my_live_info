import { reactive } from "vue";
import { supabase } from "@/lib/supabase";

export interface Artist {
  id: string;
  canonical_name: string;
  created_at: string;
}

export interface User {
  id: string;
  name: string;
  email: string | null;
  feishu_webhook: string | null;
  notify_on_status_change: boolean;
  created_at: string;
}

interface DataState {
  artists: Artist[];
  users: User[];
}

const state = reactive<DataState>({ artists: [], users: [] });

export function useData() {
  return {
    state,
    async loadArtists() {
      const { data, error } = await supabase()
        .from("artists")
        .select("id, canonical_name, created_at")
        .order("canonical_name");
      if (error) throw error;
      state.artists = (data ?? []) as Artist[];
    },
    async loadUsers() {
      const { data, error } = await supabase()
        .from("users")
        .select("id, name, email, feishu_webhook, notify_on_status_change, created_at")
        .order("name");
      if (error) throw error;
      state.users = (data ?? []) as User[];
    },
  };
}
