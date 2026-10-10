<template>
  <div class="lf-container" v-loading="loading">
    <el-page-header @back="$router.back()">
      <template #content>
        <span class="title">认领单 {{ claim?.claim_no }}</span>
        <StatusTag :status="claim?.status" kind="claim" class="ml" />
      </template>
    </el-page-header>

    <el-row :gutter="16" style="margin-top: 16px" v-if="claim">
      <el-col :xs="24" :md="14">
        <el-card shadow="never">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="物品">{{ claim.found_item?.title }}</el-descriptions-item>
            <el-descriptions-item label="物品单号">{{ claim.found_item?.code }}</el-descriptions-item>
            <el-descriptions-item label="物品状态">
              <StatusTag :status="claim.found_item?.status" />
            </el-descriptions-item>
            <el-descriptions-item label="保管点">
              {{ claim.found_item?.storage_place || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="申请人">
              {{ claim.claimant?.real_name || claim.claimant?.username }}
            </el-descriptions-item>
            <el-descriptions-item label="提交时间">{{ claim.created_at }}</el-descriptions-item>
            <el-descriptions-item label="处理人">
              {{ claim.handler?.username || '未处理' }}
            </el-descriptions-item>
            <el-descriptions-item label="处理时间">{{ claim.handled_at || '-' }}</el-descriptions-item>
          </el-descriptions>

          <div class="block">
            <h3>认领理由</h3>
            <p>{{ claim.reason || '（未填写）' }}</p>
          </div>
          <div class="block" v-if="claim.contact">
            <h3>联系方式</h3>
            <p>{{ claim.contact }}</p>
          </div>
          <div class="block" v-if="(claim.evidence_list || []).length">
            <h3>凭证图片</h3>
            <el-image
              v-for="(img, i) in claim.evidence_list"
              :key="i"
              :src="img"
              :preview-src-list="claim.evidence_list"
              fit="cover"
              class="evidence"
            />
          </div>
          <div class="block" v-if="claim.handle_comment">
            <h3>处理意见</h3>
            <p>{{ claim.handle_comment }}</p>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="10">
        <el-card v-if="claim.can_handle && claim.status === 'pending'" shadow="never">
          <template #header>审核操作</template>
          <el-input v-model="comment" type="textarea" :rows="3" placeholder="处理意见（驳回时必填）" />
          <div class="ops">
            <el-button type="success" @click="doApprove">审核通过</el-button>
            <el-button type="danger" @click="doReject">驳回</el-button>
          </div>
        </el-card>

        <el-card
          v-if="claim.can_handle && claim.status === 'approved'"
          shadow="never"
          style="margin-top: 16px"
        >
          <template #header>结案</template>
          <el-button type="warning" @click="doArchive">归档结案</el-button>
          <div class="lf-muted" style="margin-top: 8px">
            归档后物品与认领单均进入终态，不可再流转
          </div>
        </el-card>

        <el-card shadow="never" style="margin-top: 16px">
          <template #header>全流程追溯</template>
          <el-timeline>
            <el-timeline-item
              v-for="(log, i) in trace"
              :key="i"
              :timestamp="log.created_at"
              :type="log.result === 'success' ? 'success' : 'danger'"
            >
              {{ log.action }} · {{ log.username }}
              <span class="lf-muted">{{ log.detail }}</span>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-if="!trace.length" description="暂无日志记录" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { archiveClaim, approveClaim, fetchClaimDetail, fetchClaimTrace, rejectClaim } from '@/api/claims'
import StatusTag from '@/components/StatusTag.vue'

const route = useRoute()
const router = useRouter()
const claim = ref(null)
const trace = ref([])
const comment = ref('')
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await fetchClaimDetail(route.params.id)
    claim.value = res.data?.claim || null
    const tr = await fetchClaimTrace(route.params.id).catch(() => null)
    trace.value = tr?.data?.logs || []
  } finally {
    loading.value = false
  }
}

async function doApprove() {
  await ElMessageBox.confirm('确认通过该认领申请？通过后物品状态更新为已认领。', '提示', { type: 'warning' })
  await approveClaim(claim.value.id, comment.value)
  ElMessage.success('已通过')
  load()
}

async function doReject() {
  if (!comment.value.trim()) {
    ElMessage.warning('驳回必须填写处理意见')
    return
  }
  await rejectClaim(claim.value.id, comment.value)
  ElMessage.success('已驳回')
  load()
}

async function doArchive() {
  await ElMessageBox.confirm('确认归档结案？', '提示', { type: 'warning' })
  await archiveClaim(claim.value.id)
  ElMessage.success('已归档')
  load()
}

onMounted(load)
</script>

<style scoped>
.title {
  font-size: 18px;
  font-weight: 600;
}
.ml {
  margin-left: 8px;
}
.block h3 {
  font-size: 14px;
  margin: 14px 0 4px;
}
.block p {
  color: var(--lf-text-regular);
  line-height: 1.7;
}
.evidence {
  width: 100px;
  height: 100px;
  border-radius: 6px;
  margin-right: 8px;
}
.ops {
  margin-top: 12px;
  display: flex;
  gap: 10px;
}
</style>
