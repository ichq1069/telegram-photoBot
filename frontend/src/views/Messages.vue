<template>
  <div class="messages-page">
    <div class="page-header">
      <h3>消息管理</h3>
      <el-button type="primary" @click="showTemplateDialog(null)">添加模板</el-button>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="消息模板" name="templates">
        <el-table :data="templates" stripe>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="name" label="模板名称" width="150" />
          <el-table-column prop="bot_id" label="机器人ID" width="100" />
          <el-table-column prop="trigger_keyword" label="触发关键词" width="150" />
          <el-table-column prop="reply_type" label="回复类型" width="100" />
          <el-table-column prop="reply_content" label="回复内容" min-width="200" show-overflow-tooltip />
          <el-table-column label="操作" width="200">
            <template #default="{ row }">
              <el-button size="small" @click="showTemplateDialog(row)">编辑</el-button>
              <el-popconfirm title="确定删除?" @confirm="deleteTemplate(row.id)">
                <template #reference>
                  <el-button size="small" type="danger">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="批量推送" name="broadcast">
        <el-card>
          <el-form :model="broadcastForm" label-width="100px" style="max-width:600px">
            <el-form-item label="选择机器人">
              <el-select v-model="broadcastForm.bot_id" placeholder="选择机器人" style="width:100%">
                <el-option v-for="b in bots" :key="b.id" :label="b.name" :value="b.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="目标Chat ID">
              <el-input v-model="broadcastForm.chat_ids_str" placeholder="多个ID用逗号分隔" />
            </el-form-item>
            <el-form-item label="消息内容">
              <el-input v-model="broadcastForm.message" type="textarea" :rows="4" placeholder="支持HTML格式" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="sendBroadcast" :loading="broadcasting">发送</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="templateDialogVisible" :title="editingTemplate ? '编辑模板' : '添加模板'" width="500px">
      <el-form ref="templateFormRef" :model="templateForm" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="templateForm.name" />
        </el-form-item>
        <el-form-item label="机器人ID" required>
          <el-input-number v-model="templateForm.bot_id" :min="1" />
        </el-form-item>
        <el-form-item label="触发关键词">
          <el-input v-model="templateForm.trigger_keyword" placeholder="留空则为欢迎语" />
        </el-form-item>
        <el-form-item label="回复类型">
          <el-select v-model="templateForm.reply_type">
            <el-option label="文本" value="text" />
            <el-option label="图片" value="photo" />
            <el-option label="文件" value="document" />
          </el-select>
        </el-form-item>
        <el-form-item label="回复内容">
          <el-input v-model="templateForm.reply_content" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="欢迎语">
          <el-input v-model="templateForm.welcome_message" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="templateDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveTemplate" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { messageAPI, botAPI } from '@/api/endpoints'

const activeTab = ref('templates')
const templates = ref([])
const bots = ref([])
const templateDialogVisible = ref(false)
const editingTemplate = ref(null)
const saving = ref(false)
const broadcasting = ref(false)

const templateForm = reactive({
  name: '', bot_id: 1, trigger_keyword: '', reply_type: 'text',
  reply_content: '', welcome_message: '',
})

const broadcastForm = reactive({
  bot_id: null, chat_ids_str: '', message: '',
})

async function fetchData() {
  const [tRes, bRes] = await Promise.all([
    messageAPI.templates(),
    botAPI.list(),
  ])
  templates.value = tRes.data
  bots.value = bRes.data
}

function showTemplateDialog(tpl) {
  editingTemplate.value = tpl
  if (tpl) {
    Object.assign(templateForm, {
      name: tpl.name, bot_id: tpl.bot_id,
      trigger_keyword: tpl.trigger_keyword || '',
      reply_type: tpl.reply_type,
      reply_content: tpl.reply_content || '',
      welcome_message: tpl.welcome_message || '',
    })
  } else {
    Object.assign(templateForm, {
      name: '', bot_id: 1, trigger_keyword: '', reply_type: 'text',
      reply_content: '', welcome_message: '',
    })
  }
  templateDialogVisible.value = true
}

async function saveTemplate() {
  saving.value = true
  try {
    if (editingTemplate.value) {
      await messageAPI.updateTemplate(editingTemplate.value.id, templateForm)
    } else {
      await messageAPI.createTemplate(templateForm)
    }
    ElMessage.success(editingTemplate.value ? '更新成功' : '添加成功')
    templateDialogVisible.value = false
    fetchData()
  } finally {
    saving.value = false
  }
}

async function deleteTemplate(id) {
  await messageAPI.deleteTemplate(id)
  ElMessage.success('删除成功')
  fetchData()
}

async function sendBroadcast() {
  if (!broadcastForm.bot_id || !broadcastForm.chat_ids_str || !broadcastForm.message) {
    ElMessage.warning('请填写完整信息')
    return
  }
  broadcasting.value = true
  try {
    const res = await messageAPI.broadcast({
      bot_id: broadcastForm.bot_id,
      chat_ids: broadcastForm.chat_ids_str.split(',').map(s => s.trim()).filter(Boolean),
      message: broadcastForm.message,
    })
    ElMessage.success(`发送完成: 成功${res.data.success.length}个, 失败${res.data.failed.length}个`)
  } finally {
    broadcasting.value = false
  }
}

onMounted(fetchData)
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
