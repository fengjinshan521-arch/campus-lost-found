<template>
  <div class="uploader">
    <el-upload
      :file-list="fileList"
      list-type="picture-card"
      :http-request="customUpload"
      :on-remove="onRemove"
      :limit="limit"
      accept="image/png,image/jpeg,image/gif,image/webp"
    >
      <el-icon><Plus /></el-icon>
    </el-upload>
    <div class="lf-muted">支持 png/jpg/gif/webp，单张不超过 {{ limit }} 张，服务端会校验文件头魔数</div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { uploadImage } from '@/api/items'
import { ensureCsrf } from '@/api/request'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  limit: { type: Number, default: 3 },
  entityType: { type: String, default: 'misc' }
})
const emit = defineEmits(['update:modelValue'])

const fileList = ref(
  (props.modelValue || []).map((url, i) => ({ name: `image-${i}`, url }))
)

watch(
  () => props.modelValue,
  (val) => {
    fileList.value = (val || []).map((url, i) => ({ name: `image-${i}`, url }))
  }
)

async function customUpload(options) {
  await ensureCsrf()
  const formData = new FormData()
  formData.append('file', options.file)
  formData.append('entity_type', props.entityType)
  try {
    const res = await uploadImage(formData)
    const url = res.data.url
    const next = [...(props.modelValue || []), url]
    emit('update:modelValue', next)
    options.onSuccess(res.data)
  } catch (e) {
    ElMessage.error(e?.message || '上传失败')
    options.onError(e)
  }
}

function onRemove(file, list) {
  const urls = list.map((f) => f.url).filter(Boolean)
  emit('update:modelValue', urls)
}
</script>

<style scoped>
.uploader {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
