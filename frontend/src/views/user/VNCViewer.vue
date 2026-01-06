<template>
  <div class="vnc-container">
    <div class="vnc-toolbar">
       <el-button size="small" @click="$router.go(-1)">返回</el-button>
       <span class="vnc-title" v-if="node && vmid">VM: {{ vmid }} ({{ node }})</span>
    </div>
    <iframe v-if="vncUrl" :src="vncUrl" class="vnc-frame" frameborder="0"></iframe>
    <div class="overlay" v-if="loading">Loading VNC...</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '../../api/request'
import { ElMessage } from 'element-plus'

const props = defineProps(['node', 'vmid'])
const vncUrl = ref('')
const loading = ref(true)

const connect = async () => {
    try {
        const res = await request.get(`/vms/${props.vmid}/vnc-ticket`)
        const { ticket, port, password } = res
        
        // Use current hostname for WebSocket connection if backend is on same host
        // Or use configured backend host. Here we assume backend is at window.location.hostname
        // But backend port is 8000.
        const wsHost = window.location.hostname
        const wsPort = '8000'
        const wsPath = `api/v1/vms/ws/vncproxy/${props.node}/${props.vmid}?ticket=${encodeURIComponent(ticket)}&port=${port}`
        
        // Construct Iframe URL to local noVNC with robust encoding
        const params = new URLSearchParams({
            host: wsHost,
            port: wsPort,
            path: wsPath,
            password: password || '',
            autoconnect: 'true',
            resize: 'scale'
        })
        vncUrl.value = `/novnc/vnc.html?${params.toString()}`
        
        loading.value = false

    } catch (error) {
        ElMessage.error('Failed to get VNC ticket')
        loading.value = false
    }
}

onMounted(() => {
    connect()
})
</script>

<style scoped>
.vnc-container {
    width: 100%;
    height: 100%;
    background-color: #282c34;
    position: relative;
    display: flex;
    flex-direction: column;
    flex: 1;
}
.vnc-toolbar {
    height: 40px;
    background-color: #333;
    display: flex;
    align-items: center;
    padding: 0 10px;
    color: white;
    flex-shrink: 0;
}
.vnc-title {
    margin-left: 10px;
    font-size: 14px;
    color: #ddd;
}
.vnc-frame {
    width: 100%;
    flex: 1;
    border: none;
    display: block;
}
.overlay {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: white;
    font-size: 20px;
}
</style>
