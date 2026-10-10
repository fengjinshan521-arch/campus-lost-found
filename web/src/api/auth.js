import request from './request'

export const login = (data) => request.post('/auth/login', data)
export const register = (data) => request.post('/auth/register', data)
export const logout = () => request.post('/auth/logout')
export const fetchMe = () => request.get('/me')
export const changePassword = (data) => request.post('/auth/change-password', data)
export const forgotPassword = (data) => request.post('/auth/forgot-password', data)
export const resetPassword = (data) => request.post('/auth/reset-password', data)
export const verifyIdentity = (data) => request.post('/auth/verify', data)
export const updateProfile = (data) => request.put('/auth/profile', data)
