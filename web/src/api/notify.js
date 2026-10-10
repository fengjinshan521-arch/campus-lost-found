import request from './request'

export const fetchNotifications = (params) => request.get('/notifications/', { params })
export const fetchUnreadCount = () => request.get('/notifications/unread-count')
export const markRead = (id) => request.post(`/notifications/${id}/read`)
export const markAllRead = () => request.post('/notifications/read-all')
