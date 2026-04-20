<script setup lang="ts">
const props = defineProps<{ colspan: number }>();
</script>

<template>
  <tr>
    <td :colspan="props.colspan" class="p-8 text-center text-muted-foreground">
      <slot />
    </td>
  </tr>
</template>
