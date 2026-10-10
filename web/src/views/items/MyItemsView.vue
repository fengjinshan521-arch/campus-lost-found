<template>
  <div class="lf-container" v-loading="loading">
    <h2 class="lf-page-title">我的发布</h2>

    <h3>我登记的拾获物品</h3>
    <el-table :data="found" border size="small" style="margin-bottom: 24px">
      <el-table-column prop="code" label="单号" width="150" />
      <el-table-column prop="title" label="标题" min-width="200" />
      <el-table-column prop="found_zone" label="分区" width="100" />
      <el-table-column prop="found_time" label="拾获时间" width="160" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }"><StatusTag :status="row.status" /></template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button link type="primary" @click="$router.push(`/found/${row.id}`)">查看</el-button>
          <el-button link type="danger" @click="cancel('found', row.id)">撤销</el-button>
        </template>
      </el-table-column>
    </el-table>

    <h3>我发布的寻物启事</h3>
    <el-table :data="lost" border size="small">
      <el-table-column prop="code" label="单号" width="150" />
      <el-table-column prop="title" label="标题" min-width="200" />
      <el-table-column prop="lost_zone" label="分区" width="100" />
      <el-table-column prop="lost_time" label="丢失时间" width="160" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }"><StatusTag :status="row.status" /></template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button link type="primary" @click="$router.push(`/lost/${row.id}`)">查看</el-button>
          <el-button link type="danger" @click="cancel('lost', row.id)">撤销</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { cancelFound, cancelLost, fetchMyItems } from '@/api/items'
import StatusTag from '@/components/StatusTag.vue'

const found = ref([])
const lost = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await fetchMyItems()
    found.value = res.data?.found?.items || []
    lost.value = res.data?.lost?.items || []
  } finally {
    loading.value = false
  }
}

async function cancel(kind, id) {
  await ElMessageBox.confirm('确认撤销该条发布？', '提示', { type: 'warning' })
  if (kind === 'found') await cancelFound(id)
  else await cancelLost(id)
  ElMessage.success('已撤销')
  load()
}

onMounted(load)
</script>
