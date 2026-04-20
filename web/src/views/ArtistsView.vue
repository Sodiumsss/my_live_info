<script setup lang="ts">
import { onMounted, ref } from "vue";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  TableEmpty,
} from "@/components/ui/table";
import { supabase } from "@/lib/supabase";
import { useData, type Artist } from "@/stores/data";
import { useToast } from "@/stores/toast";
import { fmtDate } from "@/lib/utils";

const { state, loadArtists } = useData();
const { show } = useToast();

const newName = ref("");

onMounted(async () => {
  try {
    await loadArtists();
  } catch (e) {
    show((e as Error).message, true);
  }
});

async function add(e: Event) {
  e.preventDefault();
  const name = newName.value.trim();
  if (!name) return;
  const { error } = await supabase()
    .from("artists")
    .upsert({ canonical_name: name }, { onConflict: "canonical_name", ignoreDuplicates: true });
  if (error) {
    show(error.message, true);
    return;
  }
  newName.value = "";
  await loadArtists();
  show(`已添加：${name}`);
}

async function remove(a: Artist) {
  if (!window.confirm(`删除艺人「${a.canonical_name}」？相关订阅和演唱会会级联删除。`)) return;
  const { error } = await supabase().from("artists").delete().eq("id", a.id);
  if (error) {
    show(error.message, true);
    return;
  }
  await loadArtists();
  show("已删除");
}
</script>

<template>
  <div class="space-y-4">
    <form class="flex gap-2" @submit="add">
      <Input v-model="newName" placeholder="艺人规范名 (canonical_name)" required class="max-w-sm" />
      <Button type="submit">添加</Button>
    </form>

    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>名字</TableHead>
          <TableHead>添加时间</TableHead>
          <TableHead class="w-24"></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableEmpty v-if="!state.artists.length" :colspan="3">
          暂无艺人，先添加一个
        </TableEmpty>
        <TableRow v-for="a in state.artists" :key="a.id">
          <TableCell class="font-medium">{{ a.canonical_name }}</TableCell>
          <TableCell class="text-muted-foreground">{{ fmtDate(a.created_at) }}</TableCell>
          <TableCell class="text-right">
            <Button variant="destructive" size="sm" @click="remove(a)">删除</Button>
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  </div>
</template>
