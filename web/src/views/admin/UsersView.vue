<template>
  <div class="lf-container" v-loading="loading">
    <h2 class="lf-page-title">用户管理</h2>

    <div class="filters">
      <el-input v-model="kw" placeholder="用户名 / 姓名 / 学号" clearable style="width: 220px" @keyup.enter="load" />
      <el-select v-model="role" placeholder="角色" clearable style="width: 140px">
        <el-option label="学生" value="student" />
        <el-option label="楼管/保卫处" value="staff" />
        <el-option label="管理员" value="admin" />
      </el-select>
      <el-select v-model="status" placeholder="状态" clearable style="width: 140px">
        <el-option label="正常" value="active" />
        <el-option label="已禁用" value="disabled" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
    </div>

    <el-table :data="users" border size="small">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="real_name" label="姓名" width="100" />
      <el-table-column prop="student_no" label="学号（脱敏）" width="140" />
      <el-table-column prop="phone" label="手机号（脱敏）" width="140" />
      <el-table-column prop="role_label" label="角色" width="120" />
      <el-table-column label="认证" width="80">
        <template #default="{ row }">
          <el-tag size="small" :type="row.verified ? 'success' : 'info'">
            {{ row.verified ? '已认证' : '未认证' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="credit_score" label="信用分" width="90" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-select
            :model-value="row.role"
            size="small"
            style="width: 110px"
            @change="(v) => changeRole(row, v)"
          >
            <el-option label="学生" value="student" />
            <el-option label="楼管" value="staff" />
            <el-option label="管理员" value="admin" />
          </el-select>
          <el-button
            link
            :type="row.status === 'active' ? 'danger' : 'success'"
            @click="toggleStatus(row)"
          >
            {{ row.status === 'active' ? '停用' : '启用' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next, total"
        @current-change="load"
      />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchUsers, setUserRole, setUserStatus } from '@/api/admin'

const users = ref([])
const kw = ref('')
const role = ref('')
const status = ref('')
const page = ref(1)
const pageSize = ref(12)
const total = ref(0)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await fetchUsers({ kw: kw.value || undefined, role: role.value || undefined,
      status: status.value || undefined, page: page.value })
    users.value = res.data?.items || []
    total.value = res.data?.total || 0
    pageSize.value = res.data?.per_page || 12
  } finally {
    loading.value = false
  }
}

async function changeRole(row, value) {
  const res = await setUserRole(row.id, value)
  ElMessage.success(res.msg || '角色已更新')
  load()
}

async function toggleStatus(row) {
  const next = row.status === 'active' ? 'disabled' : 'active'
  const res = await setUserStatus(row.id, next)
  ElMessage.success(res.msg || '状态已更新')
  load()
}

onMounted(load)
</script>

<style scoped>
.filters {
  display: flex;
  gap: 10px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.pager {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}
</style>
