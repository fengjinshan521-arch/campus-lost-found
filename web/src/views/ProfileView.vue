<template>
  <div class="lf-container">
    <h2 class="lf-page-title">个人中心</h2>
    <el-row :gutter="16">
      <el-col :xs="24" :md="12">
        <el-card shadow="never">
          <template #header>基本信息</template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="用户名">{{ store.user?.username }}</el-descriptions-item>
            <el-descriptions-item label="姓名">{{ store.user?.real_name || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="角色">{{ roleLabel }}</el-descriptions-item>
            <el-descriptions-item label="学号">{{ store.user?.student_no || '未认证' }}</el-descriptions-item>
            <el-descriptions-item label="学院">{{ store.user?.college || '未填写' }}</el-descriptions-item>
            <el-descriptions-item label="信用分">{{ store.user?.credit_score }}</el-descriptions-item>
            <el-descriptions-item label="认证状态">
              <el-tag :type="store.user?.verified ? 'success' : 'info'" size="small">
                {{ store.user?.verified ? '已认证' : '未认证' }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>

          <el-form :model="profile" label-width="80px" style="margin-top: 16px">
            <el-form-item label="姓名">
              <el-input v-model="profile.real_name" />
            </el-form-item>
            <el-form-item label="学院">
              <el-input v-model="profile.college" />
            </el-form-item>
            <el-form-item label="手机号">
              <el-input v-model="profile.phone" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveProfile">保存资料</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="12">
        <el-card shadow="never">
          <template #header>校内身份认证</template>
          <el-form :model="verifyForm" label-width="80px">
            <el-form-item label="学号">
              <el-input v-model="verifyForm.student_no" placeholder="如 2022010101" />
            </el-form-item>
            <el-form-item label="姓名">
              <el-input v-model="verifyForm.real_name" placeholder="与学籍一致" />
            </el-form-item>
            <el-form-item>
              <el-button @click="doVerify">提交认证</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card shadow="never" style="margin-top: 16px">
          <template #header>修改密码</template>
          <el-form :model="pwd" label-width="90px">
            <el-form-item label="原密码">
              <el-input v-model="pwd.old_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码">
              <el-input v-model="pwd.new_password" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="danger" @click="doChangePassword">确认修改</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { changePassword, updateProfile, verifyIdentity } from '@/api/auth'

const store = useUserStore()

const roleLabel = computed(() => ({ student: '学生', staff: '楼管/保卫处', admin: '管理员' }[store.user?.role] || ''))

const profile = reactive({ real_name: '', college: '', phone: '' })
const verifyForm = reactive({ student_no: '', real_name: '' })
const pwd = reactive({ old_password: '', new_password: '' })

watch(
  () => store.user,
  (u) => {
    if (!u) return
    profile.real_name = u.real_name || ''
    profile.college = u.college || ''
    profile.phone = u.phone || ''
  },
  { immediate: true }
)

async function saveProfile() {
  const res = await updateProfile({ ...profile })
  store.user = res.data?.user || store.user
  ElMessage.success('资料已更新')
}

async function doVerify() {
  const res = await verifyIdentity({ ...verifyForm })
  store.user = res.data?.user || store.user
  ElMessage.success('身份认证成功')
}

async function doChangePassword() {
  if (!pwd.old_password || !pwd.new_password) {
    ElMessage.warning('请填写原密码与新密码')
    return
  }
  await changePassword({ ...pwd })
  pwd.old_password = ''
  pwd.new_password = ''
  ElMessage.success('密码已修改')
}
</script>
