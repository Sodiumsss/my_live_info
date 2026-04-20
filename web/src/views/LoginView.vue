<script setup lang="ts">
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/stores/auth";

const router = useRouter();
const route = useRoute();
const { login, state } = useAuth();

const password = ref("");
const error = ref("");
const loading = ref(false);

async function onSubmit(e: Event) {
  e.preventDefault();
  error.value = "";
  if (state.configMissing) {
    error.value = "config.js 未加载或构建失败（缺少 GitHub Secrets?）";
    return;
  }
  loading.value = true;
  try {
    await login(password.value);
    const redirect = (route.query.redirect as string) || "/artists";
    await router.push(redirect);
  } catch (err) {
    console.error(err);
    error.value = "密钥错误，请重试";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center p-5 bg-muted/30">
    <Card class="w-full max-w-sm">
      <CardHeader>
        <CardTitle>演唱会信息 · 管理台</CardTitle>
        <CardDescription>使用 ADMIN_KEY 解密本地存储的 service key</CardDescription>
      </CardHeader>
      <CardContent>
        <form class="space-y-4" @submit="onSubmit">
          <div class="space-y-2">
            <Label for="admin-key">密钥</Label>
            <Input
              id="admin-key"
              v-model="password"
              type="password"
              autocomplete="off"
              autofocus
              required
            />
          </div>
          <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
          <Button type="submit" class="w-full" :disabled="loading">
            {{ loading ? "解密中…" : "进入" }}
          </Button>
        </form>
      </CardContent>
    </Card>
  </div>
</template>
