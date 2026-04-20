<script setup lang="ts">
import { RouterLink, RouterView } from "vue-router";
import { cn } from "@/lib/utils";

const tabs = [
  { name: "artists", label: "艺人" },
  { name: "users", label: "用户" },
  { name: "subscriptions", label: "订阅" },
  { name: "concerts", label: "演唱会" },
] as const;
</script>

<template>
  <div class="min-h-screen bg-background">
    <header class="border-b bg-card">
      <div class="mx-auto max-w-6xl px-6 py-4">
        <h1 class="text-lg font-semibold">演唱会信息 · 管理台</h1>
        <nav class="mt-3 flex gap-1">
          <RouterLink
            v-for="t in tabs"
            :key="t.name"
            :to="{ name: t.name }"
            custom
            v-slot="{ navigate, isActive }"
          >
            <button
              type="button"
              :class="
                cn(
                  'px-3 py-1.5 text-sm rounded-md transition-colors',
                  isActive
                    ? 'bg-secondary text-secondary-foreground'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent',
                )
              "
              @click="navigate"
            >
              {{ t.label }}
            </button>
          </RouterLink>
        </nav>
      </div>
    </header>
    <main class="mx-auto max-w-6xl px-6 py-6">
      <RouterView />
    </main>
  </div>
</template>
