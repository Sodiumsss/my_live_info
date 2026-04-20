<script setup lang="ts">
import { useToast } from "@/stores/toast";
import { cn } from "@/lib/utils";

const { state } = useToast();
</script>

<template>
  <Transition
    enter-active-class="transition-all duration-200"
    enter-from-class="opacity-0 translate-y-2"
    leave-active-class="transition-all duration-200"
    leave-to-class="opacity-0 translate-y-2"
  >
    <div
      v-if="state.visible"
      :class="
        cn(
          'fixed bottom-6 right-6 z-50 max-w-sm rounded-md px-4 py-2 text-sm shadow-lg',
          state.isError
            ? 'bg-destructive text-destructive-foreground'
            : 'bg-foreground text-background',
        )
      "
    >
      {{ state.message }}
    </div>
  </Transition>
</template>
