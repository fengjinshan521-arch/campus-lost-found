<template>
  <div class="lf-container">
    <el-card class="form-card">
      <h2 class="lf-page-title">拾获登记</h2>
      <el-alert
        type="info"
        show-icon
        :closable="false"
        title="登记后将自动进行一次匹配计算，若发现疑似失主会立即推送通知"
        style="margin-bottom: 16px"
      />

      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="物品标题" prop="title">
          <el-input v-model="form.title" placeholder="如：捡到黑色 iPhone13 手机" />
        </el-form-item>
        <el-form-item label="物品分类" prop="category_id">
          <el-cascader
            v-model="cascader"
            :options="categoryOptions"
            :props="{ checkStrictly: true, value: 'id', label: 'name' }"
            placeholder="请选择分类"
            clearable
            @change="onCategoryChange"
          />
        </el-form-item>
        <el-form-item label="拾获地点" prop="place">
          <el-input v-model="form.place" placeholder="如：图书馆三楼自习室（系统会自动归一化分区）" />
        </el-form-item>
        <el-form-item label="拾获时间" prop="happen_time">
          <el-date-picker
            v-model="form.happen_time"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm"
            placeholder="选择拾获时间"
          />
        </el-form-item>
        <el-form-item label="保管点">
          <el-input v-model="form.storage_place" placeholder="如：保卫处 3 号柜" />
        </el-form-item>
        <el-form-item label="特征标签">
          <el-select v-model="form.features" multiple filterable allow-create default-first-option
            placeholder="输入后回车添加，如：黑色、iPhone13">
          </el-select>
        </el-form-item>
        <el-form-item label="详细描述">
          <el-input v-model="form.description" type="textarea" :rows="4"
            placeholder="尽量描述颜色、品牌、磨损痕迹等可用于核实的细节" />
        </el-form-item>
        <el-form-item label="物品图片">
          <UploadImages v-model="form.images" entity-type="found_item" :limit="3" />
        </el-form-item>
        <el-form-item label="敏感物品">
          <el-switch v-model="form.is_sensitive" />
          <span class="lf-muted" style="margin-left: 8px">
            证件/卡包类请开启，列表页将隐藏完整描述与图片
          </span>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="submit">提交登记</el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createFound, fetchMeta } from '@/api/items'
import { ensureCsrf } from '@/api/request'
import UploadImages from '@/components/UploadImages.vue'

const router = useRouter()
const formRef = ref()
const loading = ref(false)
const categoryOptions = ref([])
const cascader = ref([])

const form = reactive({
  title: '',
  category_id: null,
  place: '',
  happen_time: '',
  storage_place: '',
  features: [],
  description: '',
  images: [],
  is_sensitive: false
})

const rules = {
  title: [{ required: true, message: '请填写物品标题', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择物品分类', trigger: 'change' }],
  place: [{ required: true, message: '请填写拾获地点', trigger: 'blur' }],
  happen_time: [{ required: true, message: '请选择拾获时间', trigger: 'change' }]
}

onMounted(async () => {
  try {
    const res = await fetchMeta()
    categoryOptions.value = (res.data?.categories || []).map((c) => ({
      id: c.id,
      name: c.name,
      children: (c.children || []).map((ch) => ({ id: ch.id, name: ch.name }))
    }))
  } catch (e) {
    /* 忽略 */
  }
})

function onCategoryChange(value) {
  const ids = Array.isArray(value) ? value.flat() : [value]
  form.category_id = ids[ids.length - 1] || null
}

async function submit() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await ensureCsrf()
      const res = await createFound({ ...form })
      ElMessage.success(res.msg || '拾获登记成功')
      router.push(`/found/${res.data.id}`)
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.form-card {
  width: min(760px, 96%);
  margin: 0 auto;
}
</style>
