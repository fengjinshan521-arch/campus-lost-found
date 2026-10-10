<template>
  <div class="lf-container">
    <h2 class="lf-page-title">招领信息</h2>
    <SearchBar ref="searchRef" @search="onSearch" />

    <div v-if="loading" class="lf-muted">加载中…</div>
    <template v-else>
      <div class="lf-grid">
        <ItemCard v-for="item in items" :key="item.id" :item="item" kind="found" />
      </div>
      <el-empty v-if="!items.length" description="没有符合条件的招领信息" />
      <div class="pager">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next, total"
          @current-change="load"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import SearchBar from '@/components/SearchBar.vue'
import ItemCard from '@/components/ItemCard.vue'
import { fetchFoundList } from '@/api/items'

const route = useRoute()
const items = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(12)
const total = ref(0)
const filters = ref({})

async function load() {
  loading.value = true
  try {
    const res = await fetchFoundList({ page: page.value, ...filters.value })
    items.value = res.data?.items || []
    total.value = res.data?.total || 0
    pageSize.value = res.data?.per_page || 12
  } finally {
    loading.value = false
  }
}

function onSearch(params) {
  filters.value = params
  page.value = 1
  load()
}

onMounted(() => {
  if (route.query.kw) filters.value = { kw: route.query.kw }
  load()
})
</script>

<style scoped>
.pager {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
