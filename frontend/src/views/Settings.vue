<template>
  <div class="settings-page">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="系统配置" name="config">
        <el-card>
          <el-form label-width="160px">
            <el-form-item v-for="cfg in configs" :key="cfg.id" :label="cfg.description || cfg.config_key">
              <el-input v-model="cfg.config_value" :disabled="cfg.config_key === 'db_type'">
                <template #append>
                  <el-button @click="saveConfig(cfg.config_key, cfg.config_value)">保存</el-button>
                </template>
              </el-input>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="数据库管理" name="database">
        <el-card>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="当前数据库">{{ dbStatus.current_db }}</el-descriptions-item>
            <el-descriptions-item label="MySQL已配置">{{ dbStatus.mysql_configured ? '是' : '否' }}</el-descriptions-item>
            <el-descriptions-item label="MySQL已连接">{{ dbStatus.mysql_connected ? '是' : '否' }}</el-descriptions-item>
            <el-descriptions-item label="同步已启用">{{ dbStatus.sync_enabled ? '是' : '否' }}</el-descriptions-item>
            <el-descriptions-item label="上次同步时间">{{ dbStatus.last_sync_time || '从未' }}</el-descriptions-item>
          </el-descriptions>
          <div style="margin-top:16px">
            <el-button type="primary" @click="syncDB" :loading="syncingDB">手动同步到MySQL</el-button>
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="系统日志" name="logs">
        <el-card>
          <div class="log-filters">
            <el-select v-model="logFilter.level" placeholder="日志级别" clearable style="width:120px">
              <el-option label="INFO" value="INFO" />
              <el-option label="WARN" value="WARN" />
              <el-option label="ERROR" value="ERROR" />
            </el-select>
            <el-select v-model="logFilter.log_type" placeholder="日志类型" clearable style="width:120px;margin-left:10px">
              <el-option label="上传" value="upload" />
              <el-option label="同步" value="sync" />
              <el-option label="登录" value="login" />
              <el-option label="机器人" value="bot" />
            </el-select>
            <el-input v-model="logFilter.keyword" placeholder="关键词搜索" clearable style="width:200px;margin-left:10px" />
            <el-button type="primary" @click="fetchLogs" style="margin-left:10px">查询</el-button>
          </div>
          <el-table :data="logs" stripe style="margin-top:16px" size="small">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="log_type" label="类型" width="80" />
            <el-table-column prop="level" label="级别" width="70">
              <template #default="{ row }">
                <el-tag :type="row.level === 'ERROR' ? 'danger' : row.level === 'WARN' ? 'warning' : 'info'" size="small">
                  {{ row.level }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="消息" min-width="250" />
            <el-table-column prop="created_at" label="时间" width="170" />
          </el-table>
          <el-pagination
            v-if="logTotal > 0"
            :current-page="logPage"
            :page-size="20"
            :total="logTotal"
            layout="prev, pager, next"
            @current-change="page => { logPage = page; fetchLogs() }"
            style="margin-top:16px;justify-content:flex-end"
          />
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { systemAPI } from '@/api/endpoints'

const activeTab = ref('config')
const configs = ref([])
const dbStatus = ref({})
const syncingDB = ref(false)
const logs = ref([])
const logTotal = ref(0)
const logPage = ref(1)

const logFilter = reactive({ level: '', log_type: '', keyword: '' })

async function fetchConfigs() {
  const res = await systemAPI.configs()
  configs.value = res.data
}

async function saveConfig(key, value) {
  await systemAPI.updateConfig(key, { config_value: value })
  ElMessage.success('配置已更新')
}

async function fetchDBStatus() {
  const res = await systemAPI.dbStatus()
  dbStatus.value = res.data
}

async function syncDB() {
  syncingDB.value = true
  try {
    await systemAPI.syncDB()
    ElMessage.success('同步完成')
    fetchDBStatus()
  } finally {
    syncingDB.value = false
  }
}

async function fetchLogs() {
  const res = await systemAPI.logs({
    log_type: logFilter.log_type || undefined,
    level: logFilter.level || undefined,
    keyword: logFilter.keyword || undefined,
    page: logPage.value,
  })
  logs.value = res.data.items
  logTotal.value = res.data.total
}

onMounted(() => {
  fetchConfigs()
  fetchDBStatus()
  fetchLogs()
})
</script>

<style scoped>
.log-filters {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0;
}
</style>
