<template>
  <div class="lf-container" style="max-width: 460px; margin: 40px auto">
    <el-card shadow="never" class="lf-card">
      <h2 class="lf-page-title">找回密码</h2>

      <!-- 第一步：身份校验 -->
      <el-form v-if="step === 1" :model="form" label-width="84px" @submit.prevent>
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="注册时填写的登录账号" />
        </el-form-item>
        <el-form-item label="学号">
          <el-input v-model="form.student_no" placeholder="与账号绑定的学号" />
        </el-form-item>
        <el-form-item label="真实姓名">
          <el-input v-model="form.real_name" placeholder="与账号绑定的真实姓名" />
        </el-form-item>
        <el-button type="primary" :loading="loading" class="lf-full-btn" @click="identify">
          校验身份
        </el-button>
        <div class="lf-muted lf-tip">
          演示环境：身份校验通过后会直接返回重置令牌，复制填入第二步即可。
        </div>
      </el-form>

      <!-- 第二步：设置新密码 -->
      <el-form v-else :model="form" label-width="84px" @submit.prevent>
        <el-form-item label="重置令牌">
          <el-input v-model="form.reset_token" placeholder="上一步返回的重置令牌" />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="form.new_password" type="password" show-password placeholder="至少8位，含字母/数字/符号中两类" />
        </el-form-item>
        <el-button type="primary" :loading="loading" class="lf-full-btn" @click="doReset">
          重置密码
        </el-button>
        <el-button text class="lf-full-btn" @click="step = 1">返回上一步</el-button>
      </el-form>

      <el-button text class="lf-full-btn lf-back" @click="$router.push('/login')">
        想起密码了？去登录
      </el-button>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { forgotPassword, resetPassword } from '@/api/auth'

const step = ref(1)
const loading = ref(false)
const form = reactive({ username: '', student_no: '', real_name: '', reset_token: '', new_password: '' })

async function identify() {
  if (!form.username || !form.student_no || !form.real_name) {
    ElMessage.warning('请填写用户名、学号与真实姓名')
    return
  }
  loading.value = true
  try {
    const res = await forgotPassword({ ...form })
    form.reset_token = res.data.reset_token
    step.value = 2
    ElMessage.success(`身份校验通过，令牌有效期约 ${res.data.expire_in_minutes} 分钟`)
  } finally {
    loading.value = false
  }
}

async function doReset() {
  if (!form.reset_token || !form.new_password) {
    ElMessage.warning('请填写重置令牌与新密码')
    return
  }
  loading.value = true
  try {
    await resetPassword({ reset_token: form.reset_token, new_password: form.new_password })
    ElMessage.success('密码已重置，请使用新密码登录')
    setTimeout(() => window.location.assign('/login'), 800)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.lf-full-btn { width: 100%; margin-top: 8px; }
.lf-tip { font-size: 12px; margin-top: 10px; line-height: 1.6; }
.lf-back { margin-top: 4px; }
</style>
