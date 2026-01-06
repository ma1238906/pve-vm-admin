<template>
  <div>
    <div class="header-actions">
      <h2>用户管理</h2>
      <el-button type="primary" @click="showCreateDialog">新建用户</el-button>
    </div>

    <el-table :data="users" style="width: 100%" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="80" sortable />
      <el-table-column prop="username" label="用户名" sortable />
      <el-table-column prop="is_superuser" label="角色" width="120">
          <template #default="scope">
              <el-tag :type="scope.row.is_superuser ? 'danger' : 'info'">{{ scope.row.is_superuser ? '管理员' : '普通用户' }}</el-tag>
          </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="100">
          <template #default="scope">
               <el-tag :type="scope.row.is_active ? 'success' : 'danger'">{{ scope.row.is_active ? '启用' : '禁用' }}</el-tag>
          </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="scope">
           <el-popconfirm title="确定要删除此用户吗？" @confirm="handleDelete(scope.row)" v-if="scope.row.username !== 'admin'">
              <template #reference>
                  <el-button size="small" type="danger">删除</el-button>
              </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- Create Dialog -->
    <el-dialog v-model="createDialogVisible" title="创建新用户">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="createForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="createForm.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleCreate" :loading="createLoading">创建</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '../../api/request'
import { ElMessage } from 'element-plus'

const users = ref([])
const loading = ref(false)
const createDialogVisible = ref(false)
const createLoading = ref(false)

const createForm = ref({
  username: '',
  password: ''
})

const fetchData = async () => {
  loading.value = true
  try {
    users.value = await request.get('/users/')
  } catch (error) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const showCreateDialog = () => {
    createForm.value = { username: '', password: '' }
    createDialogVisible.value = true
}

const handleCreate = async () => {
    if (!createForm.value.username || !createForm.value.password) {
        ElMessage.warning('请输入用户名和密码')
        return
    }
    createLoading.value = true
    try {
        await request.post('/users/', createForm.value)
        ElMessage.success('用户创建成功')
        createDialogVisible.value = false
        fetchData()
    } catch (error) {
        ElMessage.error('创建失败: ' + (error.response?.data?.detail || '未知错误'))
    } finally {
        createLoading.value = false
    }
}

const handleDelete = async (row) => {
    try {
        await request.delete(`/users/${row.id}`)
        ElMessage.success('用户已删除')
        fetchData()
    } catch (error) {
        ElMessage.error('删除失败: ' + (error.response?.data?.detail || '未知错误'))
    }
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
</style>
