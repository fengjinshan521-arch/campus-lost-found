<template>
  <div class="lf-container" v-loading="loading">
    <h2 class="lf-page-title">操作日志追溯</h2>

    <div class="filters">
      <el-input v-model="action" placeholder="动作，如 claim_approve" clearable style="width: 220px" @keyup.enter="load" />
      <el-input v-model="targetType" placeholder="对象类型：found_item / claim" clearable style="width: 220px" />
      <el-input v-model="targetId" placeholder="对象 ID" clearable style="width: 140px" />
      <el-button type="primary" @click="trace">按对象追溯</el-button>
      <el-button @click="load">查看全部</el-button>
    </div>

    <el-card v-if="timeline.length" shadow="never" style="margin-bottom: 16px">
      <template #header>{{ targetType }} #{{ targetId }} 的完整时间线</template>
      <el-timeline>
        <el-timeline-item
          v-for="(log, i) in timeline"
          :key="i"
          :timestamp="log.created_at"
          :type="log.result === 'success' ? 'success' : 'danger'"
        >
          <strong>{{ log.action }}</strong> · {{ log.username }} · IP {{ log.ip || '-' }}
          <div class="lf-muted">{{ log.detail }}</div>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <el-table :data="logs" border size="small">
      <el-table-column prop="created_at" label="时间" width="170" />
      <el-table-column prop="username" label="操作人" width="110" />
      <el-table-column prop="action" label="动作" width="170" />
      <el-table-column label="操作对象" width="160">
        <template #default="{ row }">
          {{ row.target_type || '-' }}<span v-if="row.target_id"> #{{ row.target_id }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="detail" label="详情" min-width="240" show-overflow-tooltip />
      <el-table-column prop="ip" label="IP" width="130" />
      <el-table-column label="结果" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="row.result === 'success' ? 'success' : 'danger'">
            {{ row.result }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>

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
import { ElMessage } from 'element-plus'
import { fetchLogTrace, fetchLogs } from '@/api/admin'

const logs = ref([])
const timeline = ref([])
const action = ref('')
const targetType = ref('')
const targetId = ref('')
const page = ref(1)
const pageSize = ref(15)
const total = ref(0)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await fetchLogs({ action: action.value || undefined, page: page.value })
    logs.value = res.data?.items || []
    total.value = res.data?.total || 0
    pageSize.value = res.data?.per_page || 15
  } finally {
    loading.value = false
  }
}

async function trace() {
  if (!targetType.value || !targetId.value) {
    ElMessage.warning('请填写对象类型与对象 ID')
    return
  }
  const res = await fetchLogTrace({ target_type: targetType.value, target_id: targetId.value })
  timeline.value = res.data?.timeline || []
  if (!timeline.value.length) ElMessage.info('该对象暂无日志记录')
}

onMounted(load)
</script>

<style scoped>
.filters {
  display: flex;
  gap: 10px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.pager {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}
</style>
