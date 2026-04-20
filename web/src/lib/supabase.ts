import { createClient, type SupabaseClient } from "@supabase/supabase-js";

let _client: SupabaseClient | null = null;

export function setSupabaseClient(url: string, serviceKey: string) {
  _client = createClient(url, serviceKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });
}

export function supabase(): SupabaseClient {
  if (!_client) throw new Error("Supabase client 未初始化（请先登录）");
  return _client;
}

export function hasSupabaseClient(): boolean {
  return _client !== null;
}
