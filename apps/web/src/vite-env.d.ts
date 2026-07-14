/// <reference types="vite/client" />
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_NUR_ENABLE_OMEGA_RESEARCH?: string;
}
interface ImportMeta { readonly env: ImportMetaEnv; }
