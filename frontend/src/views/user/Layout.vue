<template>
  <el-container class="layout-container">
    <el-header class="user-header">
      <div class="logo">PVE VDI</div>
      <div class="header-right">
        <el-button v-if="authStore.isAdmin" type="text" @click="router.push('/admin')">管理后台</el-button>
        <span>{{ authStore.user?.username }}</span>
        <el-button type="text" @click="logout">Logout</el-button>
      </div>
    </el-header>
    <el-main class="main-content">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const logout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
  width: 100vw;
  display: flex;
  flex-direction: column;
}
.user-header {
  background-color: #409EFF;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 60px;
  flex-shrink: 0;
}
.main-content {
  padding: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #f5f7fa;
  overflow: hidden;
}
.logo {
  font-size: 20px;
  font-weight: bold;
}
.header-right span {
    margin-right: 15px;
}
.header-right .el-button {
    color: white;
}
</style>
