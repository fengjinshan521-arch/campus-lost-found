import { defineStore } from 'pinia'
import { fetchMe, login as apiLogin, logout as apiLogout, register as apiRegister } from '@/api/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null,
    loaded: false
  }),
  getters: {
    isLogin: (state) => !!state.user,
    isAdmin: (state) => state.user?.role === 'admin',
    isStaff: (state) => ['admin', 'staff'].includes(state.user?.role),
    displayName: (state) => state.user?.real_name || state.user?.username || '游客'
  },
  actions: {
    async load() {
      try {
        const res = await fetchMe()
        this.user = res.data?.user || null
      } catch (e) {
        this.user = null
      }
      this.loaded = true
    },
    async login(payload) {
      const res = await apiLogin(payload)
      this.user = res.data?.user || null
      return res
    },
    async register(payload) {
      const res = await apiRegister(payload)
      this.user = res.data?.user || null
      return res
    },
    async logout() {
      try {
        await apiLogout()
      } catch (e) {
        /* 忽略：无论服务端结果如何，前端都清理会话 */
      }
      this.user = null
    }
  }
})
