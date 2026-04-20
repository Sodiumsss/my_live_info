<script setup lang="ts">
import { cn } from "@/lib/utils";
const props = defineProps<{ class?: string }>();
</script>

<template>
  <div class="relative w-full overflow-auto rounded-md border">
    <table :class="cn('w-full caption-bottom text-sm', props.class)">
      <slot />
    </table>
  </div>
</template>
