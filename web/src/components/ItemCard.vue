<template>
  <el-card shadow="hover" class="item-card" @click="goDetail">
    <span class="status-ribbon" :style="{ background: statusColor }" />
    <span class="tag-hole" />
    <div class="cover">
      <el-image v-if="cover" :src="cover" fit="cover" class="cover-img">
        <template #error>
          <div class="cover-empty">
            <el-icon :size="28"><Box /></el-icon>
            <span>图片加载失败</span>
          </div>
        </template>
      </el-image>
      <div v-else class="cover-empty">
        <el-icon :size="28"><Box /></el-icon>
        <span>暂无图片</span>
      </div>
      <StatusTag :status="item.status" class="status" />
    </div>
    <div class="title">{{ item.title }}</div>
    <div class="meta lf-muted">
      <span>{{ item.category_name || '未分类' }}</span>
      <span>·</span>
      <span>{{ placeLabel }}</span>
    </div>
    <div class="meta lf-muted">
      <span>单号 {{ item.code }}</span>
      <span>·</span>
      <span>{{ timeLabel }}</span>
    </div>
    <div class="desc">{{ brief }}</div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import StatusTag from './StatusTag.vue'

const props = defineProps({
  item: { type: Object, required: true },
  kind: { type: String, default: 'found' } // found | lost
})

const router = useRouter()

const STATUS_COLOR = {
  unclaimed: 'var(--lf-warning)',
  pending: 'var(--lf-warning)',
  claimed: 'var(--lf-success)',
  matched: 'var(--lf-primary)',
  archived: 'var(--lf-muted)'
}
const statusColor = computed(() => STATUS_COLOR[props.item.status] || 'var(--lf-primary)')

const cover = computed(() => (props.item.image_list || [])[0] || '')
const placeLabel = computed(() =>
  props.kind === 'found' ? props.item.found_place : props.item.lost_place
)
const timeLabel = computed(() =>
  (props.kind === 'found' ? props.item.found_time : props.item.lost_time) || ''
)
const brief = computed(() => {
  const text = props.item.description || ''
  return text.length > 60 ? text.slice(0, 60) + '…' : text
})

function goDetail() {
  router.push(`/${props.kind}/${props.item.id}`)
}
</script>

<style scoped>
.item-card {
  position: relative;
  cursor: pointer;
  border-radius: var(--lf-radius-lg);
  overflow: hidden;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}
.status-ribbon {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  border-radius: var(--lf-radius-lg) 0 0 var(--lf-radius-lg);
  z-index: 3;
}
.tag-hole {
  position: absolute;
  top: 9px;
  left: 50%;
  transform: translateX(-50%);
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--lf-card);
  box-shadow: inset 0 0 0 2px var(--lf-border-strong);
  z-index: 3;
}
.item-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--lf-shadow-hover);
  border-color: var(--lf-primary-light);
}
.item-card :deep(.el-card__body) {
  padding: 12px;
}
.cover {
  position: relative;
  height: 158px;
  background: var(--lf-bg);
  border-radius: var(--lf-radius-md);
  overflow: hidden;
  margin-bottom: 12px;
}
.cover-img {
  width: 100%;
  height: 100%;
  border-radius: var(--lf-radius-md);
}
.cover-img :deep(img) {
  transition: transform 0.3s ease;
}
.item-card:hover .cover-img :deep(img) {
  transform: scale(1.05);
}
.cover-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 100%;
  color: var(--lf-muted);
  font-size: 12px;
}
.status {
  position: absolute;
  right: 8px;
  top: 8px;
  box-shadow: var(--lf-shadow-sm);
}
.title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--lf-text);
}
.meta {
  display: flex;
  gap: 6px;
  margin-bottom: 3px;
  font-size: 12.5px;
  color: var(--lf-muted);
}
.desc {
  margin-top: 8px;
  font-size: 13px;
  color: var(--lf-text-regular);
  min-height: 38px;
  line-height: 1.55;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
