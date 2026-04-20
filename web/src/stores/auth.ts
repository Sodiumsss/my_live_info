import { reactive } from "vue";
import { decryptServiceKey } from "@/lib/crypto";
import { setSupabaseClient, hasSupabaseClient } from "@/lib/supabase";

interface AuthState {
  authed: boolean;
  configMissing: boolean;
}

const state = reactive<AuthState>({
  authed: hasSupabaseClient(),
  configMissing: !window.LIVE_INFO_CONFIG,
});

export function useAuth() {
  return {
    state,
    async login(password: string): Promise<void> {
      const cfg = window.LIVE_INFO_CONFIG;
      if (!cfg) throw new Error("config.js 未加载或构建失败（缺少 GitHub Secrets?）");
      const serviceKey = await decryptServiceKey(password, cfg);
      setSupabaseClient(cfg.supabaseUrl, serviceKey);
      state.authed = true;
    },
  };
}
