<template>
  <div class="lf-container">
    <section class="hero">
      <span class="hero-eyebrow">校园失物招领 · 让物归原主</span>
      <h1 class="hero-title">每一件失物，<br />都值得被找回</h1>
      <p class="hero-sub">登记、发布、匹配、认领、归档 —— 一条清晰可查的归还之路</p>
      <div class="hero-search">
        <el-input
          v-model="keyword"
          size="large"
          placeholder="试试搜索：手机、校园卡、图书馆…"
          @keyup.enter="doSearch"
        >
          <template #append>
            <el-button type="primary" :icon="Search" @click="doSearch">搜索</el-button>
          </template>
        </el-input>
      </div>
      <div class="quick">
        <el-button v-if="store.isLogin" type="primary" size="large" round @click="$router.push('/found/new')">
          我要登记拾获
        </el-button>
        <el-button v-if="store.isLogin" size="large" round @click="$router.push('/lost/new')">我要发布寻物</el-button>
        <el-button v-else size="large" round @click="$router.push('/login')">登录后可登记</el-button>
      </div>
    </section>

    <section class="flow">
      <div v-for="(f, i) in flow" :key="i" class="flow-step">
        <span class="flow-no">{{ i + 1 }}</span>
        <div class="flow-text">
          <div class="flow-name">{{ f.name }}</div>
          <div class="flow-desc">{{ f.desc }}</div>
        </div>
      </div>
    </section>

    <section class="stats">
      <el-card v-for="s in statCards" :key="s.label" shadow="never" class="stat-card">
        <div class="stat-value">{{ s.value }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </el-card>
    </section>

    <section>
      <div class="section-head">
        <h2 class="lf-page-title">最新招领信息</h2>
        <el-link type="primary" @click="$router.push('/found')">查看全部</el-link>
      </div>
      <div v-if="loading" class="lf-muted">加载中…</div>
      <div v-else class="lf-grid">
        <ItemCard v-for="item in foundList" :key="item.id" :item="item" kind="found" />
      </div>
      <el-empty v-if="!loading && !foundList.length" description="暂无招领信息" />
    </section>

    <section v-if="hotLocations.length" style="margin-top: 24px">
      <h2 class="lf-page-title">高发地点 TOP5</h2>
      <el-card shadow="never">
        <div v-for="h in hotLocations" :key="h.zone" class="hot-row">
          <span>{{ h.zone }}</span>
          <el-progress
            :percentage="Math.round((h.count / maxHot) * 100)"
            :stroke-width="12"
            :show-text="false"
          />
          <span class="lf-muted">{{ h.count }} 条</span>
        </div>
      </el-card>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { fetchFoundList, fetchMeta } from '@/api/items'
import { fetchPublicStats } from '@/api/admin'
import ItemCard from '@/components/ItemCard.vue'

const store = useUserStore()
const router = useRouter()

const keyword = ref('')
const loading = ref(false)
const foundList = ref([])
const stats = ref({})
const hotLocations = ref([])

const flow = [
  { name: '拾获登记', desc: '捡到东西先记录' },
  { name: '信息发布', desc: '生成招领卡片' },
  { name: '检索匹配', desc: '智能推荐失主' },
  { name: '认领确认', desc: '核对后当面归还' },
  { name: '结果归档', desc: '全流程留痕可溯' }
]

const statCards = computed(() => [
  { label: '招领信息总数', value: stats.value.found_total ?? '-' },
  { label: '寻物启事总数', value: stats.value.lost_total ?? '-' },
  { label: '已成功认领', value: stats.value.found_claimed ?? '-' },
  { label: '认领率', value: stats.value.claim_rate ?? '-' }
])

const maxHot = computed(() => Math.max(1, ...hotLocations.value.map((h) => h.count)))

async function loadStats() {
  try {
    const res = await fetchPublicStats()
    stats.value = res.data || {}
    hotLocations.value = res.data?.hot_locations || []
  } catch (e) {
    /* 统计失败不影响首页 */
  }
}

async function loadLatest(params = {}) {
  loading.value = true
  try {
    const res = await fetchFoundList({ page: 1, ...params })
    foundList.value = res.data?.items || []
  } catch (e) {
    foundList.value = []
  } finally {
    loading.value = false
  }
}

function doSearch() {
  if (!keyword.value.trim()) return
  router.push({ path: '/found', query: { kw: keyword.value.trim() } })
}

onMounted(async () => {
  fetchMeta() // 预热字典缓存
  await Promise.all([loadStats(), loadLatest({ status: 'unclaimed' })])
})
</script>

<style scoped>
.hero {
  text-align: center;
  padding: 52px 20px 44px;
  margin-bottom: 20px;
  background:
    radial-gradient(120% 120% at 50% -10%, var(--lf-primary-soft) 0%, rgba(241, 248, 246, 0) 55%),
    var(--lf-card);
  border: 1px solid var(--lf-border);
  border-radius: var(--lf-radius-lg);
  box-shadow: var(--lf-shadow-sm);
}
.hero-eyebrow {
  display: inline-block;
  font-family: var(--lf-font-body);
  font-size: 12.5px;
  font-weight: 600;
  letter-spacing: 1.5px;
  color: var(--lf-primary);
  background: var(--lf-primary-light);
  padding: 5px 14px;
  border-radius: 999px;
  margin-bottom: 18px;
}
.hero-title {
  margin: 0 0 12px;
  font-family: var(--lf-font-display);
  font-size: var(--lf-fs-display);
  font-weight: 700;
  line-height: 1.28;
  letter-spacing: 0.5px;
  color: var(--lf-text);
}
.hero-sub {
  margin: 0;
  font-size: 14px;
  color: var(--lf-muted);
  letter-spacing: 0.5px;
}
.hero-search {
  width: min(560px, 92%);
  margin: 24px auto 16px;
}
.quick {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

/* 流程条：真实有序的归还链路，编号在此是成立的 */
.flow {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 28px;
}
.flow-step {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--lf-card);
  border: 1px solid var(--lf-border);
  border-radius: var(--lf-radius-md);
  padding: 14px 14px;
  box-shadow: var(--lf-shadow-sm);
}
.flow-no {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--lf-primary);
  color: #fff;
  font-family: var(--lf-font-display);
  font-size: 13px;
  font-weight: 600;
}
.flow-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--lf-text);
}
.flow-desc {
  font-size: 12px;
  color: var(--lf-muted);
  margin-top: 1px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--lf-gap);
  margin-bottom: 28px;
}
.stat-card {
  text-align: center;
  border-radius: var(--lf-radius-md);
  border-top: 3px solid var(--lf-primary);
}
.stat-card :deep(.el-card__body) {
  padding: 18px 12px;
}
.stat-value {
  font-family: var(--lf-font-display);
  font-size: 26px;
  font-weight: 700;
  color: var(--lf-primary);
  line-height: 1.3;
}
.stat-label {
  margin-top: 2px;
  font-size: 13px;
  color: var(--lf-muted);
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.section-head .lf-page-title {
  margin: 0;
}
.hot-row {
  display: grid;
  grid-template-columns: 90px 1fr 60px;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
  font-size: 13px;
}
@media (max-width: 992px) {
  .flow {
    grid-template-columns: repeat(3, 1fr);
  }
}
@media (max-width: 768px) {
  .hero {
    padding: 34px 16px;
  }
  .hero-title {
    font-size: 23px;
  }
  .stat-value {
    font-size: 22px;
  }
  .flow {
    grid-template-columns: repeat(2, 1fr);
  }
  .flow-desc {
    display: none;
  }
}
</style>
