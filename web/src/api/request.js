import axios from 'axios'
import { ElMessage } from 'element-plus'

// CSRF Token：从任意响应头 X-CSRFToken 取得，写操作自动回传
let csrfToken = ''

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  timeout: 20000,
  withCredentials: true
})

service.interceptors.request.use((config) => {
  const method = (config.method || 'get').toLowerCase()
  if (!['get', 'head', 'options'].includes(method) && csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken
  }
  return config
})

service.interceptors.response.use(
  (response) => {
    const token = response.headers['x-csrftoken']
    if (token) csrfToken = token

    const data = response.data
    if (data && typeof data === 'object' && 'code' in data) {
      if (data.code === 0) return data
      ElMessage.error(data.msg || '请求失败')
      return Promise.reject(new Error(data.msg || '请求失败'))
    }
    return data
  },
  (error) => {
    const status = error.response?.status
    const msg = error.response?.data?.msg || error.message || '网络异常'
    if (status === 401) ElMessage.warning('请先登录')
    else if (status === 403) ElMessage.error('没有操作权限')
    else if (status === 413) ElMessage.error('上传文件体积超限')
    else ElMessage.error(msg)
    return Promise.reject(error)
  }
)

/** 首次写操作前主动换取 CSRF Token */
export function ensureCsrf() {
  return service.get('/csrf-token').then((res) => {
    csrfToken = res?.data?.csrf_token || csrfToken
    return csrfToken
  })
}

export default service
