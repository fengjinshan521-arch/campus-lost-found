<template>
  <div class="match-reason">
    <div class="score">
      综合相似度
      <strong :class="levelClass">{{ percent }}</strong>
    </div>
    <div v-for="f in factors" :key="f.name" class="factor">
      <div class="factor-head">
        <span>{{ f.name }}</span>
        <span class="lf-muted">权重 {{ f.weight }} · 得分 {{ f.factor }}</span>
      </div>
      <el-progress
        :percentage="Math.round(f.factor * 100)"
        :stroke-width="10"
        :show-text="false"
        :color="levelClass === 'high' ? '#1f9d6b' : '#0f7b72'"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  score: { type: Number, default: 0 },
  detail: { type: Object, default: () => ({}) }
})

const LABELS = {
  category: '类别一致',
  keyword: '关键词重合',
  location: '地点邻近',
  time: '时间接近',
  feature: '特征相符',
  text: '描述相似'
}

const percent = computed(() => `${Math.round((props.score || 0) * 100)}%`)
const levelClass = computed(() => {
  if ((props.score || 0) >= 0.75) return 'high'
  return (props.score || 0) >= 0.45 ? 'medium' : 'low'
})

const factors = computed(() => {
  const f = props.detail?.factors || {}
  const w = props.detail?.weights || {}
  return Object.keys(LABELS).map((key) => ({
    name: LABELS[key],
    factor: f[key] ?? 0,
    weight: w[key] ?? 0
  }))
})
</script>

<style scoped>
.match-reason {
  background: var(--lf-bg);
  border: 1px solid var(--lf-border);
  border-radius: 8px;
  padding: 12px;
}
.score {
  margin-bottom: 10px;
  font-size: 14px;
}
.score strong {
  margin-left: 6px;
  font-size: 18px;
}
.high {
  color: #16a34a;
}
.medium {
  color: var(--lf-primary);
}
.low {
  color: var(--lf-muted);
}
.factor {
  margin-bottom: 8px;
}
.factor-head {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 2px;
}
</style>
