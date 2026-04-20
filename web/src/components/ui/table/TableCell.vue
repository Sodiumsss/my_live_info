<script setup lang="ts">
import { cn } from "@/lib/utils";
const props = defineProps<{ class?: string; colspan?: number }>();
</script>

<template>
  <td
    :colspan="colspan"
    :class="cn('p-3 align-middle', props.class)"
  >
    <slot />
  </td>
</template>
