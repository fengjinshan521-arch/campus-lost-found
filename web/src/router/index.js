import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const routes = [
  { path: '/', name: 'home', component: () => import('@/views/HomeView.vue') },
  { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
  { path: '/register', name: 'register', component: () => import('@/views/RegisterView.vue') },
  { path: '/forgot', name: 'forgot', component: () => import('@/views/ForgotPasswordView.vue') },

  { path: '/found', name: 'found-list', component: () => import('@/views/items/FoundListView.vue') },
  { path: '/lost', name: 'lost-list', component: () => import('@/views/items/LostListView.vue') },
  {
    path: '/found/:id',
    name: 'found-detail',
    component: () => import('@/views/items/ItemDetailView.vue'),
    meta: { kind: 'found' }
  },
  {
    path: '/lost/:id',
    name: 'lost-detail',
    component: () => import('@/views/items/ItemDetailView.vue'),
    meta: { kind: 'lost' }
  },
  {
    path: '/found/new',
    name: 'found-new',
    component: () => import('@/views/items/FoundFormView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/lost/new',
    name: 'lost-new',
    component: () => import('@/views/items/LostFormView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/mine',
    name: 'my-items',
    component: () => import('@/views/items/MyItemsView.vue'),
    meta: { requiresAuth: true }
  },

  {
    path: '/claims/new',
    name: 'claim-new',
    component: () => import('@/views/claims/ClaimFormView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/claims',
    name: 'claim-list',
    component: () => import('@/views/claims/ClaimListView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/claims/:id',
    name: 'claim-detail',
    component: () => import('@/views/claims/ClaimDetailView.vue'),
    meta: { requiresAuth: true }
  },

  {
    path: '/notifications',
    name: 'notifications',
    component: () => import('@/views/notify/NotifyView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { requiresAuth: true }
  },

  {
    path: '/admin',
    name: 'admin-dashboard',
    component: () => import('@/views/admin/DashboardView.vue'),
    meta: { requiresStaff: true }
  },
  {
    path: '/admin/users',
    name: 'admin-users',
    component: () => import('@/views/admin/UsersView.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/categories',
    name: 'admin-categories',
    component: () => import('@/views/admin/CategoriesView.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/logs',
    name: 'admin-logs',
    component: () => import('@/views/admin/LogsView.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/admins',
    name: 'admin-admins',
    component: () => import('@/views/admin/AdminsView.vue'),
    meta: { requiresAdmin: true }
  },

  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

router.beforeEach(async (to) => {
  const store = useUserStore()
  if (!store.loaded) await store.load()

  if (to.meta.requiresAuth && !store.isLogin) {
    ElMessage.warning('请先登录')
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.meta.requiresAdmin && !store.isAdmin) {
    ElMessage.error('仅管理员可访问')
    return { path: '/' }
  }
  if (to.meta.requiresStaff && !store.isStaff) {
    ElMessage.error('仅楼管/管理员可访问')
    return { path: '/' }
  }
  return true
})

export default router
