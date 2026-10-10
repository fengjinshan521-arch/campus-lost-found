<template>
  <div class="lf-app">
    <header class="lf-header">
      <div class="lf-header-inner">
        <router-link to="/" class="lf-logo">
          <span class="lf-logo-mark">
            <el-icon :size="16"><Search /></el-icon>
          </span>
          <span class="lf-logo-text">校园失物招领平台</span>
        </router-link>

        <!-- 桌面端：横向菜单 -->
        <el-menu :default-active="activeMenu" mode="horizontal" :ellipsis="false" router class="lf-nav-desktop">
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item index="/found">招领信息</el-menu-item>
          <el-menu-item index="/lost">寻物启事</el-menu-item>
          <el-menu-item v-if="store.isLogin" index="/found/new">拾获登记</el-menu-item>
          <el-menu-item v-if="store.isLogin" index="/lost/new">发布寻物</el-menu-item>
          <el-menu-item v-if="store.isLogin" index="/mine">我的发布</el-menu-item>
          <el-menu-item v-if="store.isLogin" index="/claims">认领管理</el-menu-item>
          <el-sub-menu v-if="store.isStaff" index="/admin">
            <template #title>后台管理</template>
            <el-menu-item index="/admin">统计看板</el-menu-item>
            <template v-if="store.isAdmin">
              <el-menu-item index="/admin/users">用户管理</el-menu-item>
              <el-menu-item index="/admin/categories">分类管理</el-menu-item>
              <el-menu-item index="/admin/logs">系统日志</el-menu-item>
              <el-menu-item index="/admin/admins">管理员管理</el-menu-item>
            </template>
          </el-sub-menu>
        </el-menu>

        <div class="lf-header-actions">
          <el-badge v-if="store.isLogin" :value="unread" :hidden="!unread" :max="99">
            <el-button text @click="$router.push('/notifications')">
              <el-icon><Bell /></el-icon>
              <span class="action-text">通知</span>
            </el-button>
          </el-badge>
          <template v-if="store.isLogin">
            <el-dropdown @command="onCommand">
              <span class="lf-user">
                <span class="lf-user-avatar">{{ avatarChar }}</span>
                <span class="lf-user-name">{{ store.displayName }}</span>
                <el-tag size="small" effect="plain">{{ roleLabel }}</el-tag>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                  <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <el-button text @click="$router.push('/login')">登录</el-button>
            <el-button type="primary" round @click="$router.push('/register')">注册</el-button>
          </template>

          <!-- 移动端：汉堡按钮 -->
          <el-button class="lf-nav-toggle" text @click="drawerOpen = true">
            <el-icon :size="20"><Menu /></el-icon>
          </el-button>
        </div>
      </div>
    </header>

    <!-- 移动端：抽屉导航 -->
    <el-drawer v-model="drawerOpen" title="导航菜单" size="72%" :with-header="true" direction="ltr">
      <el-menu :default-active="activeMenu" router @select="drawerOpen = false" class="lf-nav-mobile">
        <el-menu-item index="/">首页</el-menu-item>
        <el-menu-item index="/found">招领信息</el-menu-item>
        <el-menu-item index="/lost">寻物启事</el-menu-item>
        <template v-if="store.isLogin">
          <el-menu-item index="/found/new">拾获登记</el-menu-item>
          <el-menu-item index="/lost/new">发布寻物</el-menu-item>
          <el-menu-item index="/mine">我的发布</el-menu-item>
          <el-menu-item index="/claims">认领管理</el-menu-item>
        </template>
        <el-sub-menu v-if="store.isStaff" index="/admin">
          <template #title>后台管理</template>
          <el-menu-item index="/admin">统计看板</el-menu-item>
          <template v-if="store.isAdmin">
            <el-menu-item index="/admin/users">用户管理</el-menu-item>
            <el-menu-item index="/admin/categories">分类管理</el-menu-item>
            <el-menu-item index="/admin/logs">系统日志</el-menu-item>
            <el-menu-item index="/admin/admins">管理员管理</el-menu-item>
          </template>
        </el-sub-menu>
      </el-menu>
    </el-drawer>

    <main>
      <router-view />
    </main>

    <footer class="lf-footer">
      校园失物招领信息平台 · 拾获登记 → 信息发布 → 检索匹配 → 认领确认 → 结果归档（全流程可追溯）
    </footer>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, Menu, Search } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { fetchUnreadCount } from '@/api/notify'
import { ElMessage } from 'element-plus'

const store = useUserStore()
const router = useRouter()
const unread = ref(0)
const drawerOpen = ref(false)

const roleLabel = computed(() => {
  const map = { student: '学生', staff: '楼管', admin: '管理员' }
  return map[store.user?.role] || ''
})

const avatarChar = computed(() => (store.displayName || '客').trim().charAt(0))

const activeMenu = computed(() => {
  const path = router.currentRoute.value.path
  if (path.startsWith('/found')) return '/found'
  if (path.startsWith('/lost')) return '/lost'
  if (path.startsWith('/claims')) return '/claims'
  if (path.startsWith('/admin')) return path
  return '/'
})

async function refreshUnread() {
  if (!store.isLogin) {
    unread.value = 0
    return
  }
  try {
    const res = await fetchUnreadCount()
    unread.value = res.data?.unread_count || 0
  } catch (e) {
    unread.value = 0
  }
}

function onCommand(cmd) {
  if (cmd === 'profile') router.push('/profile')
  if (cmd === 'logout') {
    store.logout()
    ElMessage.success('已退出登录')
    router.push('/')
  }
}

onMounted(refreshUnread)
watch(() => store.isLogin, refreshUnread)
watch(() => router.currentRoute.value.fullPath, refreshUnread)
</script>

<style scoped>
.lf-app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

main {
  flex: 1;
}

.lf-logo-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: var(--lf-primary);
  color: #fff;
  flex-shrink: 0;
}

.lf-header-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.action-text {
  margin-left: 4px;
}

.lf-user {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: var(--lf-text);
  padding: 4px 8px;
  border-radius: var(--lf-radius-sm);
  transition: background-color 0.15s ease;
}

.lf-user:hover {
  background: var(--lf-primary-light);
}

.lf-user-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--lf-primary-light);
  color: var(--lf-primary);
  font-size: 13px;
  font-weight: 600;
}

.lf-user-name {
  max-width: 96px;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 移动端汉堡按钮默认隐藏 */
.lf-nav-toggle {
  display: none;
}

.lf-nav-mobile .el-menu-item {
  font-size: 15px;
}

@media (max-width: 992px) {
  .lf-nav-desktop {
    display: none;
  }
  .lf-nav-toggle {
    display: inline-flex;
  }
  .action-text,
  .lf-user-name {
    display: none;
  }
}
</style>
