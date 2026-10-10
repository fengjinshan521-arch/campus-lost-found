<template>
  <div class="lf-container">
    <el-card class="auth-card">
      <h2 class="lf-page-title">登录</h2>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="form.remember">记住我（7 天）</el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="submit">登录</el-button>
          <el-button text @click="$router.push('/register')">还没有账号？去注册</el-button>
          <el-button text @click="$router.push('/forgot')">忘记密码？</el-button>
        </el-form-item>
      </el-form>

      <el-divider>演示账号</el-divider>
      <div class="lf-muted">
        管理员 admin / Admin@12345 · 楼管 staff01 / Staff@123 · 学生 zhangsan / Student@123
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const store = useUserStore()
const router = useRouter()
const route = useRoute()

const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', password: '', remember: true })

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function submit() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await store.login({ username: form.username, password: form.password, remember: form.remember })
      ElMessage.success('登录成功')
      router.push(route.query.redirect || '/')
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.auth-card {
  width: min(460px, 94%);
  margin: 24px auto;
}
</style>
