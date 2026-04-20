<script setup lang="ts">
import { onMounted, ref } from "vue";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
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
import { useData } from "@/stores/data";
import { useToast } from "@/stores/toast";
import { fmtDate } from "@/lib/utils";

interface Sub {
  user_id: string;
  artist_id: string;
  created_at: string;
  users: { name: string } | null;
  artists: { canonical_name: string } | null;
}

const { state, loadArtists, loadUsers } = useData();
const { show } = useToast();

const subs = ref<Sub[]>([]);
const userId = ref("");
const artistId = ref("");
const loading = ref(false);

async function loadSubs() {
  loading.value = true;
  const { data, error } = await supabase()
    .from("subscriptions")
    .select("user_id, artist_id, created_at, users(name), artists(canonical_name)")
    .order("created_at", { ascending: false });
  loading.value = false;
  if (error) {
    show(error.message, true);
    return;
  }
  subs.value = (data ?? []) as unknown as Sub[];
}

onMounted(async () => {
  try {
    await Promise.all([loadArtists(), loadUsers(), loadSubs()]);
  } catch (e) {
    show((e as Error).message, true);
  }
});

async function add(e: Event) {
  e.preventDefault();
  if (!userId.value || !artistId.value) {
    show("请选择用户和艺人", true);
    return;
  }
  const { error } = await supabase()
    .from("subscriptions")
    .upsert(
      { user_id: userId.value, artist_id: artistId.value },
      { onConflict: "user_id,artist_id", ignoreDuplicates: true },
    );
  if (error) {
    show(error.message, true);
    return;
  }
  userId.value = "";
  artistId.value = "";
  await loadSubs();
  show("已订阅");
}

async function remove(s: Sub) {
  const uname = s.users?.name ?? s.user_id;
  const aname = s.artists?.canonical_name ?? s.artist_id;
  if (!window.confirm(`退订「${uname}」对「${aname}」的订阅？`)) return;
  const { error } = await supabase()
    .from("subscriptions")
    .delete()
    .eq("user_id", s.user_id)
    .eq("artist_id", s.artist_id);
  if (error) {
    show(error.message, true);
    return;
  }
  await loadSubs();
  show("已退订");
}
</script>

<template>
  <div class="space-y-4">
    <form class="flex flex-wrap gap-2" @submit="add">
      <Select v-model="userId" required class="w-48">
        <option value="">选择用户</option>
        <option v-for="u in state.users" :key="u.id" :value="u.id">{{ u.name }}</option>
      </Select>
      <Select v-model="artistId" required class="w-48">
        <option value="">选择艺人</option>
        <option v-for="a in state.artists" :key="a.id" :value="a.id">
          {{ a.canonical_name }}
        </option>
      </Select>
      <Button type="submit">订阅</Button>
    </form>

    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>用户</TableHead>
          <TableHead>艺人</TableHead>
          <TableHead>订阅时间</TableHead>
          <TableHead class="w-24"></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableEmpty v-if="!subs.length && !loading" :colspan="4">暂无订阅关系</TableEmpty>
        <TableRow v-for="s in subs" :key="`${s.user_id}-${s.artist_id}`">
          <TableCell class="font-medium">{{ s.users?.name ?? s.user_id }}</TableCell>
          <TableCell>{{ s.artists?.canonical_name ?? s.artist_id }}</TableCell>
          <TableCell class="text-muted-foreground">{{ fmtDate(s.created_at) }}</TableCell>
          <TableCell class="text-right">
            <Button variant="destructive" size="sm" @click="remove(s)">退订</Button>
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  </div>
</template>
