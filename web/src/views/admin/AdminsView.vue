<template>
  <div class="lf-container" v-loading="loading">
    <div class="head">
      <h2 class="lf-page-title">管理员管理</h2>
      <el-button type="primary" @click="openDialog()">新增管理账号</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon style="margin-bottom: 14px">
      管理账号仅由系统管理员创建与维护；系统始终保留至少一个启用状态的管理员，当前启用管理员
      <b>{{ stats.active_admin_count ?? 0 }}</b> 名。所有操作均写入日志可追溯。
    </el-alert>

    <div class="filters">
      <el-input v-model="kw" placeholder="账号 / 姓名 / 手机号" clearable style="width: 200px" @keyup.enter="load" />
      <el-select v-model="role" placeholder="角色" clearable style="width: 150px">
        <el-option label="系统管理员" value="admin" />
        <el-option label="楼管/保卫处" value="staff" />
      </el-select>
      <el-select v-model="status" placeholder="状态" clearable style="width: 120px">
        <el-option label="正常" value="active" />
        <el-option label="已停用" value="disabled" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
    </div>

    <el-table :data="admins" border size="small">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="登录账号" width="130" />
      <el-table-column prop="real_name" label="姓名" width="110" />
      <el-table-column label="角色" width="120">
        <template #default="{ row }">
          <el-tag size="small" :type="row.role === 'admin' ? 'danger' : 'warning'" effect="plain">
            {{ row.role_label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="college" label="所属部门" min-width="140" />
      <el-table-column prop="phone" label="手机号" width="140" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="row.status === 'active' ? 'success' : 'info'">
            {{ row.status === 'active' ? '正常' : '已停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="260">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
          <el-button link type="warning" @click="resetPwd(row)">重置密码</el-button>
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

    <el-dialog v-model="dialog" :title="form.id ? '编辑管理账号' : '新增管理账号'" width="460px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="登录账号" required>
          <el-input v-model="form.username" :disabled="!!form.id" placeholder="如 admin、staff01" />
        </el-form-item>
        <el-form-item label="姓名" required>
          <el-input v-model="form.real_name" placeholder="如 张管理" />
        </el-form-item>
        <el-form-item label="角色" required>
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="系统管理员（全部后台权限）" value="admin" />
            <el-option label="楼管/保卫处（登记与审核）" value="staff" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属部门">
          <el-input v-model="form.college" placeholder="如 保卫处 / 后勤部" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" maxlength="20" />
        </el-form-item>
        <el-form-item v-if="!form.id" label="初始密码" required>
          <el-input v-model="form.password" show-password placeholder="至少 6 位，含字母与数字" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createAdmin, fetchAdmins, resetAdminPassword, setAdminStatus, updateAdmin } from '@/api/admin'
import { useUserStore } from '@/stores/user'

const store = useUserStore()
const admins = ref([])
const stats = ref({})
const kw = ref('')
const role = ref('')
const status = ref('')
const page = ref(1)
const pageSize = ref(12)
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const dialog = ref(false)
const form = reactive({ id: null, username: '', real_name: '', role: 'staff', college: '', phone: '', password: '' })

async function load() {
  loading.value = true
  try {
    const res = await fetchAdmins({ kw: kw.value || undefined, role: role.value || undefined,
      status: status.value || undefined, page: page.value })
    admins.value = res.data?.items || []
    total.value = res.data?.total || 0
    pageSize.value = res.data?.per_page || 12
    stats.value = res.data || {}
  } finally {
    loading.value = false
  }
}

function openDialog(row) {
  Object.assign(form, {
    id: row?.id || null,
    username: row?.username || '',
    real_name: row?.real_name || '',
    role: row?.role || 'staff',
    college: row?.college || '',
    phone: row?.phone || '',
    password: ''
  })
  dialog.value = true
}

async function submit() {
  if (!form.username.trim()) return ElMessage.warning('请填写登录账号')
  if (!form.real_name.trim()) return ElMessage.warning('请填写姓名')
  if (!form.id && !form.password) return ElMessage.warning('请设置初始密码')

  saving.value = true
  try {
    const data = {
      username: form.username.trim(),
      real_name: form.real_name.trim(),
      role: form.role,
      college: form.college.trim() || undefined,
      phone: form.phone.trim() || undefined
    }
    const res = form.id
      ? await updateAdmin(form.id, data)
      : await createAdmin({ ...data, password: form.password })
    ElMessage.success(res.msg || '已保存')
    dialog.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function resetPwd(row) {
  const { value } = await ElMessageBox.prompt(
    `为账号「${row.username}」设置新密码（至少 6 位，含字母与数字）`,
    '重置密码',
    { inputType: 'password', inputPattern: /^.{6,}$/, inputErrorMessage: '密码至少 6 位' }
  )
  const res = await resetAdminPassword(row.id, value)
  ElMessage.success(res.msg || '密码已重置')
}

async function toggleStatus(row) {
  if (row.id === store.user?.id) {
    ElMessage.warning('不能停用自己的账号，请由其他管理员操作')
    return
  }
  const next = row.status === 'active' ? 'disabled' : 'active'
  try {
    const res = await setAdminStatus(row.id, next)
    ElMessage.success(res.msg || '状态已更新')
    load()
  } catch (e) {
    ElMessage.error(e?.msg || '操作失败')
  }
}

onMounted(load)
</script>

<style scoped>
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
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
