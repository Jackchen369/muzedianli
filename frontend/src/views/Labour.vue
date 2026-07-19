<template>
  <div>
    <div style="margin-bottom:12px;display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:18px;font-weight:bold">人员工时管理</span>
    </div>
    <el-tabs v-model="tab" @tab-change="fetch">
      <!-- 人员档案 -->
      <el-tab-pane label="人员档案" name="staff">
        <div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap">
          <el-input v-model="staffSearch" placeholder="搜索姓名/身份证..." clearable prefix-icon="Search" style="width:240px" />
          <el-button v-if="isAdmin" type="primary" @click="openStaff">新增人员</el-button>
          <el-button @click="exportStaff">导出Excel</el-button>
        </div>
        <el-table :data="paginatedStaff" stripe border size="small" style="width:100%">
          <el-table-column prop="name" label="姓名" min-width="80" />
          <el-table-column prop="id_card" label="身份证号" min-width="150" />
          <el-table-column prop="phone" label="电话" min-width="110" />
          <el-table-column prop="work_type" label="工种" min-width="70" />
          <el-table-column label="开户行" min-width="90"><template #default="{row}">{{ row.bank_name || '-' }}</template></el-table-column>
          <el-table-column label="银行账号" min-width="130" prop="bank_account" />
          <el-table-column label="状态" min-width="60"><template #default="{row}"><el-tag :type="row.is_active?'success':'info'" size="small">{{ row.is_active?'正常':'停用' }}</el-tag></template></el-table-column>
          <el-table-column label="操作" min-width="120">
            <template #default="{row}">
              <el-button text type="primary" size="small" @click="editStaff(row)">编辑</el-button>
              <el-popconfirm v-if="isAdmin" title="确定删除？" @confirm="delStaff(row.id)"><template #reference><el-button text type="danger" size="small">删除</el-button></template></el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
        <div style="margin-top:10px;display:flex;justify-content:flex-end">
          <el-pagination v-model:page-size="staffPageSize" :page-sizes="[10,20,50,100]" :total="staffTotal" v-model:current-page="staffPage" layout="total,sizes,prev,pager,next,jumper" background small />
        </div>
      </el-tab-pane>

      <!-- 工时记录 -->
      <el-tab-pane label="工时记录" name="hours">
        <div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap">
          <el-select v-model="hourFilterStaff" clearable placeholder="人员" style="width:140px" @change="fetch">
            <el-option v-for="s in staffList" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
          <el-button v-if="isAdmin || isAttendance" type="primary" @click="openHour">添加工时</el-button>
          <el-button @click="exportHours">导出Excel</el-button>
        </div>
        <el-table :data="paginatedHours" stripe border size="small">
          <el-table-column label="人员" min-width="70"><template #default="{row}">{{ staffMap[row.staff_id] }}</template></el-table-column>
          <el-table-column prop="work_date" label="日期" min-width="90" />
          <el-table-column prop="position_title" label="临时职务" min-width="80" />
          <el-table-column prop="attendance_subsidy" label="出工补助" min-width="80"><template #default="{row}">¥{{ row.attendance_subsidy||0 }}</template></el-table-column>
          <el-table-column prop="meal_allowance" label="饭补" min-width="60"><template #default="{row}">¥{{ row.meal_allowance||0 }}</template></el-table-column>
          <el-table-column prop="heat_subsidy" label="高温补贴" min-width="70"><template #default="{row}">¥{{ row.heat_subsidy||0 }}</template></el-table-column>
          <el-table-column prop="weather_subsidy" label="天气补贴" min-width="70"><template #default="{row}">¥{{ row.weather_subsidy||0 }}</template></el-table-column>
          <el-table-column prop="daily_total" label="日合计" min-width="70"><template #default="{row}">¥{{ row.daily_total||0 }}</template></el-table-column>
          <el-table-column label="审核" min-width="55">
            <template #default="{row}">
              <el-button v-if="isAdmin" text :type="row.is_approved?'success':'warning'" size="small" @click="toggleApprove(row)">
                {{ row.is_approved?'通过':'待审' }}
              </el-button>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="100">
            <template #default="{row}">
              <el-button v-if="isAdmin || isAttendance" text type="primary" size="small" @click="editHour(row)">编辑</el-button>
              <el-popconfirm v-if="isAdmin || (isAttendance && !row.is_approved)" title="确定删除？" @confirm="delHour(row.id)"><template #reference><el-button text type="danger" size="small">删</el-button></template></el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
        <div style="margin-top:10px;display:flex;justify-content:flex-end">
          <el-pagination v-model:page-size="hourPageSize" :page-sizes="[10,20,50,100]" :total="hourTotal" v-model:current-page="hourPage" layout="total,sizes,prev,pager,next,jumper" background small />
        </div>
      </el-tab-pane>

      <!-- 薪酬管理 -->
      <el-tab-pane label="薪酬管理" name="salary">
        <div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap">
          <el-select v-model="salaryFilterStaff" clearable placeholder="人员" style="width:140px" @change="fetch">
            <el-option v-for="s in staffList" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
          <el-button v-if="isAdmin" type="primary" @click="openSalary">生成薪酬</el-button>
          <el-button @click="exportSalary">导出Excel</el-button>
        </div>
        <el-table :data="paginatedSalary" stripe border size="small">
          <el-table-column label="人员" min-width="70"><template #default="{row}">{{ staffMap[row.staff_id] }}</template></el-table-column>
          <el-table-column prop="salary_month" label="月份" min-width="70" />
          <el-table-column prop="base_amount" label="基础工资" min-width="80"><template #default="{row}">¥{{ (row.base_amount||0).toLocaleString() }}</template></el-table-column>
          <el-table-column prop="hourly_wage" label="工时工资" min-width="80"><template #default="{row}">¥{{ (row.hourly_wage||0).toLocaleString() }}</template></el-table-column>
          <el-table-column prop="insurance_fund" label="五险一金" min-width="70"><template #default="{row}">¥{{ (row.insurance_fund||0).toLocaleString() }}</template></el-table-column>
          <el-table-column prop="project_bonus" label="项目提成" min-width="70"><template #default="{row}">¥{{ (row.project_bonus||0).toLocaleString() }}</template></el-table-column>
          <el-table-column prop="net_amount" label="实发" min-width="80"><template #default="{row}"><span style="font-weight:bold;color:#E6A23C">¥{{ (row.net_amount||0).toLocaleString() }}</span></template></el-table-column>
          <el-table-column label="状态" min-width="60"><template #default="{row}"><el-tag :type="row.is_paid?'success':'info'" size="small">{{ row.is_paid?'已发':'未发' }}</el-tag></template></el-table-column>
          <el-table-column label="发放日期" min-width="85"><template #default="{row}">{{ row.paid_at ? row.paid_at.slice(0,10) : '-' }}</template></el-table-column>
          <el-table-column label="操作" min-width="110">
            <template #default="{row}">
              <el-button v-if="isAdmin" text type="primary" size="small" @click="editSalary(row)">编辑</el-button>
              <el-popconfirm v-if="isAdmin" title="确定删除？" @confirm="delSalary(row.id)"><template #reference><el-button text type="danger" size="small">删除</el-button></template></el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
        <div style="margin-top:10px;display:flex;justify-content:flex-end">
          <el-pagination v-model:page-size="salaryPageSize" :page-sizes="[10,20,50,100]" :total="salaryTotal" v-model:current-page="salaryPage" layout="total,sizes,prev,pager,next,jumper" background small />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 人员对话框 -->
    <el-dialog v-model="showStaff" :title="staffEditId?'编辑人员':'新增人员'" width="580px">
      <el-form :model="staffForm" label-width="90px">
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="姓名"><el-input v-model="staffForm.name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="工种"><el-input v-model="staffForm.work_type" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="身份证号"><el-input v-model="staffForm.id_card" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="电话"><el-input v-model="staffForm.phone" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="状态"><el-switch v-model="staffForm.is_active" active-text="在职" inactive-text="离职" /></el-form-item>
        <el-divider content-position="left">银行信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="开户行"><el-input v-model="staffForm.bank_name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="银行账号"><el-input v-model="staffForm.bank_account" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer><el-button @click="showStaff=false">取消</el-button><el-button type="primary" @click="saveStaff">保存</el-button></template>
    </el-dialog>

    <!-- 工时对话框 -->
    <el-dialog v-model="showHour" :title="hourEditId?'编辑工时':'添加工时'" width="500px">
      <el-form :model="hourForm" label-width="90px">
        <el-form-item label="人员"><el-select v-model="hourForm.staff_id" filterable style="width:100%"><el-option v-for="s in staffList" :key="s.id" :label="s.name" :value="s.id" /></el-select></el-form-item>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="日期"><el-date-picker v-model="hourForm.work_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="临时职务"><el-input v-model="hourForm.position_title" placeholder="如: 水电工/小工" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="出工补助"><el-input-number v-model="hourForm.attendance_subsidy" :min="0" style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="饭补"><el-input-number v-model="hourForm.meal_allowance" :min="0" style="width:100%" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="高温补贴"><el-input-number v-model="hourForm.heat_subsidy" :min="0" style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="天气补贴"><el-input-number v-model="hourForm.weather_subsidy" :min="0" style="width:100%" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="工作内容"><el-input v-model="hourForm.content" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showHour=false">取消</el-button><el-button type="primary" @click="saveHour">保存</el-button></template>
    </el-dialog>

    <!-- 薪酬对话框 -->
    <el-dialog v-model="showSalary" :title="salaryEditId?'编辑薪酬':'生成薪酬'" width="580px">
      <el-form :model="salaryForm" label-width="95px">
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="人员"><el-select v-model="salaryForm.staff_id" filterable style="width:100%"><el-option v-for="s in staffList" :key="s.id" :label="s.name" :value="s.id" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="月份"><el-date-picker v-model="salaryForm.salary_month" type="month" style="width:100%" value-format="YYYY-MM" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="基础工资"><el-input-number v-model="salaryForm.base_amount" :min="0" style="width:100%" @change="calcSalary" /></el-form-item></el-col>
          <el-col :span="12">
            <el-form-item label="工时工资">
              <div style="display:flex;gap:4px;width:100%">
                <el-input-number v-model="salaryForm.hourly_wage" :min="0" style="flex:1" @change="calcSalary" />
                <el-button type="primary" :disabled="!salaryForm.staff_id||!salaryForm.salary_month" @click="fetchHourlyWage" style="white-space:nowrap">提取</el-button>
              </div>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="五险一金"><el-input-number v-model="salaryForm.insurance_fund" :min="0" style="width:100%" @change="calcSalary" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="项目提成"><el-input-number v-model="salaryForm.project_bonus" :min="0" style="width:100%" @change="calcSalary" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="实发"><el-input :model-value="salaryNet" disabled style="width:100%;font-weight:bold;font-size:18px;color:#E6A23C" /></el-form-item>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="发放状态"><el-switch v-model="salaryForm.is_paid" active-text="已发放" inactive-text="未发放" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="发放日期"><el-date-picker v-model="salaryForm.paid_at" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="备注"><el-input v-model="salaryForm.remark" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showSalary=false">取消</el-button><el-button type="primary" @click="saveSalary">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import request from '@/api/request'

const tab = ref('staff')
const staffList = ref([])
const hourList = ref([])
const salaryList = ref([])
const projects = ref([])
const staffMap = ref({})
const projMap = ref({})
const staffSearch = ref('')
const hourFilterStaff = ref('')
const salaryFilterStaff = ref('')

// Pagination
const staffPage = ref(1); const staffPageSize = ref(10)
const hourPage = ref(1); const hourPageSize = ref(10)
const salaryPage = ref(1); const salaryPageSize = ref(10)

const staffTotal = computed(() => filteredStaff.value.length)
const hourTotal = computed(() => hourList.value.length)
const salaryTotal = computed(() => filteredSalary.value.length)

const paginatedStaff = computed(() => {
  const s = (staffPage.value - 1) * staffPageSize.value
  return filteredStaff.value.slice(s, s + staffPageSize.value)
})
const paginatedHours = computed(() => {
  const s = (hourPage.value - 1) * hourPageSize.value
  return hourList.value.slice(s, s + hourPageSize.value)
})
const paginatedSalary = computed(() => {
  const s = (salaryPage.value - 1) * salaryPageSize.value
  return filteredSalary.value.slice(s, s + salaryPageSize.value)
})

const filteredStaff = computed(() => {
  if (!staffSearch.value) return staffList.value
  const s = staffSearch.value.toLowerCase()
  return staffList.value.filter(i =>
    i.name?.toLowerCase().includes(s) || i.id_card?.includes(s)
  )
})

// Staff dialog
const showStaff = ref(false); const staffEditId = ref(null)
const staffForm = reactive({ name:'', id_card:'', phone:'', bank_card:'', bank_name:'', bank_account:'', work_type:'', is_active:true })

// Hour dialog
const showHour = ref(false); const hourEditId = ref(null)
const hourForm = reactive({ staff_id:null, work_date:'', position_title:'', attendance_subsidy:0, meal_allowance:0, heat_subsidy:0, weather_subsidy:0, content:'' })

// Salary dialog
const showSalary = ref(false); const salaryEditId = ref(null)
const salaryForm = reactive({ staff_id:null, project_id:null, salary_month:'', base_amount:0, hourly_wage:0, insurance_fund:0, project_bonus:0, is_paid:false, paid_at:'', remark:'' })

const salaryNet = computed(() => {
  const net = (salaryForm.base_amount||0) + (salaryForm.hourly_wage||0) - (salaryForm.insurance_fund||0) + (salaryForm.project_bonus||0)
  return `¥${net.toLocaleString()}`
})

const currentUser = computed(() => {
  try { return JSON.parse(localStorage.getItem('user')) } catch { return null }
})
const isAdmin = computed(() => currentUser.value?.role === 'super_admin' || currentUser.value?.role === 'company_admin')
const isAttendance = computed(() => currentUser.value?.role === 'attendance')

function calcSalary() {} // triggers computed refresh

async function fetch() {
  [staffList.value, projects.value] = await Promise.all([
    request.get('/labour/staff'), request.get('/projects').then(r => r.items || r || []).catch(() => [])
  ])
  staffList.value.forEach(s => staffMap.value[s.id] = s.name)
  projects.value.forEach(p => projMap.value[p.id] = p.name)

  if (tab.value === 'hours') {
    let url = '/labour/work-hours'
    const params = []
    if (hourFilterStaff.value) params.push(`staff_id=${hourFilterStaff.value}`)
    if (params.length) url += '?' + params.join('&')
    hourList.value = await request.get(url)
    hourPage.value = 1
  }
  if (tab.value === 'salary') {
    salaryList.value = await request.get('/labour/salary')
    salaryPage.value = 1
  }
  staffPage.value = 1
}

const filteredSalary = computed(() => {
  if (!salaryFilterStaff.value) return salaryList.value
  return salaryList.value.filter(i => i.staff_id === salaryFilterStaff.value)
})

// Staff CRUD
function openStaff() { staffEditId.value = null; Object.assign(staffForm, { name:'', id_card:'', phone:'', bank_card:'', bank_name:'', bank_account:'', work_type:'', is_active:true }); showStaff.value = true }
function editStaff(row) { staffEditId.value = row.id; Object.assign(staffForm, row); showStaff.value = true }
async function saveStaff() {
  if (staffEditId.value) await request.put(`/labour/staff/${staffEditId.value}`, staffForm)
  else await request.post('/labour/staff', staffForm)
  ElMessage.success('保存成功'); showStaff.value = false; fetch()
}
async function delStaff(id) { await request.delete(`/labour/staff/${id}`); ElMessage.success('已删除'); fetch() }

// Hour CRUD
function openHour() { hourEditId.value = null; Object.assign(hourForm, { staff_id:null, work_date:'', position_title:'', attendance_subsidy:0, meal_allowance:0, heat_subsidy:0, weather_subsidy:0, content:'' }); showHour.value = true }
function editHour(row) { hourEditId.value = row.id; Object.assign(hourForm, row); showHour.value = true }
async function saveHour() {
  if (!hourForm.staff_id) return ElMessage.warning('请选择人员')
  if (!hourForm.work_date) return ElMessage.warning('请选择日期')
  if (hourEditId.value) await request.put(`/labour/work-hours/${hourEditId.value}`, hourForm)
  else await request.post('/labour/work-hours', hourForm)
  ElMessage.success('保存成功'); showHour.value = false; fetch()
}
async function delHour(id) { await request.delete(`/labour/work-hours/${id}`); ElMessage.success('已删除'); fetch() }
async function toggleApprove(row) {
  await request.put(`/labour/work-hours/${row.id}/approve`)
  ElMessage.success(row.is_approved ? '已取消审核' : '已审核通过')
  fetch()
}

// Salary CRUD
function openSalary() { salaryEditId.value = null; Object.assign(salaryForm, { staff_id:null, project_id:null, salary_month:'', base_amount:0, hourly_wage:0, insurance_fund:0, project_bonus:0, is_paid:false, paid_at:'', remark:'' }); showSalary.value = true }
function editSalary(row) { salaryEditId.value = row.id; Object.assign(salaryForm, row); showSalary.value = true }
async function fetchHourlyWage() {
  try {
    const res = await request.get('/labour/hourly-wage', { params: { staff_id: salaryForm.staff_id, month: salaryForm.salary_month } })
    salaryForm.hourly_wage = parseFloat(res.total) || 0
    ElMessage.success(`已提取工时工资: ¥${(parseFloat(res.total)||0).toLocaleString()}（${res.work_days}天 × ¥${parseFloat(res.daily_wage)||0}）`)
  } catch { ElMessage.error('提取失败，请检查该人员当月是否有工时记录') }
}
async function saveSalary() {
  const payload = { ...salaryForm, net_amount: (salaryForm.base_amount||0) + (salaryForm.hourly_wage||0) - (salaryForm.insurance_fund||0) + (salaryForm.project_bonus||0) }
  if (salaryEditId.value) await request.put(`/labour/salary/${salaryEditId.value}`, payload)
  else await request.post('/labour/salary', payload)
  ElMessage.success('保存成功'); showSalary.value = false; fetch()
}
async function delSalary(id) { await request.delete(`/labour/salary/${id}`); ElMessage.success('已删除'); fetch() }

// Excel Export
async function downloadExcel(url, filename) {
  const res = await request.get(url, { responseType: 'blob' })
  const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = filename
  a.click(); URL.revokeObjectURL(a.href)
  ElMessage.success('导出成功')
}
async function exportStaff() { await downloadExcel('/labour/export/staff', `人员档案_${new Date().toISOString().slice(0,10)}.xlsx`) }
async function exportHours() { await downloadExcel('/labour/export/work-hours', `工时记录_${new Date().toISOString().slice(0,10)}.xlsx`) }
async function exportSalary() { await downloadExcel('/labour/export/salary', `薪酬管理_${new Date().toISOString().slice(0,10)}.xlsx`) }

onMounted(fetch)
</script>
