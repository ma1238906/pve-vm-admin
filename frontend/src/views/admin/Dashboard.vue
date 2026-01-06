<template>
  <div>
    <h2 style="margin-bottom: 20px;">系统仪表盘</h2>
    
    <el-row :gutter="20" style="margin-bottom: 20px;">
        <el-col :span="6">
            <el-card shadow="hover">
                <template #header>节点总数</template>
                <div class="stat-number">{{ stats.nodes_count }}</div>
            </el-card>
        </el-col>
        <el-col :span="6">
            <el-card shadow="hover">
                <template #header>在线节点</template>
                <div class="stat-number" style="color: #67C23A">{{ stats.online_nodes }}</div>
            </el-card>
        </el-col>
        <el-col :span="6">
             <el-card shadow="hover">
                <template #header>虚拟机总数</template>
                <div class="stat-number">{{ totalVms }}</div>
            </el-card>
        </el-col>
        <el-col :span="6">
             <el-card shadow="hover">
                <template #header>运行中虚拟机</template>
                <div class="stat-number" style="color: #409EFF">{{ runningVms }}</div>
            </el-card>
        </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>集群 CPU 使用率</template>
          <div ref="cpuChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>集群内存使用率</template>
          <div ref="memChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import * as echarts from 'echarts'
import request from '../../api/request'

const cpuChart = ref(null)
const memChart = ref(null)
const runningVms = ref(0)
const totalVms = ref(0)
const stats = reactive({
    nodes_count: 0,
    online_nodes: 0,
    total_cpu: 0,
    used_cpu: 0,
    total_mem: 0,
    used_mem: 0
})

let cpuChartInstance = null
let memChartInstance = null

const updateCharts = () => {
    if (!cpuChartInstance) cpuChartInstance = echarts.init(cpuChart.value)
    if (!memChartInstance) memChartInstance = echarts.init(memChart.value)

    const cpuUsage = stats.total_cpu > 0 ? (stats.used_cpu / stats.total_cpu * 100).toFixed(1) : 0
    const memUsage = stats.total_mem > 0 ? (stats.used_mem / stats.total_mem * 100).toFixed(1) : 0

    cpuChartInstance.setOption({
        series: [{
            type: 'gauge',
            progress: { show: true },
            detail: { valueAnimation: true, formatter: '{value}%' },
            data: [{ value: cpuUsage, name: 'CPU' }]
        }]
    })

    memChartInstance.setOption({
         series: [{
            type: 'gauge',
            progress: { show: true },
            detail: { valueAnimation: true, formatter: '{value}%' },
            data: [{ value: memUsage, name: 'Memory' }]
        }]
    })
}

onMounted(async () => {
    try {
        // Fetch PVE Cluster Stats
        const dashData = await request.get('/vms/dashboard')
        Object.assign(stats, dashData)
        
        // Fetch VMs for counts
        const vms = await request.get('/vms/')
        totalVms.value = vms.length
        runningVms.value = vms.filter(vm => vm.status === 'running').length
        
        updateCharts()
    } catch (e) {
        console.error(e)
    }
})
</script>

<style scoped>
.stat-number {
    font-size: 28px;
    font-weight: bold;
    text-align: center;
    color: #303133;
}
</style>
