<template>
  <div>
    <div style="margin-bottom:16px;display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:18px;font-weight:bold">工程计价</span>
      <div>
        <el-select v-model="filterProject" clearable placeholder="筛选项目" style="width:200px;margin-right:8px" @change="fetch">
          <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-button v-if="canWrite" type="primary" @click="openNew">新增计价</el-button>
        <el-button @click="exportExcel">导出Excel</el-button>
      </div>
    </div>

    <el-tabs v-model="tab" @tab-change="fetch">
      <el-tab-pane label="主体业务" name="主体业务">
        <el-card style="margin-bottom:12px">
          <div style="font-size:14px">主体业务汇总: <span style="font-size:20px;font-weight:bold;color:#E6A23C">¥{{ ((totalMain||0)/10000).toFixed(1) }}万</span></div>
        </el-card>
        <el-table :data="mainList" stripe border style="width:100%">
          <el-table-column label="项目" min-width="150" align="center"><template #default="{row}">{{ projMap[row.project_id] }}</template></el-table-column>
          <el-table-column prop="item_name" label="工程名称" min-width="200" align="center" />
          <el-table-column label="金额" min-width="120" align="center"><template #default="{row}">¥{{ (row.amount||0).toLocaleString() }}</template></el-table-column>
          <el-table-column label="日期" min-width="100" align="center"><template #default="{row}">{{ row.pricing_date || '-' }}</template></el-table-column>
          <el-table-column label="审核" min-width="80" align="center"><template #default="{row}"><el-tag :type="row.is_approved?'success':'warning'" size="small">{{ row.is_approved?'已审核':'待审核' }}</el-tag></template></el-table-column>
          <el-table-column prop="remark" label="备注" min-width="150" align="center" />
          <el-table-column label="操作" min-width="150" align="center">
            <template #default="{row}">
              <el-button v-if="isAdmin && !row.is_approved" text type="primary" size="small" @click="openEdit(row)">编辑</el-button>
              <el-button v-if="isAdmin" text :type="row.is_approved?'success':'warning'" size="small" @click="toggleApprove(row)">{{ row.is_approved?'取消审核':'审核' }}</el-button>
              <el-popconfirm v-if="isAdmin && !row.is_approved" title="确定删除？" @confirm="handleDelete(row.id)"><template #reference><el-button text type="danger" size="small">删除</el-button></template></el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination v-if="mainTotal>pageSize" v-model:current-page="mainPage" :page-size="pageSize" :total="mainTotal" layout="total, sizes, prev, pager, next, jumper" :page-sizes="[10,20,50,100]" style="margin-top:8px;justify-content:center" @current-change="fetch" @size-change="pageSize=$event;fetch()" />
      </el-tab-pane>

      <el-tab-pane label="带电作业" name="带电作业">
        <el-card style="margin-bottom:12px">
          <div style="font-size:14px">带电作业汇总: <span style="font-size:20px;font-weight:bold;color:#E6A23C">¥{{ ((totalLive||0)/10000).toFixed(1) }}万</span></div>
        </el-card>
        <el-table :data="liveList" stripe border style="width:100%">
          <el-table-column label="项目" min-width="150" align="center"><template #default="{row}">{{ projMap[row.project_id] }}</template></el-table-column>
          <el-table-column prop="item_name" label="工程名称" min-width="200" align="center" />
          <el-table-column label="金额" min-width="120" align="center"><template #default="{row}">¥{{ (row.amount||0).toLocaleString() }}</template></el-table-column>
          <el-table-column label="日期" min-width="100" align="center"><template #default="{row}">{{ row.pricing_date || '-' }}</template></el-table-column>
          <el-table-column label="审核" min-width="80" align="center"><template #default="{row}"><el-tag :type="row.is_approved?'success':'warning'" size="small">{{ row.is_approved?'已审核':'待审核' }}</el-tag></template></el-table-column>
          <el-table-column prop="remark" label="备注" min-width="150" align="center" />
          <el-table-column label="操作" min-width="150" align="center">
            <template #default="{row}">
              <el-button v-if="isAdmin && !row.is_approved" text type="primary" size="small" @click="openEdit(row)">编辑</el-button>
              <el-button v-if="isAdmin" text :type="row.is_approved?'success':'warning'" size="small" @click="toggleApprove(row)">{{ row.is_approved?'取消审核':'审核' }}</el-button>
              <el-popconfirm v-if="isAdmin && !row.is_approved" title="确定删除？" @confirm="handleDelete(row.id)"><template #reference><el-button text type="danger" size="small">删除</el-button></template></el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination v-if="liveTotal>pageSize" v-model:current-page="livePage" :page-size="pageSize" :total="liveTotal" layout="total, sizes, prev, pager, next, jumper" :page-sizes="[10,20,50,100]" style="margin-top:8px;justify-content:center" @current-change="fetch" @size-change="pageSize=$event;fetch()" />
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="showDialog" :title="isEdit?'编辑计价':'新增计价'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="所属板块"><el-tag :type="tab==='主体业务'?'primary':'success'">{{ tab }}</el-tag></el-form-item>
        <el-form-item label="关联项目"><el-select v-model="form.project_id" filterable style="width:100%"><el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" /></el-select></el-form-item>
        <el-form-item label="工程名称"><el-input v-model="form.item_name" /></el-form-item>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="金额"><el-input-number v-model="form.amount" :min="0" :step="10000" style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="日期"><el-date-picker v-model="form.pricing_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog=false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const tab = ref('主体业务')
const mainList = ref([])
const liveList = ref([])
const projects = ref([])
const projMap = ref({})
const filterProject = ref('')
const totalMain = ref(0)
const totalLive = ref(0)
const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const mainPage = ref(1)
const mainTotal = ref(0)
const livePage = ref(1)
const liveTotal = ref(0)
const pageSize = ref(10)

const currentUser = computed(() => { try { return JSON.parse(localStorage.getItem('user') || '{}') } catch { return {} } })
const role = computed(() => currentUser.value?.role || '')
const isAdmin = computed(() => role.value === 'super_admin' || role.value === 'company_admin')
const isAttendance = computed(() => role.value === 'attendance')
const canWrite = computed(() => isAdmin.value || isAttendance.value)

const form = reactive({ project_id: null, item_name: '', amount: 0, pricing_date: null, remark: '' })

async function fetch() {
  const pf = filterProject.value ? `&project_id=${filterProject.value}` : ''
  const cat = tab.value

  // Main business
  const mr = await request.get(`/pricing?page=${mainPage.value}&page_size=${pageSize.value}&category=主体业务${pf}`)
  mainList.value = mr.items || []
  mainTotal.value = mr.total || 0
  const mt = await request.get(`/pricing/total?category=主体业务${pf.replace('&','?') || ''}`)
  totalMain.value = mt.total || 0

  // Live working
  const lr = await request.get(`/pricing?page=${livePage.value}&page_size=${pageSize.value}&category=带电作业${pf}`)
  liveList.value = lr.items || []
  liveTotal.value = lr.total || 0
  const lt = await request.get(`/pricing/total?category=带电作业${pf.replace('&','?') || ''}`)
  totalLive.value = lt.total || 0

  const pr = await request.get('/projects?page=1&page_size=999')
  projects.value = pr.items || []
  projects.value.forEach(p => projMap.value[p.id] = p.name)
}

function openNew() {
  isEdit.value = false; editId.value = null
  Object.assign(form, { project_id: null, item_name: '', amount: 0, pricing_date: null, remark: '' })
  showDialog.value = true
}

function openEdit(row) {
  isEdit.value = true; editId.value = row.id
  Object.assign(form, { project_id: row.project_id, item_name: row.item_name, amount: row.amount || 0, pricing_date: row.pricing_date || null, remark: row.remark || '' })
  showDialog.value = true
}

async function toggleApprove(row) {
  await request.put(`/pricing/${row.id}/approve`)
  ElMessage.success(row.is_approved ? '已取消审核' : '审核通过')
  fetch()
}

async function save() {
  try {
    const payload = { ...form, category: tab.value }
    if (isEdit.value) {
      await request.put(`/pricing/${editId.value}`, payload)
      ElMessage.success('编辑成功')
    } else {
      await request.post('/pricing', payload)
      ElMessage.success('新增成功')
    }
    showDialog.value = false; fetch()
  } catch (e) { ElMessage.error(e?.detail || '保存失败') }
}

async function handleDelete(id) {
  await request.delete(`/pricing/${id}`)
  ElMessage.success('删除成功'); fetch()
}

async function downloadExcel(url, filename) {
  const res = await request.get(url, { responseType: 'blob' })
  const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = filename
  a.click(); URL.revokeObjectURL(a.href)
  ElMessage.success('导出成功')
}
async function exportExcel() {
  const cat = tab.value
  const pf = filterProject.value ? `&project_id=${filterProject.value}` : ''
  await downloadExcel(`/pricing/export?category=${cat}${pf}`, `工程计价_${cat}_${new Date().toISOString().slice(0,10)}.xlsx`)
}

onMounted(fetch)
</script>
