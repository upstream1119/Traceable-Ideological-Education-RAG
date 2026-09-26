/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_RETRIEVE_MODE?: "mock" | "api";
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
