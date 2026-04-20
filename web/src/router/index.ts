import { createRouter, createWebHashHistory, type RouteRecordRaw } from "vue-router";
import { useAuth } from "@/stores/auth";

const routes: RouteRecordRaw[] = [
  {
    path: "/login",
    name: "login",
    component: () => import("@/views/LoginView.vue"),
    meta: { public: true },
  },
  {
    path: "/",
    component: () => import("@/views/AppLayout.vue"),
    children: [
      { path: "", redirect: { name: "artists" } },
      { path: "artists", name: "artists", component: () => import("@/views/ArtistsView.vue") },
      { path: "users", name: "users", component: () => import("@/views/UsersView.vue") },
      {
        path: "subscriptions",
        name: "subscriptions",
        component: () => import("@/views/SubscriptionsView.vue"),
      },
      { path: "concerts", name: "concerts", component: () => import("@/views/ConcertsView.vue") },
    ],
  },
  { path: "/:pathMatch(.*)*", redirect: { name: "artists" } },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

router.beforeEach((to) => {
  const { state } = useAuth();
  if (!to.meta.public && !state.authed) {
    return { name: "login", query: { redirect: to.fullPath } };
  }
  if (to.name === "login" && state.authed) {
    return { name: "artists" };
  }
});

export default router;
