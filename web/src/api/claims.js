import request from './request'

export const createClaim = (data) => request.post('/claims/create', data)
export const fetchMyClaims = () => request.get('/claims/mine')
export const fetchInbox = () => request.get('/claims/inbox')
export const fetchPendingClaims = () => request.get('/claims/pending')
export const fetchClaimDetail = (id) => request.get(`/claims/${id}`)
export const fetchClaimTrace = (id) => request.get(`/claims/trace/${id}`)

export const approveClaim = (id, comment) => request.post(`/claims/${id}/approve`, { comment })
export const rejectClaim = (id, comment) => request.post(`/claims/${id}/reject`, { comment })
export const cancelClaim = (id) => request.post(`/claims/${id}/cancel`)
export const archiveClaim = (id) => request.post(`/claims/${id}/archive`)

export const fetchClaimMeta = () => request.get('/claims/meta')
