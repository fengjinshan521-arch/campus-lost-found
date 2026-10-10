<template>
  <el-tag :type="tagType" size="small" effect="light">{{ label }}</el-tag>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, default: '' },
  kind: { type: String, default: 'item' } // item | claim
})

const ITEM_MAP = {
  unclaimed: ['未认领', 'primary'],
  pending: ['待确认', 'warning'],
  claimed: ['已认领', 'success'],
  archived: ['已归档', 'info'],
  cancelled: ['已撤销', 'danger']
}

const CLAIM_MAP = {
  pending: ['待确认', 'warning'],
  approved: ['已认领', 'success'],
  rejected: ['已驳回', 'danger'],
  cancelled: ['已取消', 'info'],
  archived: ['已归档', 'info']
}

const label = computed(() => {
  const map = props.kind === 'claim' ? CLAIM_MAP : ITEM_MAP
  return map[props.status]?.[0] || props.status || '未知'
})

const tagType = computed(() => {
  const map = props.kind === 'claim' ? CLAIM_MAP : ITEM_MAP
  return map[props.status]?.[1] || 'info'
})
</script>
