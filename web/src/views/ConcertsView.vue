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

interface Concert {
  id: string;
  city: string;
  show_date: string;
  venue: string | null;
  status: string;
  sale_status: string;
  sale_open_at: string | null;
  source_url: string | null;
  artist_id: string;
  artists: { canonical_name: string } | null;
}

const { state, loadArtists } = useData();
const { show } = useToast();

const concerts = ref<Concert[]>([]);
const loading = ref(false);
const filterArtist = ref("");
const filterStatus = ref("");
const filterSale = ref("");

async function load() {
  loading.value = true;
  let q = supabase()
    .from("concerts")
    .select(
      "id, city, show_date, venue, status, sale_status, sale_open_at, source_url, artist_id, artists(canonical_name)",
    )
    .order("show_date", { ascending: false })
    .limit(200);
  if (filterArtist.value) q = q.eq("artist_id", filterArtist.value);
  if (filterStatus.value) q = q.eq("status", filterStatus.value);
  if (filterSale.value) q = q.eq("sale_status", filterSale.value);
  const { data, error } = await q;
  loading.value = false;
  if (error) {
    show(error.message, true);
    concerts.value = [];
    return;
  }
  concerts.value = (data ?? []) as unknown as Concert[];
}

onMounted(async () => {
  try {
    await loadArtists();
    await load();
  } catch (e) {
    show((e as Error).message, true);
  }
});
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap gap-2 items-center">
      <Select v-model="filterArtist" class="w-48" @update:model-value="load">
        <option value="">全部艺人</option>
        <option v-for="a in state.artists" :key="a.id" :value="a.id">
          {{ a.canonical_name }}
        </option>
      </Select>
      <Select v-model="filterStatus" class="w-40" @update:model-value="load">
        <option value="">全部状态</option>
        <option value="verified">verified</option>
        <option value="unverified">unverified</option>
      </Select>
      <Select v-model="filterSale" class="w-44" @update:model-value="load">
        <option value="">全部开票状态</option>
        <option value="announced">announced</option>
        <option value="on_sale">on_sale</option>
        <option value="sold_out">sold_out</option>
        <option value="unknown">unknown</option>
      </Select>
      <Button @click="load">刷新</Button>
    </div>

    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>艺人</TableHead>
          <TableHead>城市</TableHead>
          <TableHead>日期</TableHead>
          <TableHead>场馆</TableHead>
          <TableHead>状态</TableHead>
          <TableHead>开票</TableHead>
          <TableHead>开票时间</TableHead>
          <TableHead>来源</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableEmpty v-if="loading" :colspan="8">加载中…</TableEmpty>
        <TableEmpty v-else-if="!concerts.length" :colspan="8">无数据</TableEmpty>
        <TableRow v-for="c in concerts" :key="c.id">
          <TableCell class="font-medium">{{ c.artists?.canonical_name ?? "" }}</TableCell>
          <TableCell>{{ c.city }}</TableCell>
          <TableCell>{{ c.show_date }}</TableCell>
          <TableCell>{{ c.venue ?? "" }}</TableCell>
          <TableCell>{{ c.status }}</TableCell>
          <TableCell>{{ c.sale_status }}</TableCell>
          <TableCell>{{ c.sale_open_at ? fmtDate(c.sale_open_at) : "" }}</TableCell>
          <TableCell>
            <a
              v-if="c.source_url"
              :href="c.source_url"
              target="_blank"
              rel="noopener"
              class="text-primary underline-offset-4 hover:underline"
            >
              链接
            </a>
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  </div>
</template>
