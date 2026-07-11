<template>
  <el-container style="height:100vh">
    <el-aside :width="collapsed ? '64px' : '220px'" class="aside">
      <div class="logo">{{ collapsed ? '沐' : '沐泽电力管理系统' }}</div>
      <el-menu :default-active="route.path" router :collapse="collapsed" background-color="#304156" text-color="#bfcbd9" active-text-color="#409EFF">
        <el-menu-item v-if="isFinance" index="/dashboard"><el-icon><DataAnalysis /></el-icon><span>仪表盘</span></el-menu-item>
        <el-menu-item v-if="isProject" index="/projects"><el-icon><Folder /></el-icon><span>项目管理</span></el-menu-item>
        <el-menu-item v-if="isAdmin || isProject" index="/partners"><el-icon><UserFilled /></el-icon><span>往来单位</span></el-menu-item>
        <el-menu-item v-if="isFinance || isProject" index="/invoices"><el-icon><Ticket /></el-icon><span>发票管理</span></el-menu-item>
        <el-menu-item v-if="isFinance" index="/finance"><el-icon><Coin /></el-icon><span>财务管理</span></el-menu-item>
        <el-menu-item v-if="isFinance" index="/taxes"><el-icon><Warning /></el-icon><span>税金管理</span></el-menu-item>
        <el-menu-item v-if="isFinance" index="/receipts"><el-icon><Document /></el-icon><span>电子收据</span></el-menu-item>
        <el-menu-item v-if="isLabour" index="/labour"><el-icon><UserFilled /></el-icon><span>人员工时</span></el-menu-item>
        <el-menu-item index="/archive"><el-icon><FolderOpened /></el-icon><span>电子档案</span></el-menu-item>
        <el-menu-item index="/reimbursement"><el-icon><Money /></el-icon><span>报销管理</span></el-menu-item>
        <el-menu-item v-if="isAdmin" index="/users"><el-icon><User /></el-icon><span>用户管理</span></el-menu-item>
        <el-menu-item v-if="isAdmin" index="/backup"><el-icon><Setting /></el-icon><span>系统备份</span></el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <el-icon style="cursor:pointer;font-size:20px" @click="collapsed=!collapsed"><Fold /></el-icon>
        <div class="header-right">
          <span class="user-info">{{ user?.display_name || '管理员' }}</span>
          <el-tag v-if="user?.role==='super_admin'" size="small" type="danger">超管</el-tag>
          <el-button text @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      <el-main class="main"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Fold, DataAnalysis, Folder, UserFilled, Ticket, Coin, Warning, Document, User, Money, Setting } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const collapsed = ref(false)
const user = computed(() => {
  try { return JSON.parse(localStorage.getItem('user')) } catch { return null }
})
const role = computed(() => user.value?.role || '')
const isAdmin = computed(() => role.value === 'super_admin' || role.value === 'company_admin')
const isFinance = computed(() => isAdmin.value || role.value === 'finance' || role.value === 'project_manager')
const isProject = computed(() => isAdmin.value || role.value === 'project_manager')
const isLabour = computed(() => isAdmin.value || role.value === 'project_manager' || role.value === 'attendance' || role.value === 'finance' || role.value === 'worker')
const isAttendance = computed(() => role.value === 'attendance')

function handleLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
}
</script>

<style scoped>
.aside { background-color: #304156; overflow: hidden; transition: width .3s; }
.logo { height: 60px; line-height: 60px; text-align: center; color: #fff; font-size: 18px; font-weight: bold; letter-spacing: 2px; background: rgba(0,0,0,.2); }
.header { display: flex; align-items: center; justify-content: space-between; background: #fff; border-bottom: 1px solid #e6e6e6; }
.header-right { display: flex; align-items: center; gap: 12px; }
.user-info { font-size: 14px; color: #303133; }
.main { background: #f0f2f5; min-height: calc(100vh - 60px); }
</style>
