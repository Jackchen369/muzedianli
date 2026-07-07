<template>
  <div>
    <div style="margin-bottom:16px;display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:18px;font-weight:bold">往来单位</span>
      <div style="display:flex;gap:8px">
        <el-input v-model="searchKey" placeholder="搜索单位名称..." clearable prefix-icon="Search" style="width:220px" @input="fetchList" />
        <el-select v-model="typeFilter" clearable placeholder="筛选类型" style="width:130px" @change="fetchList">
          <el-option label="业主" value="业主" />
          <el-option label="供应商" value="供应商" />
          <el-option label="业主+供应商" value="业主+供应商" />
        </el-select>
        <el-button type="primary" @click="openNew">新增单位</el-button>
      </div>
    </div>
    <el-table :data="filteredList" stripe border style="width:100%">
      <el-table-column prop="name" label="单位名称" min-width="150" />
      <el-table-column label="类型" width="120">
        <template #default="{row}">
          <el-tag :type="row.partner_type==='业主'?'success':row.partner_type==='供应商'?'warning':'primary'" size="small">{{ row.partner_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="contact_person" label="联系人" width="100" />
      <el-table-column prop="contact_phone" label="电话" width="130" />
      <el-table-column prop="tax_id" label="税号" width="150" />
      <el-table-column prop="bank_code" label="联行号" width="150" />
      <el-table-column label="开户行/账号" min-width="180">
        <template #default="{row}">{{ row.bank_name ? row.bank_name+(row.bank_account?' / '+row.bank_account:''): '-' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="130" fixed="right">
        <template #default="{row}">
          <el-button text type="primary" size="small" @click="editRow(row)">编辑</el-button>
          <el-popconfirm title="确定删除该单位？" @confirm="handleDelete(row.id)">
            <template #reference><el-button text type="danger" size="small">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showDialog" :title="editId?'编辑单位':'新增单位'" width="600px">
      <el-form :model="form" label-width="90px">
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="单位名称" prop="name"><el-input v-model="form.name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="类型" prop="partner_type">
            <el-select v-model="form.partner_type" style="width:100%">
              <el-option label="业主" value="业主" /><el-option label="供应商" value="供应商" /><el-option label="业主+供应商" value="业主+供应商" />
            </el-select>
          </el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="联系人"><el-input v-model="form.contact_person" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="电话"><el-input v-model="form.contact_phone" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="开户行"><el-input v-model="form.bank_name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="银行账号"><el-input v-model="form.bank_account" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="联行号"><el-input v-model="form.bank_code" /></el-form-item>
        <el-form-item label="税号"><el-input v-model="form.tax_id" /></el-form-item>
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
import { Search } from '@element-plus/icons-vue'
import request from '@/api/request'

const list = ref([])
const searchKey = ref('')
const typeFilter = ref('')
const showDialog = ref(false)
const editId = ref(null)
const formRef = ref(null)
const form = reactive({
  name:'', partner_type:'业主', contact_person:'', contact_phone:'',
  address:'', bank_name:'', bank_account:'', bank_code:'', tax_id:''
})

const filteredList = computed(() => {
  let items = list.value
  if (searchKey.value) {
    const s = searchKey.value.toLowerCase()
    items = items.filter(i => i.name?.toLowerCase().includes(s))
  }
  if (typeFilter.value) {
    items = items.filter(i => i.partner_type === typeFilter.value)
  }
  return items
})

async function fetchList() { list.value = await request.get('/partners') }
function openNew() {
  editId.value = null
  Object.assign(form, { name:'', partner_type:'业主', contact_person:'', contact_phone:'', address:'', bank_name:'', bank_account:'', bank_code:'', tax_id:'' })
  showDialog.value = true
}
function editRow(row) {
  Object.assign(form, row)
  editId.value = row.id
  showDialog.value = true
}
async function save() {
  if (editId.value) await request.put(`/partners/${editId.value}`, form)
  else await request.post('/partners', form)
  ElMessage.success('保存成功')
  showDialog.value = false
  editId.value = null
  fetchList()
}
async function handleDelete(id) {
  await request.delete(`/partners/${id}`)
  ElMessage.success('删除成功')
  fetchList()
}
onMounted(fetchList)
</script>
