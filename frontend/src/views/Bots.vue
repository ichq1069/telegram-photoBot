<template>
  <div class="bots-page">
    <div class="page-header">
      <h3>机器人管理</h3>
      <el-button type="primary" @click="showDialog(null)">添加机器人</el-button>
    </div>

    <el-table :data="bots" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="名称" width="150" />
      <el-table-column prop="bot_token" label="Token" min-width="200">
        <template #default="{ row }">
          <span>{{ row.bot_token?.substring(0, 20) }}...</span>
        </template>
      </el-table-column>
      <el-table-column prop="api_mode" label="API模式" width="100">
        <template #default="{ row }">
          <el-tag :type="row.api_mode === 'official' ? '' : 'warning'" size="small">
            {{ row.api_mode === 'official' ? '官方' : '自建' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">
            {{ statusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="group_name" label="分组" width="100" />
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="checkBot(row)">检测</el-button>
          <el-button size="small" type="primary" @click="showDialog(row)">编辑</el-button>
          <el-popconfirm title="确定删除?" @confirm="deleteBot(row.id)">
            <template #reference>
              <el-button size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editingBot ? '编辑机器人' : '添加机器人'" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="Bot Token" prop="bot_token">
          <el-input v-model="form.bot_token" />
        </el-form-item>
        <el-form-item label="Chat ID">
          <el-input v-model="form.chat_id" placeholder="可选，存储消息的目标ID" />
        </el-form-item>
        <el-form-item label="分组">
          <el-input v-model="form.group_name" />
        </el-form-item>
        <el-form-item label="代理URL">
          <el-input v-model="form.proxy_url" placeholder="可选" />
        </el-form-item>
        <el-form-item label="API模式" prop="api_mode">
          <el-radio-group v-model="form.api_mode">
            <el-radio value="official">官方API</el-radio>
            <el-radio value="self_build">自建中转API</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveBot" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { botAPI } from '@/api/endpoints'

const bots = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editingBot = ref(null)
const saving = ref(false)
const formRef = ref()

const form = reactive({
  name: '',
  bot_token: '',
  chat_id: '',
  group_name: 'default',
  proxy_url: '',
  api_mode: 'official',
})

const rules = {
  name: [{ required: true, message: '请输入名称' }],
  bot_token: [{ required: true, message: '请输入Bot Token' }],
}

function statusType(status) {
  return { online: 'success', offline: 'info', error: 'danger', disabled: 'warning' }[status] || 'info'
}

function statusLabel(status) {
  return { online: '在线', offline: '离线', error: '异常', disabled: '已禁用' }[status] || status
}

async function fetchBots() {
  loading.value = true
  try {
    const res = await botAPI.list()
    bots.value = res.data
  } finally {
    loading.value = false
  }
}

function showDialog(bot) {
  editingBot.value = bot
  if (bot) {
    Object.assign(form, {
      name: bot.name,
      bot_token: bot.bot_token,
      chat_id: bot.chat_id || '',
      group_name: bot.group_name,
      proxy_url: bot.proxy_url || '',
      api_mode: bot.api_mode,
    })
  } else {
    formRef.value?.resetFields()
    form.chat_id = ''
    form.proxy_url = ''
  }
  dialogVisible.value = true
}

async function saveBot() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (editingBot.value) {
      await botAPI.update(editingBot.value.id, form)
    } else {
      await botAPI.create(form)
    }
    ElMessage.success(editingBot.value ? '更新成功' : '添加成功')
    dialogVisible.value = false
    fetchBots()
  } finally {
    saving.value = false
  }
}

async function deleteBot(id) {
  await botAPI.delete(id)
  ElMessage.success('删除成功')
  fetchBots()
}

async function checkBot(bot) {
  try {
    const res = await botAPI.check(bot.id)
    const r = res.data
    ElMessage.info(r.online ? `[${r.name}] 在线 - @${r.username || 'unknown'}` : `[${r.name}] 离线: ${r.error || ''}`)
    fetchBots()
  } catch {}
}

onMounted(fetchBots)
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h3 {
  margin: 0;
}
</style>
