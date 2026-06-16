<template>
  <div class="users-page">
    <div class="page-header">
      <h3>用户管理</h3>
      <el-button type="primary" @click="showDialog(null)">添加用户</el-button>
    </div>

    <el-table :data="users" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" width="150" />
      <el-table-column prop="role" label="角色" width="100">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">
            {{ row.role === 'admin' ? '管理员' : row.role }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'warning'" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="last_login_time" label="最后登录" width="170" />
      <el-table-column prop="last_login_ip" label="登录IP" width="140" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="showDialog(row)">编辑</el-button>
          <el-popconfirm title="确定删除?" @confirm="deleteUser(row.id)">
            <template #reference>
              <el-button size="small" type="danger" :disabled="row.id === 1">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editingUser ? '编辑用户' : '添加用户'" width="460px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="!!editingUser" />
        </el-form-item>
        <el-form-item label="密码" :prop="editingUser ? '' : 'password'">
          <el-input v-model="form.password" type="password" show-password :placeholder="editingUser ? '留空则不修改' : ''" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role">
            <el-option label="管理员 (全权限)" value="admin" />
            <el-option label="图床权限" value="image_only" />
            <el-option label="机器人权限" value="bot_only" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveUser" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { userAPI } from '@/api/endpoints'

const users = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editingUser = ref(null)
const saving = ref(false)
const formRef = ref()

const form = reactive({
  username: '',
  password: '',
  role: 'admin',
})

const rules = {
  username: [{ required: true, message: '请输入用户名' }],
  password: [{ required: true, message: '请输入密码', min: 6 }],
}

async function fetchUsers() {
  loading.value = true
  try {
    const res = await userAPI.list()
    users.value = res.data
  } finally {
    loading.value = false
  }
}

function showDialog(user) {
  editingUser.value = user
  if (user) {
    form.username = user.username
    form.password = ''
    form.role = user.role
  } else {
    form.username = ''
    form.password = ''
    form.role = 'admin'
  }
  dialogVisible.value = true
}

async function saveUser() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const data = editingUser.value
      ? { role: form.role, ...(form.password ? { password: form.password } : {}) }
      : { username: form.username, password: form.password, role: form.role }

    if (editingUser.value) {
      await userAPI.update(editingUser.value.id, data)
    } else {
      await userAPI.create(data)
    }
    ElMessage.success(editingUser.value ? '更新成功' : '添加成功')
    dialogVisible.value = false
    fetchUsers()
  } finally {
    saving.value = false
  }
}

async function deleteUser(id) {
  await userAPI.delete(id)
  ElMessage.success('删除成功')
  fetchUsers()
}

onMounted(fetchUsers)
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h3 { margin: 0; }
</style>
