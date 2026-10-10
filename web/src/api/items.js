import request from './request'

export const fetchMeta = () => request.get('/meta')

export const fetchFoundList = (params) => request.get('/items/found', { params })
export const fetchLostList = (params) => request.get('/items/lost', { params })
export const globalSearch = (params) => request.get('/items/search', { params })

export const fetchFoundDetail = (id) => request.get(`/items/found/${id}`)
export const fetchLostDetail = (id) => request.get(`/items/lost/${id}`)

export const createFound = (data) => request.post('/items/found', data)
export const createLost = (data) => request.post('/items/lost', data)
export const updateFound = (id, data) => request.put(`/items/found/${id}`, data)
export const updateLost = (id, data) => request.put(`/items/lost/${id}`, data)

export const cancelFound = (id) => request.post(`/items/found/${id}/cancel`)
export const cancelLost = (id) => request.post(`/items/lost/${id}/cancel`)
export const archiveFound = (id) => request.post(`/items/found/${id}/archive`)

export const fetchMyItems = () => request.get('/items/mine')
export const fetchFoundMatches = (id) => request.get(`/items/found/${id}/matches`)
export const fetchLostMatches = (id) => request.get(`/items/lost/${id}/matches`)
export const fetchItemClaims = (id) => request.get(`/items/found/${id}/claims`)
export const fetchCanHandle = (id) => request.get(`/items/found/${id}/can-handle`)

export const uploadImage = (formData) =>
  request.post('/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
