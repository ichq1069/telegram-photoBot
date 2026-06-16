import api from './index'

export const authAPI = {
  login(username, password) {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)
    return api.post('/auth/login', formData)
  },
  getMe() {
    return api.get('/auth/me')
  },
  changePassword(data) {
    return api.put('/auth/me/password', data)
  },
}

export const botAPI = {
  list(params) { return api.get('/bots', { params }) },
  get(id) { return api.get(`/bots/${id}`) },
  create(data) { return api.post('/bots', data) },
  update(id, data) { return api.put(`/bots/${id}`, data) },
  delete(id) { return api.delete(`/bots/${id}`) },
  check(id) { return api.post(`/bots/${id}/check`) },
  checkAll() { return api.post('/bots/check-all') },
}

export const imageAPI = {
  list(params) { return api.get('/images', { params }) },
  get(id) { return api.get(`/images/${id}`) },
  update(id, data) { return api.put(`/images/${id}`, data) },
  delete(id) { return api.delete(`/images/${id}`) },
  upload(formData) {
    return api.post('/images/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  stats() { return api.get('/images/stats') },
}

export const messageAPI = {
  templates(params) { return api.get('/messages/templates', { params }) },
  createTemplate(data) { return api.post('/messages/templates', data) },
  updateTemplate(id, data) { return api.put(`/messages/templates/${id}`, data) },
  deleteTemplate(id) { return api.delete(`/messages/templates/${id}`) },
  broadcast(data) { return api.post('/messages/broadcast', data) },
}

export const systemAPI = {
  stats() { return api.get('/system/stats') },
  configs() { return api.get('/system/configs') },
  updateConfig(key, data) { return api.put(`/system/configs/${key}`, data) },
  logs(params) { return api.get('/system/logs', { params }) },
  dbStatus() { return api.get('/system/database/status') },
  syncDB() { return api.post('/system/database/sync') },
  switchDB(target) { return api.post(`/system/database/switch/${target}`) },
}

export const userAPI = {
  list(params) { return api.get('/admin/users', { params }) },
  create(data) { return api.post('/admin/users', data) },
  update(id, data) { return api.put(`/admin/users/${id}`, data) },
  delete(id) { return api.delete(`/admin/users/${id}`) },
}
