<template>
  <div class="desktop-container">
    <el-row :gutter="20">
      <el-col :span="6" v-for="vm in vms" :key="vm.id">
        <el-card class="vm-card" :body-style="{ padding: '0px' }">
          <div class="vm-image" @click="connectVM(vm)">
            <div class="os-icon">
                <img v-if="isWindows(vm.os_type)" src="/os-icons/windows.png" alt="Windows" class="os-img" />
                <img v-else-if="isLinux(vm.os_type)" src="/os-icons/linux.png" alt="Linux" class="os-img" />
                <img v-else src="/os-icons/other.png" alt="Other" class="os-img" />
            </div>
            <div class="vm-status" :class="vm.status"></div>
          </div>
          <div style="padding: 14px">
            <div class="vm-name">{{ vm.name }}</div>
            <div class="vm-info">Uptime: {{ formatUptime(vm.uptime) }}</div>
            <div class="bottom">
              <el-button-group>
                <el-button size="small" type="success" @click="handleAction(vm, 'start')" :disabled="vm.status === 'running'">Start</el-button>
                <el-button size="small" type="warning" @click="handleAction(vm, 'reset')" :disabled="vm.status !== 'running'">Restart</el-button>
                <el-button size="small" type="danger" @click="handleAction(vm, 'shutdown')" :disabled="vm.status !== 'running'">Shutdown</el-button>
              </el-button-group>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import request from '../../api/request'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../../stores/auth'

const vms = ref([])
const router = useRouter()
const authStore = useAuthStore()
let pollTimer = null

const fetchData = async () => {
  if (!authStore.token) return
  try {
    vms.value = await request.get('/vms/')
  } catch (error) {
    // Suppress error on unauthenticated redirects
    if (error?.response?.status !== 401) {
      ElMessage.error('Failed to fetch VMs')
    }
  }
}

const connectVM = (vm) => {
    if (vm.status !== 'running') {
        ElMessage.warning('VM is not running')
        return
    }
    router.push({ name: 'VNCViewer', params: { node: vm.node, vmid: vm.vmid } })
}

const handleAction = async (vm, action) => {
    try {
        await request.post(`/vms/${vm.vmid}/${action}`)
        ElMessage.success(`Action ${action} initiated`)
        setTimeout(fetchData, 3000)
    } catch (error) {
         ElMessage.error('Action Failed')
    }
}

const formatUptime = (seconds) => {
    if (!seconds) return '0s'
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    return `${h}h ${m}m`
}

const isWindows = (osType) => {
    if (!osType) return false
    return osType.startsWith('w') || osType.startsWith('win')
}

const isLinux = (osType) => {
    if (!osType) return false
    return ['l26', 'l24'].includes(osType) || osType.includes('linux')
}

onMounted(() => {
  fetchData()
  // Poll status
  pollTimer = setInterval(fetchData, 10000)
})

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})
</script>

<style scoped>
.desktop-container {
    padding: 20px;
}
.vm-card {
    margin-bottom: 20px;
    transition: transform 0.3s;
}
.vm-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.vm-image {
    height: 150px;
    background-color: #ecf5ff;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 60px;
    cursor: pointer;
    position: relative;
}
.vm-status {
    position: absolute;
    top: 10px;
    right: 10px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background-color: #909399;
}
.vm-status.running {
    background-color: #67C23A;
    box-shadow: 0 0 10px #67C23A;
    animation: breathe 2s infinite;
}
.vm-name {
    font-weight: bold;
    font-size: 16px;
    margin-bottom: 5px;
}
.vm-info {
    font-size: 12px;
    color: #909399;
    margin-bottom: 10px;
}
.bottom {
    display: flex;
    justify-content: center;
}
@keyframes breathe {
    0% { opacity: 0.6; }
    50% { opacity: 1; }
    100% { opacity: 0.6; }
}
.os-img {
    width: 80px;
    height: 80px;
    object-fit: contain;
}
</style>
