<template>
  <div class="search-bar">
    <el-input
      v-model="form.keyword"
      placeholder="输入关键词：物品名称、特征、地点、单号"
      clearable
      size="large"
      @keyup.enter="emitSearch"
    >
      <template #append>
        <el-button :icon="Search" @click="emitSearch">搜索</el-button>
      </template>
    </el-input>

    <div class="filters">
      <el-select v-model="form.categoryId" placeholder="全部分类" clearable style="width: 160px">
        <el-option
          v-for="c in categories"
          :key="c.id"
          :label="c.name"
          :value="c.id"
        />
      </el-select>
      <el-select v-model="form.zone" placeholder="全部分区" clearable style="width: 140px">
        <el-option v-for="z in zones" :key="z" :label="z" :value="z" />
      </el-select>
      <el-select v-model="form.status" placeholder="全部状态" clearable style="width: 140px">
        <el-option
          v-for="(label, key) in itemStatus"
          :key="key"
          :label="label"
          :value="key"
        />
      </el-select>
      <el-button @click="reset">重置</el-button>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { fetchMeta } from '@/api/items'

const emit = defineEmits(['search'])

const categories = ref([])
const zones = ref([])
const itemStatus = ref({})

const form = reactive({
  keyword: '',
  categoryId: null,
  zone: '',
  status: ''
})

onMounted(async () => {
  try {
    const res = await fetchMeta()
    const data = res.data || {}
    // 一级分类与二级分类一并作为筛选项
    const flat = []
    ;(data.categories || []).forEach((c) => {
      flat.push({ id: c.id, name: c.name })
      ;(c.children || []).forEach((ch) => flat.push({ id: ch.id, name: `${c.name} / ${ch.name}` }))
    })
    categories.value = flat
    zones.value = data.zones || []
    itemStatus.value = data.item_status || {}
  } catch (e) {
    /* 字典获取失败不阻断页面 */
  }
})

function emitSearch() {
  emit('search', {
    kw: form.keyword || undefined,
    category_id: form.categoryId || undefined,
    zone: form.zone || undefined,
    status: form.status || undefined
  })
}

function reset() {
  form.keyword = ''
  form.categoryId = null
  form.zone = ''
  form.status = ''
  emitSearch()
}

defineExpose({ form })
</script>

<style scoped>
.search-bar {
  background: var(--lf-card);
  border: 1px solid var(--lf-border);
  border-radius: var(--lf-radius-lg);
  padding: 18px;
  margin-bottom: var(--lf-gap);
  box-shadow: var(--lf-shadow-sm);
}
.filters {
  display: flex;
  gap: 10px;
  margin-top: 12px;
  flex-wrap: wrap;
}
</style>
