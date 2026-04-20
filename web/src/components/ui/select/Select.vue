<script setup lang="ts">
import { cn } from "@/lib/utils";

const props = defineProps<{
  modelValue?: string;
  required?: boolean;
  disabled?: boolean;
  class?: string;
}>();

const emit = defineEmits<{ "update:modelValue": [value: string] }>();
</script>

<template>
  <select
    :value="modelValue"
    :required="required"
    :disabled="disabled"
    :class="
      cn(
        'flex h-9 w-full items-center justify-between rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50',
        props.class,
      )
    "
    @change="emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
  >
    <slot />
  </select>
</template>
