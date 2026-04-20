<script setup lang="ts">
import { cn } from "@/lib/utils";

const props = defineProps<{
  modelValue?: boolean;
  id?: string;
  disabled?: boolean;
  class?: string;
}>();

const emit = defineEmits<{ "update:modelValue": [value: boolean] }>();
</script>

<template>
  <input
    :id="id"
    type="checkbox"
    :checked="modelValue"
    :disabled="disabled"
    :class="
      cn(
        'h-4 w-4 shrink-0 rounded-sm border border-primary shadow focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 accent-primary',
        props.class,
      )
    "
    @change="emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
  />
</template>
