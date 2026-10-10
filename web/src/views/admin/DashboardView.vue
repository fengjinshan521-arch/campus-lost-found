<template>
  <div class="lf-container" v-loading="loading">
    <div class="head">
      <h2 class="lf-page-title">数据统计看板</h2>
      <div>
        <el-button @click="runMatch">全量重算匹配</el-button>
        <el-button v-if="store.isAdmin" type="primary" @click="dialog = true">发布公告</el-button>
      </div>
    </div>

    <div class="cards">
      <el-card v-for="c in cards" :key="c.label" shadow="never">
        <div class="value">{{ c.value }}</div>
        <div class="lf-muted">{{ c.label }}</div>
      </el-card>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :md="14">
        <el-card shadow="never">
          <template #header>近 14 日登记趋势</template>
          <div ref="trendRef" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="10">
        <el-card shadow="never">
          <template #header>物品状态分布</template>
          <div ref="pipelineRef" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :xs="24" :md="12">
        <el-card shadow="never">
          <template #header>分类分布 TOP8</template>
          <el-table :data="categoryTop" size="small" border>
            <el-table-column prop="name" label="分类" />
            <el-table-column prop="found" label="拾获" width="90" />
            <el-table-column prop="lost" label="寻物" width="90" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card shadow="never">
          <template #header>高发地点 TOP8</template>
          <el-table :data="stats.hot_locations || []" size="small" border>
            <el-table-column prop="zone" label="分区" />
            <el-table-column prop="count" label="数量" width="90" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="dialog" title="发布系统公告" width="480px">
      <el-form :model="notice" label-width="70px">
        <el-form-item label="标题">
          <el-input v-model="notice.title" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="notice.content" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="sendBroadcast">发送</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { useUserStore } from '@/stores/user'
import { fetchStats, runFullMatch, broadcast } from '@/api/admin'

const store = useUserStore()
const stats = ref({})
const loading = ref(false)
const dialog = ref(false)
const notice = ref({ title: '', content: '' })

const trendRef = ref()
const pipelineRef = ref()
let trendChart = null
let pipelineChart = null

const cards = computed(() => {
  const o = stats.value.overview || {}
  return [
    { label: '拾获登记总数', value: o.found_total ?? '-' },
    { label: '寻物启事总数', value: o.lost_total ?? '-' },
    { label: '待确认物品', value: o.found_pending ?? '-' },
    { label: '认领率', value: stats.value.claim_rate?.rate_percent ?? '-' },
    { label: '认领单总数', value: o.claim_total ?? '-' },
    { label: '平均处理时长(小时)', value: stats.value.avg_handle_hours ?? '-' },
    { label: '注册用户', value: o.user_total ?? '-' },
    { label: '匹配记录', value: o.match_total ?? '-' }
  ]
})

const categoryTop = computed(() => (stats.value.category_distribution || []).slice(0, 8))

function renderCharts() {
  const trend = stats.value.trend || []
  if (trendRef.value) {
    trendChart = trendChart || echarts.init(trendRef.value)
    trendChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['拾获', '寻物'] },
      xAxis: { type: 'category', data: trend.map((t) => t.date) },
      yAxis: { type: 'value', minInterval: 1 },
      color: ['#0f7b72', '#e08a1e', '#1f9d6b', '#d9534f', '#3f9a91', '#7c8a85'],
      series: [
        { name: '拾获', type: 'line', smooth: true, data: trend.map((t) => t.found), itemStyle: { color: '#0f7b72' }, lineStyle: { color: '#0f7b72' } },
        { name: '寻物', type: 'line', smooth: true, data: trend.map((t) => t.lost), itemStyle: { color: '#e8930c' }, lineStyle: { color: '#e8930c' } }
      ]
    })
  }

  const pipeline = stats.value.status_pipeline || []
  if (pipelineRef.value) {
    pipelineChart = pipelineChart || echarts.init(pipelineRef.value)
    pipelineChart.setOption({
      tooltip: { trigger: 'item' },
      color: ['#0f7b72', '#e08a1e', '#1f9d6b', '#d9534f', '#3f9a91', '#7c8a85'],
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          data: pipeline.map((p) => ({ name: p.label, value: p.count }))
        }
      ]
    })
  }
}

async function load() {
  loading.value = true
  try {
    const res = await fetchStats()
    stats.value = res.data || {}
    renderCharts()
  } finally {
    loading.value = false
  }
}

async function runMatch() {
  const res = await runFullMatch()
  ElMessage.success(res.msg || '匹配完成')
  load()
}

async function sendBroadcast() {
  if (!notice.value.title.trim()) {
    ElMessage.warning('请填写公告标题')
    return
  }
  const res = await broadcast(notice.value)
  ElMessage.success(res.msg || '已发送')
  dialog.value = false
  notice.value = { title: '', content: '' }
}

watch(() => stats.value, renderCharts, { deep: true })

onMounted(() => {
  load()
  window.addEventListener('resize', () => {
    trendChart?.resize()
    pipelineChart?.resize()
  })
})
</script>

<style scoped>
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.value {
  font-size: 22px;
  font-weight: 700;
  color: var(--lf-primary);
}
</style>
