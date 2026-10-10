<template>
  <div class="lf-container" v-loading="loading">
    <h2 class="lf-page-title">认领管理</h2>

    <el-tabs v-model="tab">
      <el-tab-pane label="我提交的申请" name="mine">
        <el-table :data="mine" border size="small">
          <el-table-column prop="claim_no" label="认领单号" width="150" />
          <el-table-column label="物品" min-width="180">
            <template #default="{ row }">{{ row.found_item?.title || '-' }}</template>
          </el-table-column>
          <el-table-column label="申请人" width="120">
            <template #default="{ row }">{{ row.claimant?.real_name || row.claimant?.username || '-' }}</template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <StatusTag :status="row.status" kind="claim" />
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="提交时间" width="170" />
          <el-table-column label="操作" width="160">
            <template #default="{ row }">
              <el-button link type="primary" @click="goDetail(row)">详情</el-button>
              <el-button v-if="row.status === 'pending'" link type="danger" @click="cancelClaimRow(row)">
                撤回
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && !mine.length" description="暂无认领申请" />
      </el-tab-pane>

      <el-tab-pane label="待我审核" name="inbox">
        <el-table :data="inbox" border size="small">
          <el-table-column prop="claim_no" label="认领单号" width="150" />
          <el-table-column label="物品" min-width="180">
            <template #default="{ row }">{{ row.found_item?.title || '-' }}</template>
          </el-table-column>
          <el-table-column label="申请人" width="120">
            <template #default="{ row }">{{ row.claimant?.real_name || row.claimant?.username || '-' }}</template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <StatusTag :status="row.status" kind="claim" />
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="提交时间" width="170" />
          <el-table-column label="操作" width="160">
            <template #default="{ row }">
              <el-button link type="primary" @click="goDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && !inbox.length" description="暂无待审核申请" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { cancelClaim, fetchInbox, fetchMyClaims } from '@/api/claims'
import StatusTag from '@/components/StatusTag.vue'

const router = useRouter()
const tab = ref('mine')
const mine = ref([])
const inbox = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const [a, b] = await Promise.all([
      fetchMyClaims().catch(() => ({ data: { items: [] } })),
      fetchInbox().catch(() => ({ data: { items: [] } }))
    ])
    mine.value = a.data?.items || []
    inbox.value = b.data?.items || []
  } finally {
    loading.value = false
  }
}

function goDetail(row) {
  router.push(`/claims/${row.id}`)
}

async function cancelClaimRow(row) {
  await ElMessageBox.confirm('确认撤回该认领申请？', '提示', { type: 'warning' })
  await cancelClaim(row.id)
  ElMessage.success('已撤回')
  load()
}

onMounted(load)
</script>
