import request from './request'

export const fetchStats = () => request.get('/admin/stats')
export const fetchPublicStats = () => request.get('/admin/stats/public')

export const fetchUsers = (params) => request.get('/admin/users', { params })
export const setUserStatus = (id, status) => request.post(`/admin/users/${id}/status`, { status })
export const setUserRole = (id, role) => request.post(`/admin/users/${id}/role`, { role })

export const fetchCategories = () => request.get('/admin/categories')
export const createCategory = (data) => request.post('/admin/categories', data)
export const updateCategory = (id, data) => request.put(`/admin/categories/${id}`, data)
export const deleteCategory = (id) => request.delete(`/admin/categories/${id}`)

export const fetchAdmins = (params) => request.get('/admin/admins', { params })
export const createAdmin = (data) => request.post('/admin/admins', data)
export const updateAdmin = (id, data) => request.put(`/admin/admins/${id}`, data)
export const resetAdminPassword = (id, password) => request.post(`/admin/admins/${id}/password`, { password })
export const setAdminStatus = (id, status) => request.post(`/admin/admins/${id}/status`, { status })

export const fetchLogs = (params) => request.get('/admin/logs', { params })
export const fetchLogTrace = (params) => request.get('/admin/logs/trace', { params })

export const runFullMatch = () => request.post('/admin/match/run')
export const broadcast = (data) => request.post('/admin/notify/broadcast', data)
