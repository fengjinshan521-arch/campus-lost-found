<template>
  <div class="lf-container" v-loading="loading">
    <template v-if="item">
      <el-page-header @back="$router.back()">
        <template #content>
          <span class="title">{{ item.title }}</span>
          <StatusTag :status="item.status" class="ml" />
        </template>
      </el-page-header>

      <el-row :gutter="16" style="margin-top: 16px">
        <el-col :xs="24" :md="14">
          <el-card shadow="never">
            <div class="gallery">
              <el-image
                v-for="(img, i) in item.image_list || []"
                :key="i"
                :src="img"
                :preview-src-list="item.image_list || []"
                fit="cover"
                class="gallery-img"
              >
                <template #error>
                  <div class="img-error">加载失败</div>
                </template>
              </el-image>
              <div v-if="!(item.image_list || []).length" class="no-image lf-muted">
                暂无图片（可在编辑时上传）
              </div>
            </div>

            <el-descriptions :column="2" border style="margin-top: 16px">
              <el-descriptions-item label="单号">{{ item.code }}</el-descriptions-item>
              <el-descriptions-item label="分类">{{ item.category_name }}</el-descriptions-item>
              <el-descriptions-item :label="kind === 'found' ? '拾获地点' : '丢失地点'">
                {{ kind === 'found' ? item.found_place : item.lost_place }}
              </el-descriptions-item>
              <el-descriptions-item label="所在分区">
                {{ kind === 'found' ? item.found_zone : item.lost_zone }}
              </el-descriptions-item>
              <el-descriptions-item :label="kind === 'found' ? '拾获时间' : '丢失时间'">
                {{ kind === 'found' ? item.found_time : item.lost_time }}
              </el-descriptions-item>
              <el-descriptions-item label="浏览量">{{ item.view_count }}</el-descriptions-item>
              <el-descriptions-item v-if="kind === 'found'" label="保管点">
                {{ item.storage_place || '待分配' }}
              </el-descriptions-item>
              <el-descriptions-item v-if="kind === 'lost'" label="酬金">
                {{ item.reward || '无' }}
              </el-descriptions-item>
            </el-descriptions>

            <div class="desc-block">
              <h3>详细描述</h3>
              <p>{{ item.description || '（未填写）' }}</p>
              <div class="features">
                <el-tag v-for="f in item.feature_list || []" :key="f" size="small">{{ f }}</el-tag>
              </div>
            </div>

            <div v-if="canClaim" class="actions">
              <el-button type="primary" @click="goClaim">提交认领申请</el-button>
            </div>
            <div v-else-if="!store.isLogin" class="lf-muted">登录后可对未认领物品提交认领申请</div>

            <div v-if="isOwner" class="actions">
              <el-button @click="cancelItem">撤销发布</el-button>
              <el-button v-if="item.status === 'claimed'" type="warning" @click="archiveItem">
                归档结案
              </el-button>
            </div>
          </el-card>

          <el-card v-if="claims.length" shadow="never" style="margin-top: 16px">
            <template #header>认领申请时间线</template>
            <el-timeline>
              <el-timeline-item
                v-for="c in claims"
                :key="c.id"
                :timestamp="c.created_at"
                :type="c.status === 'approved' ? 'success' : 'info'"
              >
                {{ c.claimant?.real_name || c.claimant?.username }} 提交了认领：
                {{ c.reason }}
                <StatusTag :status="c.status" kind="claim" class="ml" />
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </el-col>

        <el-col :xs="24" :md="10">
          <el-card shadow="never">
            <template #header>
              智能匹配推荐
              <span class="lf-muted">（六因子加权，阈值以上展示）</span>
            </template>
            <el-empty v-if="!matches.length" description="暂未匹配到相似信息" />
            <div v-for="m in matches" :key="m.id" class="match-item">
              <div class="match-title">
                <el-link @click="goMatch(m)">{{ m.title }}</el-link>
              </div>
              <MatchReason :score="m.score" :detail="m.detail" />
              <el-button
                v-if="kind === 'lost' && store.isLogin"
                size="small"
                type="primary"
                class="match-btn"
                @click="claimFound(m.id)"
              >
                认领这条招领
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import {
  archiveFound,
  cancelFound,
  cancelLost,
  fetchFoundDetail,
  fetchItemClaims,
  fetchLostDetail
} from '@/api/items'
import StatusTag from '@/components/StatusTag.vue'
import MatchReason from '@/components/MatchReason.vue'

const route = useRoute()
const router = useRouter()
const store = useUserStore()

const kind = ref(route.meta.kind || 'found')
const item = ref(null)
const matches = ref([])
const claims = ref([])
const loading = ref(false)

const canClaim = computed(() => kind.value === 'found' && route.meta.canClaim !== false)
const isOwner = computed(() => {
  if (!item.value || !store.isLogin) return false
  const ownerId = kind.value === 'found' ? item.value.founder?.id : item.value.owner?.id
  return ownerId === store.user.id || store.isStaff
})

async function load() {
  loading.value = true
  try {
    const res =
      kind.value === 'found'
        ? await fetchFoundDetail(route.params.id)
        : await fetchLostDetail(route.params.id)
    item.value = res.data?.item || null
    matches.value = res.data?.item?.matches || []
    if (kind.value === 'found') {
      const cr = await fetchItemClaims(route.params.id).catch(() => null)
      claims.value = cr?.data?.claims || []
    }
  } finally {
    loading.value = false
  }
}

function goClaim() {
  router.push({ path: '/claims/new', query: { foundId: item.value.id } })
}

function goMatch(m) {
  router.push(kind.value === 'found' ? `/lost/${m.id}` : `/found/${m.id}`)
}

function claimFound(foundId) {
  router.push({ path: '/claims/new', query: { foundId, lostId: item.value.id } })
}

async function cancelItem() {
  await ElMessageBox.confirm('确认撤销该条信息？撤销后不可恢复。', '提示', { type: 'warning' })
  if (kind.value === 'found') await cancelFound(item.value.id)
  else await cancelLost(item.value.id)
  ElMessage.success('已撤销')
  load()
}

async function archiveItem() {
  await ElMessageBox.confirm('确认归档结案？归档后该物品流程闭环。', '提示', { type: 'warning' })
  await archiveFound(item.value.id)
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
.gallery {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.gallery-img {
  width: 140px;
  height: 140px;
  border-radius: 6px;
  background: var(--lf-bg);
}
.img-error {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: var(--lf-muted);
  font-size: 12px;
}
.no-image {
  padding: 40px 0;
  text-align: center;
}
.desc-block h3 {
  font-size: 15px;
  margin: 16px 0 6px;
}
.desc-block p {
  color: var(--lf-text-regular);
  line-height: 1.7;
}
.features {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 10px;
}
.actions {
  margin-top: 16px;
  display: flex;
  gap: 10px;
}
.match-item {
  border-bottom: 1px dashed var(--lf-border);
  padding-bottom: 12px;
  margin-bottom: 12px;
}
.match-title {
  margin-bottom: 8px;
  font-weight: 600;
}
.match-btn {
  margin-top: 8px;
}
</style>
