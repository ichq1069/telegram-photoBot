<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6" v-for="card in statCards" :key="card.label">
        <el-card class="stat-card">
          <div class="stat-label">{{ card.label }}</div>
          <div class="stat-value">{{ card.value }}</div>
        </el-card>
      </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="12">
        <el-card header="图片上传统计">
          <div class="stat-item">
            <span>今日上传</span>
            <strong>{{ imageStats.today_upload_count }}</strong>
          </div>
          <div class="stat-item">
            <span>本月上传</span>
            <strong>{{ imageStats.month_upload_count }}</strong>
          </div>
          <div class="stat-item">
            <span>总图片数</span>
            <strong>{{ imageStats.total_count }}</strong>
          </div>
          <div class="stat-item">
            <span>总访问量</span>
            <strong>{{ imageStats.total_views }}</strong>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card header="系统资源">
          <div class="stat-item">
            <span>CPU 使用率</span>
            <strong>{{ stats.cpu_percent }}%</strong>
          </div>
          <div class="stat-item">
            <span>内存使用率</span>
            <strong>{{ stats.memory_percent }}%</strong>
          </div>
          <div class="stat-item">
            <span>磁盘使用率</span>
            <strong>{{ stats.disk_percent }}%</strong>
          </div>
          <div class="stat-item">
            <span>运行时间</span>
            <strong>{{ uptimeDisplay }}</strong>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { imageAPI, systemAPI } from '@/api/endpoints'

const stats = ref({ cpu_percent: 0, memory_percent: 0, disk_percent: 0, total_images: 0, total_bots: 0, uptime_seconds: 0 })
const imageStats = ref({ today_upload_count: 0, month_upload_count: 0, total_count: 0, total_size: 0, total_views: 0 })

const statCards = computed(() => [
  { label: '机器人数量', value: stats.value.total_bots },
  { label: '图片总数', value: stats.value.total_images },
  { label: '今日上传', value: imageStats.value.today_upload_count },
  { label: '总访问量', value: imageStats.value.total_views },
])

const uptimeDisplay = computed(() => {
  const s = stats.value.uptime_seconds
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  return `${h}小时${m}分钟`
})

onMounted(async () => {
  try {
    const [sRes, iRes] = await Promise.all([systemAPI.stats(), imageAPI.stats()])
    stats.value = sRes.data
    imageStats.value = iRes.data
  } catch {}
})
</script>

<style scoped>
.stat-card {
  text-align: center;
}
.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}
.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}
.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}
</style>
