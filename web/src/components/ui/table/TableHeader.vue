<script setup lang="ts">
import { cn } from "@/lib/utils";
const props = defineProps<{ class?: string }>();
</script>

<template>
  <thead :class="cn('[&_tr]:border-b bg-muted/50', props.class)"><slot /></thead>
</template>
