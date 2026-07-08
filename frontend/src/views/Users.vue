<template>
  <div>
    <div style="margin-bottom:12px;display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:18px;font-weight:bold">用户管理</span>
      <el-button type="primary" @click="openCreate">新增用户</el-button>
    </div>

    <!-- 搜索 -->
    <div style="margin-bottom:12px">
      <el-input v-model="search" placeholder="搜索用户名/姓名..." clearable prefix-icon="Search" style="width:260px" @input="fetchList" />
    </div>

    <!-- 用户列表 -->
    <el-table :data="paginatedUsers" stripe border size="small" style="width:100%">
      <el-table-column prop="username" label="用户名" min-width="100" />
      <el-table-column prop="display_name" label="姓名" min-width="80" />
      <el-table-column prop="phone" label="手机号" min-width="110" />
      <el-table-column label="角色" min-width="100">
        <template #default="{row}">
          <el-tag :type="row.role==='super_admin'?'danger':row.role==='company_admin'?'primary':row.role==='finance'?'warning':''" size="small">
            {{ roleMap[row.role] || row.role }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" min-width="60">
        <template #default="{row}"><el-tag :type="row.is_active?'success':'info'" size="small">{{ row.is_active?'正常':'禁用' }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" min-width="150" />
      <el-table-column label="操作" min-width="260">
        <template #default="{row}">
          <div style="display:flex;gap:4px;align-items:center;flex-wrap:wrap">
            <el-button text type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button text type="success" size="small" @click="openPerm(row)">权限</el-button>
            <el-button text type="warning" size="small" @click="openResetPwd(row)">改密</el-button>
            <el-button text :type="row.is_active?'warning':'success'" size="small" @click="toggleActive(row)">{{ row.is_active?'禁用':'启用' }}</el-button>
            <el-popconfirm title="确定删除此用户？" @confirm="delUser(row.id)">
              <template #reference><el-button text type="danger" size="small">删除</el-button></template>
            </el-popconfirm>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div style="margin-top:10px;display:flex;justify-content:flex-end">
      <el-pagination v-model:page-size="pageSize" :page-sizes="[10,20,50,100]" :total="filteredUsers.length" v-model:current-page="page" layout="total,sizes,prev,pager,next,jumper" background small />
    </div>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="showForm" :title="editId?'编辑用户':'新增用户'" width="450px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="用户名"><el-input v-model="form.username" :disabled="!!editId" /></el-form-item>
        <el-form-item v-if="!editId" label="密码"><el-input v-model="form.password" type="password" show-password /></el-form-item>
        <el-form-item label="姓名"><el-input v-model="form.display_name" /></el-form-item>
        <el-form-item label="手机号"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role" style="width:100%">
            <el-option v-for="(v,k) in roleMap" :key="k" :label="v" :value="k" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="showForm=false">取消</el-button><el-button type="primary" @click="saveUser">{{ editId?'保存':'创建' }}</el-button></template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog v-model="showPwd" title="重置密码" width="380px">
      <el-form label-width="80px">
        <el-form-item label="用户">{{ pwdTarget?.display_name || pwdTarget?.username }}</el-form-item>
        <el-form-item label="新密码"><el-input v-model="newPassword" type="password" show-password /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showPwd=false">取消</el-button><el-button type="primary" @click="submitResetPwd">确定</el-button></template>
    </el-dialog>

    <!-- 权限配置对话框 -->
    <el-dialog v-model="showPerm" title="配置权限" width="480px">
      <el-form label-width="80px">
        <el-form-item label="用户">{{ permTarget?.display_name || permTarget?.username }}</el-form-item>
        <el-form-item label="当前角色">
          <el-tag :type="permTarget?.role==='super_admin'?'danger':permTarget?.role==='company_admin'?'primary':permTarget?.role==='finance'?'warning':''" size="small">
            {{ roleMap[permTarget?.role] || permTarget?.role }}
          </el-tag>
        </el-form-item>
        <el-form-item label="分配角色">
          <el-select v-model="permNewRole" style="width:100%">
            <el-option v-for="(v,k) in roleMap" :key="k" :label="v" :value="k" />
          </el-select>
        </el-form-item>
        <el-divider content-position="left">角色权限说明</el-divider>
        <div v-for="(desc, r) in rolePermissions" :key="r" style="margin-bottom:8px;padding:8px;background:#f9f9f9;border-radius:4px">
          <strong :style="{color: r==='super_admin'?'#F56C6C':r==='company_admin'?'#409EFF':'#333'}">{{ roleMap[r] || r }}</strong>
          <p style="margin:4px 0 0;font-size:12px;color:#666">{{ desc }}</p>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="showPerm=false">取消</el-button>
        <el-button type="primary" @click="submitPerm">保存权限</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import request from '@/api/request'

const users = ref([])
const search = ref('')
const page = ref(1)
const pageSize = ref(10)

const roleMap = { super_admin:'超级管理员', company_admin:'公司管理员', finance:'财务人员', project_manager:'项目负责人', attendance:'工地考勤员', worker:'施工人员' }

const rolePermissions = {
  super_admin: '全部权限：用户管理、系统配置、所有业务模块增删改查、审核与付款。',
  company_admin: '业务管理：项目管理、往来单位、发票、财务、报销审批与付款、人员工时、电子档案。',
  finance: '财务相关：发票管理、财务管理、税金管理、电子收据、报销查看、电子档案、查看自己的薪酬。',
  project_manager: '项目管理、工时记录、报销申请、发票管理、电子收据、电子档案、往来单位、查看自己的薪酬。',
  attendance: '工时管理：添加和编辑工时记录，无审核权限。',
  worker: '基础权限：查看个人相关项目、提交报销申请、电子档案、查看自己工时记录、查看自己的薪酬。',
}

const filteredUsers = computed(() => {
  if (!search.value) return users.value
  const s = search.value.toLowerCase()
  return users.value.filter(u =>
    u.username?.toLowerCase().includes(s) ||
    u.display_name?.toLowerCase().includes(s) ||
    u.phone?.includes(s)
  )
})
const paginatedUsers = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return filteredUsers.value.slice(start, start + pageSize.value)
})

// Create/Edit form
const showForm = ref(false)
const editId = ref(null)
const form = ref({ username:'', password:'', display_name:'', phone:'', role:'worker' })

// Reset password
const showPwd = ref(false)
const pwdTarget = ref(null)
const newPassword = ref('')

// Permission config
const showPerm = ref(false)
const permTarget = ref(null)
const permNewRole = ref('')

async function fetchList() { users.value = await request.get('/auth/users') }

function openCreate() {
  editId.value = null
  form.value = { username:'', password:'', display_name:'', phone:'', role:'worker' }
  showForm.value = true
}

function openEdit(row) {
  editId.value = row.id
  form.value = { username:row.username, password:'', display_name:row.display_name, phone:row.phone||'', role:row.role }
  showForm.value = true
}

async function saveUser() {
  if (editId.value) {
    await request.put(`/auth/users/${editId.value}`, { display_name:form.value.display_name, phone:form.value.phone, role:form.value.role })
  } else {
    await request.post('/auth/users', form.value)
  }
  ElMessage.success(editId.value ? '保存成功' : '创建成功')
  showForm.value = false
  fetchList()
}

function openResetPwd(row) {
  pwdTarget.value = row
  newPassword.value = ''
  showPwd.value = true
}

async function submitResetPwd() {
  if (!newPassword.value) return ElMessage.warning('请输入新密码')
  await request.put(`/auth/users/${pwdTarget.value.id}/password`, { new_password: newPassword.value })
  ElMessage.success('密码已重置')
  showPwd.value = false
}

async function toggleActive(row) {
  await request.put(`/auth/users/${row.id}/toggle-active`)
  ElMessage.success(row.is_active ? '已禁用' : '已启用')
  fetchList()
}

async function delUser(id) {
  await request.delete(`/auth/users/${id}`)
  ElMessage.success('已删除')
  fetchList()
}

function openPerm(row) {
  permTarget.value = row
  permNewRole.value = row.role
  showPerm.value = true
}

async function submitPerm() {
  if (!permTarget.value || !permNewRole.value) return
  await request.put(`/auth/users/${permTarget.value.id}`, { role: permNewRole.value })
  ElMessage.success('权限已更新')
  showPerm.value = false
  fetchList()
}

onMounted(fetchList)
</script>
