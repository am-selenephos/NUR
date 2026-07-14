declare module "react-native" {
  import type { ComponentType, ReactNode } from "react";

  export const SafeAreaView: ComponentType<{ style?: unknown; children?: ReactNode }>;
  export const View: ComponentType<{ style?: unknown; children?: ReactNode }>;
  export const Text: ComponentType<{ style?: unknown; children?: ReactNode }>;
  export const StyleSheet: {
    create<T extends Record<string, unknown>>(styles: T): T;
  };
}

declare module "expo-status-bar" {
  import type { ComponentType } from "react";

  export const StatusBar: ComponentType<{ style?: "auto" | "inverted" | "light" | "dark" }>;
}
