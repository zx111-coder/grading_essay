<template>
  <div class="class-management">
    <!-- 创建班级区域 -->
    <div class="create-class-section">
      <h2 class="section-title">创建班级</h2>
      <div class="create-form">
        <el-input 
          v-model="newClassName" 
          placeholder="请输入班级名称"
          class="class-input"
          clearable
        />
        <el-button 
          type="primary" 
          @click="handleCreateClass"
          :loading="creating"
          class="create-btn"
        >
          立即创建
        </el-button>
      </div>
    </div>

    <!-- 班级列表区域 -->
    <div class="class-list-section">
      <div class="section-header">
        <h2 class="section-title">我的班级</h2>
        <span class="class-count">共 {{ classList.length }} 个班级</span>
      </div>
      
      <!-- 班级列表卡片 -->
      <div class="class-cards" v-loading="loading">
        <el-card 
          v-for="classItem in classList" 
          :key="classItem.id"
          class="class-card"
          :body-style="{ padding: '0px' }"
          shadow="hover"
        >
          <div class="class-card-header">
            <div class="header-left">
              <!-- 显示模式：显示班级名称和编辑图标 -->
              <div v-if="editingClass?.id !== classItem.id" class="class-name-wrapper">
                <div class="class-name">{{ classItem.className }}</div>
                <el-button 
                  type="primary" 
                  link 
                  size="small"
                  class="edit-btn"
                  @click="startEdit(classItem)"
                >
                  <el-icon><Edit /></el-icon>
                </el-button>
              </div>
              
              <!-- 编辑模式：显示输入框和确认按钮 -->
              <div v-else class="edit-mode">
                <el-input 
                  v-model="editingClass.className" 
                  size="small"
                  class="edit-input"
                  @keyup.enter="confirmEdit"
                  @keyup.esc="cancelEdit"
                  ref="editInputRef"
                />
                <div class="edit-actions">
                  <el-button 
                    type="success" 
                    link 
                    size="small"
                    @click="confirmEdit"
                  >
                    <el-icon><Check /></el-icon>
                  </el-button>
                  <el-button 
                    type="info" 
                    link 
                    size="small"
                    @click="cancelEdit"
                  >
                    <el-icon><Close /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </div>
          
          <div class="class-card-body">
            <div class="info-row">
              <span class="info-label">班级Code：</span>
              <span class="info-value id-value">{{ classItem.classCode }}</span>
              <el-button 
                type="primary" 
                link 
                size="small"
                @click="copyClassCode(classItem.classCode)"
              >
                复制
              </el-button>
            </div>
            
            <div class="info-row">
              <span class="info-label">学生人数：</span>
              <span class="info-value">{{ classItem.studentCount }} 人</span>
            </div>
            
            <div class="info-row">
              <span class="info-label">创建时间：</span>
              <span class="info-value">{{ formatDate(classItem.createTime) }}</span>
            </div>
          </div>
          
          <div class="class-card-footer">
            <el-button 
              type="primary" 
              link 
              @click="goToClassDetail(classItem.id)"
            >
              进入班级
            </el-button>
            <el-button 
              type="danger" 
              link 
              @click="handleDissolveClass(classItem)"
            >
              解散班级
            </el-button>
          </div>
        </el-card>
        
        <!-- 空状态展示 -->
        <el-empty 
          v-if="classList.length === 0" 
          description="暂无班级，快去创建第一个班级吧！"
          :image-size="200"
        />
      </div>
    </div>

    <!-- 解散确认对话框 -->
    <el-dialog
      v-model="dissolveDialogVisible"
      title="解散班级"
      width="400px"
      center
    >
      <div class="dissolve-warning">
        <el-icon class="warning-icon" size="24"><WarningFilled /></el-icon>
        <p>确定要解散班级 <strong>{{ currentClass?.className }}</strong> 吗？</p>
        <p class="warning-text">解散后，该班级的所有学生将无法加入，所有作文题目和提交记录将被删除。此操作不可恢复！</p>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dissolveDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="confirmDissolveClass" :loading="dissolving">
            确认解散
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { WarningFilled, Edit, Check, Close } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import classApi from '@/api/classes' // 假设有一个API模块处理班级相关的请求

const router = useRouter()

// 新班级名字
const newClassName = ref('')

// 班级列表数据
const classList = ref([])
const loading = ref(false)
const creating = ref(false)

// 解散对话框相关
const dissolveDialogVisible = ref(false)
const dissolving = ref(false)
const currentClass = ref(null)

// 编辑相关
const editingClass = ref(null)
const editInputRef = ref(null)

onMounted(() => {
  fetchClassList()
})

// 获取班级列表
const fetchClassList = async () => {
  loading.value = true
  try {
    const response=await classApi.getClasses() // 调用API创建班级，假设返回新班级的ID
    console.log("获取班级列表返回信息", response);
    if(response.status==200){
      loading.value = false
      classList.value = response.data || []
      return
    }
  } catch (error) {
    ElMessage.error('获取班级列表失败')
    loading.value = false
  }
}

// 创建班级
const handleCreateClass = async () => {
  if (!newClassName.value.trim()) {
    ElMessage.warning('请输入有效的班级名称')
    return
  }
  creating.value = true
  try {
    const response=await classApi.createClass(newClassName.value) // 调用API创建班级，假设返回新班级的ID
    console.log("创建班级返回信息", response);
    if(response.status==200){
      newClassName.value = '' // 清空输入框
      const newClass = {
        id: response.data.id, 
        classCode: response.data.classCode, 
        className: response.data.className,
        studentCount: response.data.studentCount,
        createTime: response.data.createTime
      }
      classList.value.unshift(newClass) // 将新班级添加到列表顶部
    }
    ElMessage.success('班级创建成功!')
  } catch (error) {
    ElMessage.error('创建失败，请重试')
  } finally {
    creating.value = false
  }
}

// 复制班级code
const copyClassCode = (classCode) => {
  navigator.clipboard.writeText(classCode).then(() => {
    ElMessage.success('班级code已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败，请手动复制')
  })
}

// 格式化日期
const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

// 进入班级详情
const goToClassDetail = (classId) => {
  router.push(`/classes/class/${classId}`)
}

// 处理解散班级
const handleDissolveClass = (classItem) => {
  currentClass.value = classItem
  dissolveDialogVisible.value = true
}

// 确认解散班级
const confirmDissolveClass = async () => {
  if (!currentClass.value) return
  
  dissolving.value = true
  try {
    await classApi.deleteClass(currentClass.value.id)
    // 从列表中移除
    const index = classList.value.findIndex(item => item.id === currentClass.value.id)
    if (index !== -1) {
      classList.value.splice(index, 1)
    }
    ElMessage.success(`班级 "${currentClass.value.className}" 已成功解散`)
    dissolveDialogVisible.value = false
    currentClass.value = null
  } catch (error) {
    ElMessage.error('解散失败，请重试')
  } finally {
    dissolving.value = false
  }
}

// 开始编辑班级名称
const startEdit = (classItem) => {
  // 保存当前编辑的班级信息
  editingClass.value = {
    id: classItem.id,
    className: classItem.className
  }
  
  // 在DOM更新后自动聚焦输入框
  nextTick(() => {
    if (editInputRef.value) {
      editInputRef.value.focus()
    }
  })
}

// 确认编辑
const confirmEdit = async () => {
  if (!editingClass.value) return
  
  // 验证班级名称
  if (!editingClass.value.className.trim()) {
    ElMessage.warning('班级名称不能为空')
    return
  }
  
  try {
    const response=await classApi.editClass(editingClass.value.id, editingClass.value.className) 
    console.log("修改班级名的返回信息", response);
    if(response.status==200){
      // 更新列表中的班级名称
      const index = classList.value.findIndex(item => item.id === editingClass.value.id)
      if (index !== -1) {
        classList.value[index].className = editingClass.value.className
        ElMessage.success('班级名称修改成功')
      }
      // 退出编辑模式
      editingClass.value = null
    }
  } catch (error) {
    ElMessage.error('修改失败，请重试')
  }
}

// 取消编辑
const cancelEdit = () => {
  editingClass.value = null
}
</script>

<style scoped>
.class-management {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

/* 创建班级区域 */
.create-class-section {
  background-color: #fff;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2f3d;
  margin: 0 0 20px 0;
  position: relative;
  padding-left: 12px;
}

.section-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 18px;
  background: linear-gradient(135deg, #409EFF 0%, #36d6b2 100%);
  border-radius: 2px;
}

.create-form {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.class-input {
  width: 300px;
}

.create-btn {
  min-width: 100px;
}

/* 班级列表区域 */
.class-list-section {
  background-color: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.class-count {
  color: #909399;
  font-size: 14px;
  background-color: #f4f4f5;
  padding: 4px 12px;
  border-radius: 30px;
}

.class-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}

.class-card {
  transition: all 0.3s ease;
  border: none;
  border-radius: 12px;
  overflow: hidden;
}

.class-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1) !important;
}

.class-card-header {
  padding: 16px 20px;
  background: linear-gradient(135deg, #409EFF 0%, #36d6b2 100%);
  color: white;
}

.header-left {
  display: flex;
  align-items: center;
  width: 100%;
}

.class-name-wrapper {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 8px;
}

.class-name {
  font-size: 18px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.edit-btn {
  color: white !important;
  opacity: 0.8;
  padding: 4px !important;
}

.edit-btn:hover {
  opacity: 1;
  background-color: rgba(255, 255, 255, 0.1) !important;
}

.edit-mode {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 8px;
}

.edit-input {
  flex: 1;
}

.edit-input :deep(.el-input__wrapper) {
  background-color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.edit-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.edit-actions .el-button {
  color: white !important;
  padding: 4px !important;
}

.edit-actions .el-button:hover {
  background-color: rgba(255, 255, 255, 0.1) !important;
}

.class-card-body {
  padding: 16px 20px;
}

.info-row {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
}

.info-label {
  color: #606266;
  width: 80px;
  flex-shrink: 0;
}

.info-value {
  color: #303133;
  font-weight: 500;
  flex: 1;
}

.id-value {
  font-family: monospace;
  font-size: 15px;
  color: #409EFF;
  letter-spacing: 0.5px;
}

.class-card-footer {
  padding: 12px 20px;
  border-top: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  background-color: #fafbfc;
}

.class-card-footer .el-button {
  font-size: 14px;
}

.class-card-footer .el-button:hover {
  background-color: transparent;
  opacity: 0.8;
}

/* 解散警告对话框 */
.dissolve-warning {
  text-align: center;
  padding: 20px 0;
}

.warning-icon {
  color: #f56c6c;
  margin-bottom: 16px;
}

.dissolve-warning p {
  margin: 8px 0;
  font-size: 16px;
}

.warning-text {
  color: #f56c6c;
  font-size: 14px !important;
  margin-top: 16px !important;
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .class-management {
    padding: 16px;
  }
  
  .create-form {
    flex-direction: column;
    align-items: stretch;
  }
  
  .class-input {
    width: 100%;
  }
  
  .create-btn {
    width: 100%;
  }
  
  .class-cards {
    grid-template-columns: 1fr;
  }
}

/* 空状态样式 */
:deep(.el-empty__description) {
  margin-top: 20px;
  color: #909399;
}
</style>