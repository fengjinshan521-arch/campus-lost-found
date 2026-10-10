<template>
  <div class="lf-container" v-loading="loading">
    <div class="head">
      <h2 class="lf-page-title">分类管理</h2>
      <el-button type="primary" @click="openDialog()">新增分类</el-button>
    </div>

    <el-table :data="categories" border size="small" row-key="id">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="分类名称" min-width="160" />
      <el-table-column prop="code" label="编码" width="120" />
      <el-table-column prop="full_name" label="完整路径" min-width="180" />
      <el-table-column prop="sort_order" label="排序" width="80" />
      <el-table-column label="启用" width="80">
        <template #default="{ row }">
          <el-tag size="small" :type="row.is_active ? 'success' : 'info'">
            {{ row.is_active ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
          <el-button link type="danger" @click="remove(row)">停用</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" :title="editing ? '编辑分类' : '新增分类'" width="460px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="分类名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="编码">
          <el-input v-model="form.code" placeholder="英文标识，可留空" />
        </el-form-item>
        <el-form-item label="上级分类">
          <el-select v-model="form.parent_id" clearable placeholder="无（一级分类）" style="width: 100%">
            <el-option v-for="c in topCategories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序号">
          <el-input-number v-model="form.sort_order" :min="0" :max="999" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createCategory, deleteCategory, fetchCategories, updateCategory } from '@/api/admin'

const categories = ref([])
const loading = ref(false)
const dialog = ref(false)
const editing = ref(null)
const form = ref({ name: '', code: '', parent_id: null, sort_order: 0, description: '' })

const topCategories = computed(() => categories.value.filter((c) => !c.parent_id))

async function load() {
  loading.value = true
  try {
    const res = await fetchCategories()
    categories.value = res.data?.categories || []
  } finally {
    loading.value = false
  }
}

function openDialog(row = null) {
  editing.value = row
  form.value = row
    ? { name: row.name, code: row.code || '', parent_id: row.parent_id, sort_order: row.sort_order, description: row.description || '' }
    : { name: '', code: '', parent_id: null, sort_order: 0, description: '' }
  dialog.value = true
}

async function save() {
  if (!form.value.name.trim()) {
    ElMessage.warning('请填写分类名称')
    return
  }
  if (editing.value) {
    await updateCategory(editing.value.id, form.value)
  } else {
    await createCategory(form.value)
  }
  ElMessage.success('保存成功')
  dialog.value = false
  load()
}

async function remove(row) {
  await ElMessageBox.confirm(`确认停用分类「${row.name}」？历史数据会保留以便追溯。`, '提示', { type: 'warning' })
  await deleteCategory(row.id)
  ElMessage.success('已停用')
  load()
}

onMounted(load)
</script>

<style scoped>
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
