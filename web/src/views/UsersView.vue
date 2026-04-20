<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Card, CardContent } from "@/components/ui/card";
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
import { useData, type User } from "@/stores/data";
import { useToast } from "@/stores/toast";

const { state, loadUsers } = useData();
const { show } = useToast();

interface Form {
  id: string | null;
  name: string;
  email: string;
  feishu_webhook: string;
  notify_on_status_change: boolean;
}

const initialForm = (): Form => ({
  id: null,
  name: "",
  email: "",
  feishu_webhook: "",
  notify_on_status_change: true,
});

const form = reactive<Form>(initialForm());
const editing = ref(false);

onMounted(async () => {
  try {
    await loadUsers();
  } catch (e) {
    show((e as Error).message, true);
  }
});

function startEdit(u: User) {
  form.id = u.id;
  form.name = u.name;
  form.email = u.email ?? "";
  form.feishu_webhook = u.feishu_webhook ?? "";
  form.notify_on_status_change = u.notify_on_status_change;
  editing.value = true;
}

function reset() {
  Object.assign(form, initialForm());
  editing.value = false;
}

async function submit(e: Event) {
  e.preventDefault();
  if (!form.name.trim()) {
    show("昵称必填", true);
    return;
  }
  if (!form.email.trim() && !form.feishu_webhook.trim()) {
    show("至少填一个通知渠道（邮箱或飞书 webhook）", true);
    return;
  }
  const payload = {
    name: form.name.trim(),
    email: form.email.trim() || null,
    feishu_webhook: form.feishu_webhook.trim() || null,
    notify_on_status_change: form.notify_on_status_change,
  };
  const { error } = form.id
    ? await supabase().from("users").update(payload).eq("id", form.id)
    : await supabase().from("users").insert(payload);
  if (error) {
    show(error.message, true);
    return;
  }
  const wasEditing = editing.value;
  reset();
  await loadUsers();
  show(wasEditing ? "已更新" : "已添加");
}

async function remove(u: User) {
  if (!window.confirm(`删除用户「${u.name}」？其所有订阅会级联删除。`)) return;
  const { error } = await supabase().from("users").delete().eq("id", u.id);
  if (error) {
    show(error.message, true);
    return;
  }
  await loadUsers();
  show("已删除");
}
</script>

<template>
  <div class="space-y-4">
    <Card>
      <CardContent class="pt-6">
        <form class="space-y-4" @submit="submit">
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="space-y-2">
              <Label for="user-name">昵称</Label>
              <Input id="user-name" v-model="form.name" required />
            </div>
            <div class="space-y-2">
              <Label for="user-email">邮箱</Label>
              <Input id="user-email" v-model="form.email" type="email" />
            </div>
            <div class="space-y-2 sm:col-span-2">
              <Label for="user-feishu">飞书 webhook</Label>
              <Input
                id="user-feishu"
                v-model="form.feishu_webhook"
                type="url"
                placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/..."
              />
            </div>
          </div>
          <div class="flex items-center gap-2">
            <Checkbox id="user-notify" v-model="form.notify_on_status_change" />
            <Label for="user-notify">接收状态变更通知</Label>
          </div>
          <div class="flex gap-2">
            <Button type="submit">{{ editing ? "保存" : "添加" }}</Button>
            <Button v-if="editing" type="button" variant="outline" @click="reset">
              取消编辑
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>

    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>昵称</TableHead>
          <TableHead>邮箱</TableHead>
          <TableHead>飞书</TableHead>
          <TableHead>状态通知</TableHead>
          <TableHead class="w-32"></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableEmpty v-if="!state.users.length" :colspan="5">暂无用户</TableEmpty>
        <TableRow v-for="u in state.users" :key="u.id">
          <TableCell class="font-medium">{{ u.name }}</TableCell>
          <TableCell>{{ u.email || "" }}</TableCell>
          <TableCell>{{ u.feishu_webhook ? "✓" : "" }}</TableCell>
          <TableCell>{{ u.notify_on_status_change ? "✓" : "" }}</TableCell>
          <TableCell class="text-right space-x-1">
            <Button variant="outline" size="sm" @click="startEdit(u)">编辑</Button>
            <Button variant="destructive" size="sm" @click="remove(u)">删除</Button>
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  </div>
</template>
