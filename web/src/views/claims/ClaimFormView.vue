<template>
  <div class="lf-container">
    <el-card class="form-card">
      <h2 class="lf-page-title">提交认领申请</h2>

      <el-form :model="form" label-width="110px">
        <el-form-item label="招领单号/ID">
          <el-input v-model="form.found_item_id" placeholder="请输入要认领的招领信息 ID" />
          <div class="lf-muted">从招领详情页点击“提交认领申请”可自动带入</div>
        </el-form-item>
        <el-form-item label="关联寻物启事">
          <el-input v-model="form.lost_item_id" placeholder="选填：若你已发布过寻物启事，填写其 ID 可联动归档" />
        </el-form-item>
        <el-form-item label="认领理由">
          <el-input
            v-model="form.reason"
            type="textarea"
            :rows="4"
            placeholder="请描述只有失主才知道的细节（外观、磨损、内含物等），至少 5 个字"
          />
        </el-form-item>
        <el-form-item label="联系方式">
          <el-input v-model="form.contact" placeholder="手机号或微信，便于核实" />
        </el-form-item>
        <el-form-item label="凭证图片">
          <UploadImages v-model="form.evidence" entity-type="claim" :limit="3" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="submit">提交申请</el-button>
          <el-button @click="$router.back()">返回</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createClaim } from '@/api/claims'
import { ensureCsrf } from '@/api/request'
import UploadImages from '@/components/UploadImages.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(false)

const form = reactive({
  found_item_id: '',
  lost_item_id: '',
  reason: '',
  contact: '',
  evidence: []
})

onMounted(() => {
  if (route.query.foundId) form.found_item_id = String(route.query.foundId)
  if (route.query.lostId) form.lost_item_id = String(route.query.lostId)
})

async function submit() {
  if (!form.found_item_id) {
    ElMessage.warning('请填写招领信息 ID')
    return
  }
  if ((form.reason || '').trim().length < 5) {
    ElMessage.warning('认领理由请至少填写 5 个字，便于核实')
    return
  }
  if (form.lost_item_id && !/^\d+$/.test(String(form.lost_item_id).trim())) {
    ElMessage.warning('关联寻物启事请填写数字 ID，或留空')
    return
  }
  loading.value = true
  try {
    await ensureCsrf()
    const res = await createClaim({
      found_item_id: Number(form.found_item_id),
      lost_item_id: form.lost_item_id ? Number(form.lost_item_id) : null,
      reason: form.reason,
      contact: form.contact,
      evidence: form.evidence
    })
    ElMessage.success(res.msg || '认领申请已提交')
    router.push(`/claims/${res.data.id}`)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.form-card {
  width: min(700px, 96%);
  margin: 0 auto;
}
</style>
