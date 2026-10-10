<template>
  <div class="lf-container" v-loading="loading">
    <div class="head">
      <h2 class="lf-page-title">通知中心</h2>
      <el-button :disabled="!unread" @click="readAll">全部标记为已读</el-button>
    </div>

    <el-empty v-if="!list.length" description="暂无通知" />
    <el-card v-for="n in list" :key="n.id" shadow="never" class="notify" :class="{ unread: !n.is_read }">
      <div class="row">
        <div>
          <div class="n-title">
            <el-tag size="small" :type="typeTag(n.type)">{{ typeLabel(n.type) }}</el-tag>
            {{ n.title }}
          </div>
          <div class="lf-muted">{{ n.created_at }}</div>
          <div class="n-content">{{ n.content }}</div>
        </div>
        <div class="ops">
          <el-button v-if="n.link" link type="primary" @click="go(n)">查看</el-button>
          <el-button v-if="!n.is_read" link @click="read(n)">标记已读</el-button>
        </div>
      </div>
    </el-card>

    <div class="pager">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next, total"
        @current-change="load"
      />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchNotifications, markAllRead, markRead } from '@/api/notify'

const router = useRouter()
const list = ref([])
const unread = ref(0)
const page = ref(1)
const pageSize = ref(12)
const total = ref(0)
const loading = ref(false)

const TYPE_MAP = {
  match: ['匹配推荐', 'warning'],
  claim: ['认领申请', 'primary'],
  result: ['审核结果', 'success'],
  system: ['系统通知', 'info']
}

const typeLabel = (t) => TYPE_MAP[t]?.[0] || '通知'
const typeTag = (t) => TYPE_MAP[t]?.[1] || 'info'

async function load() {
  loading.value = true
  try {
    const res = await fetchNotifications({ page: page.value })
    const data = res.data || {}
    list.value = data.list?.items || []
    total.value = data.list?.total || 0
    pageSize.value = data.list?.per_page || 12
    unread.value = data.unread_count || 0
  } finally {
    loading.value = false
  }
}

async function read(n) {
  await markRead(n.id)
  n.is_read = true
  unread.value = Math.max(0, unread.value - 1)
}

async function readAll() {
  const res = await markAllRead()
  ElMessage.success(res.msg || '已全部标记已读')
  load()
}

function go(n) {
  if (n.link) router.push(n.link)
}

onMounted(load)
</script>

<style scoped>
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.notify {
  margin-bottom: 10px;
}
.notify.unread {
  border-left: 3px solid var(--lf-primary);
}
.row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}
.n-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 4px;
}
.n-content {
  margin-top: 6px;
  color: var(--lf-text-regular);
  line-height: 1.6;
}
.ops {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}
.pager {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}
</style>
