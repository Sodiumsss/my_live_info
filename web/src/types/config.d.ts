export {};

declare global {
  interface LiveInfoConfig {
    supabaseUrl: string;
    salt: string;
    iv: string;
    ciphertext: string;
    iterations: number;
  }

  interface Window {
    LIVE_INFO_CONFIG?: LiveInfoConfig;
  }
}
