<script setup lang="ts">
import { cn } from "@/lib/utils";
import { buttonVariants, type ButtonVariants } from "./variants";

const props = defineProps<{
  variant?: ButtonVariants["variant"];
  size?: ButtonVariants["size"];
  type?: "button" | "submit" | "reset";
  disabled?: boolean;
  class?: string;
}>();
</script>

<template>
  <button
    :type="props.type ?? 'button'"
    :disabled="disabled"
    :class="cn(buttonVariants({ variant, size }), props.class)"
  >
    <slot />
  </button>
</template>
