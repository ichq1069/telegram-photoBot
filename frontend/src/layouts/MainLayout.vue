<template>
  <el-container class="main-layout">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <h2>PhotoBot</h2>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item index="/dashboard">
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/bots">
          <span>机器人管理</span>
        </el-menu-item>
        <el-menu-item index="/images">
          <span>图床管理</span>
        </el-menu-item>
        <el-menu-item index="/messages">
          <span>消息管理</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <span>系统设置</span>
        </el-menu-item>
        <el-menu-item index="/users">
          <span>用户管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-left">{{ pageTitle }}</div>
        <div class="header-right">
          <span class="user-info">{{ authStore.user?.username }}</span>
          <el-button text @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)
const pageTitle = computed(() => route.meta.title || '')

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
}
.sidebar {
  background-color: #304156;
  overflow-y: auto;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.logo h2 {
  font-size: 18px;
  margin: 0;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
}
.header-left {
  font-size: 16px;
  font-weight: 500;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.user-info {
  color: #606266;
  font-size: 14px;
}
.main-content {
  background: #f0f2f5;
  min-height: calc(100vh - 60px);
}
</style>
