<template>
  <div>
    <div class="header-actions">
      <h2>虚拟机管理</h2>
      <el-button type="primary" @click="showCloneDialog">新建 / 克隆虚拟机</el-button>
    </div>

    <el-table :data="vms" style="width: 100%" v-loading="loading" border stripe :row-class-name="tableRowClassName">
      <el-table-column prop="vmid" label="VM ID" width="100" sortable />
      <el-table-column prop="name" label="名称" sortable />
      <el-table-column prop="node" label="节点" width="120" sortable />
      <el-table-column prop="status" label="状态" width="120">
        <template #default="scope">
          <el-tag :type="getStatusType(scope.row.status)">{{ formatStatus(scope.row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="分配用户" width="150">
          <template #default="scope">
             <span v-if="scope.row.sync_status === 'orphan'" style="color: #E6A23C">未纳管</span>
             <span v-else-if="scope.row.sync_status === 'missing'" style="color: #F56C6C">PVE中已删除</span>
             <span v-else>{{ getUserName(scope.row.owner_id) }}</span>
          </template>
      </el-table-column>
      <el-table-column label="资源使用" width="180">
          <template #default="scope">
             <div v-if="scope.row.status === 'running'">
                 <div>CPU: {{ (scope.row.cpu * 100).toFixed(1) }}%</div>
                 <div>Mem: {{ (scope.row.maxmem > 0 ? scope.row.maxmem / 1024 / 1024 / 1024 : 0).toFixed(1) }} GB</div>
             </div>
             <div v-else>-</div>
          </template>
      </el-table-column>
      <el-table-column label="操作" width="300" fixed="right">
        <template #default="scope">
          <template v-if="scope.row.sync_status === 'ok'">
              <el-button size="small" type="success" @click="handleAction(scope.row, 'start')" :disabled="scope.row.status === 'running'">启动</el-button>
              <el-button size="small" type="warning" @click="handleAction(scope.row, 'stop')" :disabled="scope.row.status === 'stopped'">停止</el-button>
              <el-button size="small" type="danger" @click="handleAction(scope.row, 'shutdown')" :disabled="scope.row.status === 'stopped'">关机</el-button>
              <el-popconfirm title="确定要删除此虚拟机吗？" @confirm="handleDelete(scope.row)">
                  <template #reference>
                      <el-button size="small" type="info">删除</el-button>
                  </template>
              </el-popconfirm>
          </template>
          <template v-else-if="scope.row.sync_status === 'orphan'">
              <el-button size="small" type="primary" @click="showImportDialog(scope.row)">纳管 / 分配</el-button>
          </template>
          <template v-else-if="scope.row.sync_status === 'missing'">
              <el-popconfirm title="确定要清理此记录吗？" @confirm="handleDelete(scope.row)">
                  <template #reference>
                      <el-button size="small" type="danger">清理记录</el-button>
                  </template>
              </el-popconfirm>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <!-- Clone Dialog -->
    <el-dialog v-model="cloneDialogVisible" title="创建虚拟机 (从模板克隆)">
      <el-form :model="cloneForm" label-width="120px">
        <el-form-item label="选择模板">
          <el-select v-model="cloneForm.vmid" placeholder="请选择模板" style="width: 100%">
            <el-option
              v-for="item in templates"
              :key="item.vmid"
              :label="item.name + ' (' + item.vmid + ')'"
              :value="item.vmid"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="所属节点">
           <el-input v-model="cloneForm.node" disabled placeholder="根据模板自动选择" />
        </el-form-item>
        <el-form-item label="新虚拟机名称">
          <el-input v-model="cloneForm.name" placeholder="请输入名称" />
        </el-form-item>
        <el-form-item label="分配给用户">
           <el-select v-model="cloneForm.owner_id" placeholder="请选择用户" style="width: 100%">
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="cloneDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleClone" :loading="cloneLoading">创建</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Import Dialog -->
    <el-dialog v-model="importDialogVisible" title="纳管虚拟机">
        <el-form :model="importForm" label-width="120px">
            <el-form-item label="VM ID">
                <el-input v-model="importForm.vmid" disabled />
            </el-form-item>
            <el-form-item label="名称">
                <el-input v-model="importForm.name" disabled />
            </el-form-item>
             <el-form-item label="分配给用户">
                <el-select v-model="importForm.owner_id" placeholder="请选择用户" style="width: 100%">
                    <el-option
                    v-for="user in users"
                    :key="user.id"
                    :label="user.username"
                    :value="user.id"
                    />
                </el-select>
            </el-form-item>
        </el-form>
        <template #footer>
            <span class="dialog-footer">
                <el-button @click="importDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="handleImport" :loading="importLoading">确定纳管</el-button>
            </span>
        </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import request from '../../api/request'
import { ElMessage } from 'element-plus'

const vms = ref([])
const templates = ref([])
const users = ref([])
const loading = ref(false)
const cloneDialogVisible = ref(false)
const cloneLoading = ref(false)
const importDialogVisible = ref(false)
const importLoading = ref(false)

const cloneForm = ref({
  vmid: null,
  node: '',
  name: '',
  owner_id: null
})

const importForm = ref({
    vmid: null,
    node: '',
    name: '',
    owner_id: null
})

const fetchData = async () => {
  loading.value = true
  try {
    vms.value = await request.get('/vms/')
    await fetchUsers() // Ensure users are loaded for mapping
  } catch (error) {
    ElMessage.error('获取虚拟机列表失败')
  } finally {
    loading.value = false
  }
}

const fetchTemplates = async () => {
    try {
        const res = await request.get('/vms/templates')
        templates.value = res
    } catch (e) {
        console.error(e)
    }
}

const fetchUsers = async () => {
    try {
        const res = await request.get('/users/')
        users.value = res
    } catch (e) {
        console.error(e)
    }
}

watch(() => cloneForm.value.vmid, (newVal) => {
    const tpl = templates.value.find(t => t.vmid === newVal)
    if (tpl) {
        cloneForm.value.node = tpl.node
    }
})

const showCloneDialog = () => {
    fetchTemplates()
    fetchUsers()
    cloneDialogVisible.value = true
}

const showImportDialog = (row) => {
    fetchUsers()
    importForm.value = {
        vmid: row.vmid,
        node: row.node,
        name: row.name,
        owner_id: null
    }
    importDialogVisible.value = true
}

const handleClone = async () => {
    cloneLoading.value = true
    try {
        await request.post('/vms/clone', cloneForm.value)
        ElMessage.success('虚拟机创建成功')
        cloneDialogVisible.value = false
        fetchData()
    } catch (error) {
        ElMessage.error('创建失败: ' + error.response?.data?.detail)
    } finally {
        cloneLoading.value = false
    }
}

const handleImport = async () => {
    if (!importForm.value.owner_id) {
        ElMessage.warning('请选择用户')
        return
    }
    importLoading.value = true
    try {
        await request.post('/vms/import', importForm.value)
        ElMessage.success('纳管成功')
        importDialogVisible.value = false
        fetchData()
    } catch (error) {
        ElMessage.error('纳管失败: ' + error.response?.data?.detail)
    } finally {
        importLoading.value = false
    }
}

const handleAction = async (row, action) => {
    try {
        await request.post(`/vms/${row.vmid}/${action}`)
        ElMessage.success(`已发送 ${action} 指令`)
        // Refresh after a delay
        setTimeout(fetchData, 3000)
    } catch (error) {
         ElMessage.error('操作失败')
    }
}

const handleDelete = async (row) => {
    try {
        await request.delete(`/vms/${row.vmid}`)
        ElMessage.success('操作成功')
        fetchData()
    } catch (error) {
        ElMessage.error('操作失败')
    }
}

const getStatusType = (status) => {
    if (status === 'running') return 'success'
    if (status === 'stopped') return 'info'
    return 'warning'
}

const formatStatus = (status) => {
    const map = {
        'running': '运行中',
        'stopped': '已停止',
        'unknown': '未知'
    }
    return map[status] || status
}

const getUserName = (id) => {
    const user = users.value.find(u => u.id === id)
    return user ? user.username : '未分配'
}

const tableRowClassName = ({ row }) => {
    if (row.sync_status === 'missing') {
        return 'warning-row'
    } else if (row.sync_status === 'orphan') {
        return 'success-row'
    }
    return ''
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.header-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}
:deep(.warning-row) {
    --el-table-tr-bg-color: #fdf6ec;
}
:deep(.success-row) {
    --el-table-tr-bg-color: #f0f9eb;
}
</style>
