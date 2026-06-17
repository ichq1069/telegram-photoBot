<template>
  <div class="images-page">
    <div class="page-header">
      <h3>图床管理</h3>
      <div class="header-actions">
      <el-upload
        :http-request="handleUpload"
        multiple
        :show-file-list="false"
        accept="image/*"
      >
        <el-button type="primary">上传图片</el-button>
      </el-upload>
        <el-select v-model="filterCategory" placeholder="分类筛选" clearable style="width:140px;margin-left:10px">
          <el-option label="未分类" value="uncategorized" />
          <el-option label="全部" value="" />
        </el-select>
      </div>
    </div>

    <el-card shadow="never" style="margin-bottom:20px">
      <template #header>
        <span>上传配置</span>
      </template>
      <el-form inline>
        <el-form-item label="目标机器人">
          <el-select v-model="uploadBotId" placeholder="选择机器人或留空上传到本地" clearable style="width:200px">
            <el-option
              v-for="bot in bots"
              :key="bot.id"
              :label="bot.name"
              :value="bot.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="API 模式" v-if="selectedBot">
          <el-tag :type="selectedBot.api_mode === 'official' ? '' : 'warning'" size="small">
            {{ selectedBot.api_mode === 'official' ? '官方API' : '自建API' }}
          </el-tag>
        </el-form-item>
        <el-form-item label="频道 Chat ID" v-if="selectedBot">
          <el-input v-model="channelId" placeholder="留空使用机器人配置的 Chat ID" style="width:220px" />
        </el-form-item>
      </el-form>
    </el-card>

    <div v-if="images.length === 0 && !loading" class="empty-state">
      <p>暂无图片，点击上方按钮上传</p>
    </div>

    <el-row :gutter="16" v-loading="loading">
      <el-col :span="6" v-for="img in images" :key="img.id" style="margin-bottom:16px">
        <el-card :body-style="{ padding: '0' }" class="image-card">
          <div class="image-preview" @click="showDetail(img)">
            <img :src="`/api/images/file/${img.id}/thumb`" :alt="img.original_name" />
          </div>
          <div class="image-info">
            <div class="image-name" :title="img.original_name">{{ img.original_name }}</div>
            <div class="image-meta">
              <span>{{ formatSize(img.file_size) }}</span>
              <span>{{ img.view_count }} 次</span>
            </div>
          </div>
          <div class="image-actions">
            <el-button size="small" @click="copyLink(img.direct_link)">复制链接</el-button>
            <el-popconfirm title="确定删除?" @confirm="deleteImage(img.id)">
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="detailVisible" title="图片详情" width="600px">
      <div v-if="selectedImage" class="detail-content">
        <img :src="`/api/images/file/${selectedImage.id}`" style="max-width:100%;border-radius:4px" />
        <el-descriptions :column="2" border style="margin-top:16px">
          <el-descriptions-item label="文件名">{{ selectedImage.original_name }}</el-descriptions-item>
          <el-descriptions-item label="大小">{{ formatSize(selectedImage.file_size) }}</el-descriptions-item>
          <el-descriptions-item label="尺寸">{{ selectedImage.width }}x{{ selectedImage.height }}</el-descriptions-item>
          <el-descriptions-item label="分类">{{ selectedImage.category }}</el-descriptions-item>
        </el-descriptions>
        <div style="margin-top:12px">
          <el-input v-model="selectedImage.direct_link" readonly>
            <template #append>
              <el-button @click="copyLink(selectedImage.direct_link)">复制</el-button>
            </template>
          </el-input>
        </div>
        <div style="margin-top:8px">
          <span>Markdown: </span>
          <el-input v-model="selectedImage.markdown_link" readonly size="small" style="margin-top:4px">
            <template #append>
              <el-button @click="copyLink(selectedImage.markdown_link)">复制</el-button>
            </template>
          </el-input>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { imageAPI, botAPI } from '@/api/endpoints'

const images = ref([])
const loading = ref(false)
const filterCategory = ref('')
const detailVisible = ref(false)
const selectedImage = ref(null)
const bots = ref([])
const uploadBotId = ref(null)
const channelId = ref('')

const selectedBot = computed(() => {
  return bots.value.find(b => b.id === uploadBotId.value) || null
})

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

async function fetchImages() {
  loading.value = true
  try {
    const res = await imageAPI.list({ category: filterCategory.value || undefined })
    images.value = res.data
  } finally {
    loading.value = false
  }
}

async function handleUpload({ file }) {
  const isImage = file.type.startsWith('image/')
  const isLt20M = file.size / 1024 / 1024 < 20
  if (!isImage) {
    ElMessage.error('只能上传图片文件')
    return
  }
  if (!isLt20M) {
    ElMessage.error('图片大小不能超过20MB')
    return
  }
  const formData = new FormData()
  formData.append('file', file)
  try {
    const token = localStorage.getItem('token')
    const params = {}
    if (uploadBotId.value) {
      params.bot_id = uploadBotId.value
    }
    if (channelId.value) {
      params.channel_id = channelId.value
    }
    const res = await imageAPI.upload(formData, {
      headers: { Authorization: `Bearer ${token}` },
      params,
    })
    const data = res.data
    ElMessage.success(`上传成功: ${data.filename}`)
    fetchImages()
  } catch (err) {
    // axios 拦截器已显示错误详情
  }
}

function showDetail(img) {
  selectedImage.value = img
  detailVisible.value = true
}

async function copyLink(text) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch {
    const input = document.createElement('input')
    input.value = text
    document.body.appendChild(input)
    input.select()
    document.execCommand('copy')
    document.body.removeChild(input)
    ElMessage.success('已复制到剪贴板')
  }
}

async function deleteImage(id) {
  await imageAPI.delete(id)
  ElMessage.success('删除成功')
  fetchImages()
}

async function fetchBots() {
  try {
    const res = await botAPI.list()
    bots.value = res.data || []
  } catch {}
}

onMounted(() => {
  fetchImages()
  fetchBots()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h3 { margin: 0; }
.header-actions { display: flex; align-items: center; }
.empty-state {
  text-align: center;
  padding: 80px 0;
  color: #909399;
}
.image-card {
  cursor: pointer;
  transition: box-shadow 0.3s;
}
.image-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.image-preview {
  height: 180px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
}
.image-preview img {
  max-width: 100%;
  max-height: 100%;
  object-fit: cover;
}
.image-info {
  padding: 10px 12px;
}
.image-name {
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.image-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
.image-actions {
  display: flex;
  justify-content: space-around;
  padding: 8px 12px 12px;
  border-top: 1px solid #f0f0f0;
}
</style>
