<template>
  <div>
    <!-- 统计卡片 -->
    <el-row :gutter="12" style="margin-bottom:16px">
      <el-col :span="6" v-for="c in cards" :key="c.label">
        <el-card shadow="hover" style="text-align:center;padding:4px">
          <div class="fv" :style="{color:c.color}">{{ c.value }}</div>
          <div class="fl">{{ c.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 按税种统计 -->
    <el-row :gutter="12" style="margin-bottom:16px">
      <el-col :span="6" v-for="s in summary.by_type" :key="s.tax_type">
        <el-card shadow="hover" style="text-align:center;padding:4px">
          <div style="font-size:16px;font-weight:bold;color:#409EFF">¥{{ (s.total/10000).toFixed(1) }}万</div>
          <div style="font-size:12px;color:#909399">{{ s.tax_type }}<el-tag size="small" style="margin-left:4px">{{ s.count }}</el-tag></div>
        </el-card>
      </el-col>
    </el-row>

    <div style="margin-bottom:12px;display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:18px;font-weight:bold">税金管理</span>
      <div style="display:flex;gap:8px">
        <el-input v-model="searchKey" placeholder="搜索单位名称..." clearable prefix-icon="Search" style="width:200px" />
        <el-select v-model="filterPeriod" clearable placeholder="周期" style="width:100px" @change="fetch">
          <el-option label="月度" value="月度" /><el-option label="季度" value="季度" /><el-option label="年度" value="年度" />
        </el-select>
        <el-select v-model="filterStatus" clearable placeholder="状态" style="width:100px" @change="fetch">
          <el-option label="已缴纳" :value="true" /><el-option label="未缴纳" :value="false" />
        </el-select>
        <el-button type="primary" @click="openNew">新增税金记录</el-button>
      </div>
    </div>

    <el-table :data="filteredList" stripe border size="small">
      <el-table-column label="单位名称" width="140" prop="unit_name" />
      <el-table-column label="税种" width="120"><template #default="{row}"><el-tag size="small" :type="row.tax_type==='企业所得税'?'danger':row.tax_type==='增值税'?'':'warning'">{{ row.tax_type }}</el-tag></template></el-table-column>
      <el-table-column label="所属期" width="90" prop="tax_period" />
      <el-table-column label="金额" width="130"><template #default="{row}">¥{{ (row.amount||0).toLocaleString() }}</template></el-table-column>
      <el-table-column label="周期" width="80"><template #default="{row}"><el-tag size="small" :type="row.period_type==='年度'?'danger':row.period_type==='季度'?'warning':'info'">{{ row.period_type }}</el-tag></template></el-table-column>
      <el-table-column label="缴纳期限" width="100" prop="due_date" />
      <el-table-column label="实缴日期" width="100" prop="paid_date" />
      <el-table-column label="状态" width="80">
        <template #default="{row}"><el-tag :type="row.is_paid?'success':'danger'" size="small">{{ row.is_paid?'已缴':'未缴' }}</el-tag></template>
      </el-table-column>
      <el-table-column label="凭证" width="55"><template #default="{row}"><el-button v-if="row.file_path" text size="small" @click="viewFile(row)">📎</el-button><span v-else>-</span></template></el-table-column>
      <el-table-column label="备注" min-width="120" prop="remark" />
      <el-table-column label="操作" width="110" fixed="right">
        <template #default="{row}">
          <el-button text type="primary" size="small" @click="editRow(row)">编</el-button>
          <el-popconfirm title="确定删除？" @confirm="delRow(row.id)"><template #reference><el-button text type="danger" size="small">删</el-button></template></el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="showNew" :title="editId?'编辑税金记录':'新增税金记录'" width="550px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="单位名称"><el-input v-model="form.unit_name" placeholder="甲公司/乙公司/丙公司" /></el-form-item>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="税种"><el-select v-model="form.tax_type" style="width:100%"><el-option label="增值税" value="增值税" /><el-option label="企业所得税" value="企业所得税" /><el-option label="附加税" value="附加税" /><el-option label="印花税" value="印花税" /><el-option label="个人所得税" value="个人所得税" /><el-option label="其他" value="其他" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="所属期"><el-date-picker v-model="form.tax_period" type="month" style="width:100%" value-format="YYYY-MM" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="金额"><el-input-number v-model="form.amount" :min="0" :step="10000" style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="周期"><el-select v-model="form.period_type" style="width:100%"><el-option label="月度（一般纳税人）" value="月度" /><el-option label="季度（小规模纳税人）" value="季度" /><el-option label="年度（企业所得税）" value="年度" /></el-select></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="缴纳期限"><el-date-picker v-model="form.due_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="实缴日期"><el-date-picker v-model="form.paid_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="缴纳状态"><el-switch v-model="form.is_paid" active-text="已缴纳" inactive-text="未缴纳" /></el-form-item>
        <el-form-item label="缴税凭证">
          <el-upload :action="uploadUrl" :headers="uploadHeaders" :on-success="upSuccess" :on-error="upError" :show-file-list="false">
            <el-button size="small" type="primary">上传凭证</el-button>
            <template #tip><span style="font-size:12px;color:#909399;margin-left:8px">{{ form.file_path ? '已上传' : '未上传' }}</span></template>
          </el-upload>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showNew=false">取消</el-button><el-button type="primary" @click="save">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import request from '@/api/request'

const list = ref([])
const searchKey = ref('')
const filterPeriod = ref('')
const filterStatus = ref('')
const showNew = ref(false)
const editId = ref(null)
const summary = ref({ by_type: [], total_all: 0, total_paid: 0, total_unpaid: 0 })
const form = reactive({
  unit_name:'', tax_type:'增值税', tax_period:'', amount:0, period_type:'月度',
  due_date:'', paid_date:'', is_paid:false, file_path:'', remark:''
})

const token = computed(() => localStorage.getItem('token') || '')
const uploadUrl = '/api/v1/files/upload/0?filetype=tax'
const uploadHeaders = computed(() => ({ Authorization: `Bearer ${token.value}` }))
const cards = computed(() => {
  return [
    { label: '税金总额', value: `¥${(summary.value.total_all/10000).toFixed(1)}万`, color: '#409EFF' },
    { label: '已缴纳', value: `¥${(summary.value.total_paid/10000).toFixed(1)}万`, color: '#67C23A' },
    { label: '未缴纳', value: `¥${(summary.value.total_unpaid/10000).toFixed(1)}万`, color: '#F56C6C' },
    { label: '记录数', value: `${list.value.length}`, color: '#303133' },
  ]
})

const filteredList = computed(() => {
  let items = list.value
  if (searchKey.value) {
    const s = searchKey.value.toLowerCase()
    items = items.filter(i => i.unit_name?.toLowerCase().includes(s))
  }
  if (filterPeriod.value) {
    items = items.filter(i => i.period_type === filterPeriod.value)
  }
  if (filterStatus.value !== '' && filterStatus.value !== undefined && filterStatus.value !== null) {
    const v = filterStatus.value === true || filterStatus.value === 'true'
    items = items.filter(i => i.is_paid === v)
  }
  return items
})
async function fetch() {
  list.value = await request.get('/taxes')
  summary.value = await request.get('/taxes/summary')
}
function openNew() {
  editId.value = null
  Object.assign(form, { unit_name:'', tax_type:'增值税', tax_period:'', amount:0, period_type:'月度', due_date:'', paid_date:'', is_paid:false, file_path:'', remark:'' })
  showNew.value = true
}
function editRow(row) {
  editId.value = row.id
  Object.assign(form, {
    unit_name:row.unit_name||'', tax_type:row.tax_type, tax_period:row.tax_period, amount:row.amount, period_type:row.period_type||'月度',
    due_date:row.due_date||'', paid_date:row.paid_date||'', is_paid:row.is_paid, file_path:row.file_path||'', remark:row.remark||''
  })
  showNew.value = true
}
function upSuccess(r) { form.file_path = r.filepath; ElMessage.success('上传成功') }
function upError() { ElMessage.error('上传失败') }
async function save() {
  const payload = { ...form }
  if (editId.value) { await request.put(`/taxes/${editId.value}`, payload); ElMessage.success('编辑成功') }
  else { await request.post('/taxes', payload); ElMessage.success('新增成功') }
  showNew.value = false; editId.value = null; fetch()
}
async function delRow(id) { await request.delete(`/taxes/${id}`); ElMessage.success('已删除'); fetch() }
function viewFile(row) { if (row.file_path) window.open(`/api/v1/files/download/by-path?path=${row.file_path}`, '_blank') }
onMounted(fetch)
</script>

<style scoped>
.fv { font-size:20px;font-weight:bold; }
.fl { font-size:12px;color:#909399;margin-top:4px; }
</style>
