<template>
  <div class="class-detail">
    <!-- 顶部导航和信息（保持不变） -->
    <div class="detail-header">
      <div class="header-left">
        <el-button 
          type="primary" 
          link 
          @click="router.back()"
          class="back-btn"
          v-show="userRole==='teacher'"
        >
          <el-icon><ArrowLeft /></el-icon>返回
        </el-button>
        <div class="class-info">
          <div class="class-name-wrapper">
            <h1 class="class-name">{{ classDetail.className }}</h1>
          </div>
          <div class="class-meta">
            <div class="meta-item">
              <el-icon class="meta-icon"><Key /></el-icon>
              <span class="meta-label">邀请码：</span>
              <span class="meta-value class-code">{{ classDetail.classCode }}</span>
              <el-button 
                type="primary" 
                link 
                size="small"
                @click="copyClassCode(classDetail.classCode)"
                class="copy-btn"
              >
                复制
              </el-button>
            </div>
            <div class="meta-item clickable" @click="showStudentList" style="cursor: pointer">
              <el-icon class="meta-icon"><User /></el-icon>
              <span class="meta-label">人员数量：</span>
              <span class="meta-value">{{ classDetail.studentCount + 1 }}人</span>
            </div>
            <div class="meta-item">
              <el-icon class="meta-icon"><Calendar /></el-icon>
              <span class="meta-label">创建时间：</span>
              <span class="meta-value">{{ formatDate(classDetail.createTime) }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 老师特有的操作按钮 -->
      <div v-if="userRole === 'teacher'" class="header-right">
        <el-button 
          type="primary" 
          @click="showCreateTaskDialog = true"
          :icon="Plus"
          class="publish-btn"
        >
          发布新题目
        </el-button>
      </div>
    </div>

    <!-- 简化的作文题目列表区域 -->
    <div class="tasks-section">
      <div class="section-header">
        <h2 class="section-title">📝 作文题目列表</h2>
        <span class="task-count">共 {{ taskList.length }} 个题目</span>
      </div>

      <div class="task-list" v-loading="loading">
        <!-- 题目卡片 - 简化版 -->
        <el-card 
          v-for="task in taskList" 
          :key="task.id"
          class="task-card"
          shadow="hover"
        >
          <div class="task-content">
            <!-- 作文要求 -->
            <div class="task-requirement">
              {{ task.requirement || '暂无题目要求' }}
            </div>
            
            <!-- 基本信息行 -->
            <div class="task-info">
              <div class="info-item">
                <el-icon><Calendar /></el-icon>
                <span>{{ formatDate(task.created_at) }}</span>
              </div>
              
              <!-- 老师视角显示上传人数 -->
              <div v-if="userRole === 'teacher'" class="info-item">
                <el-icon><Document /></el-icon>
                <span>已上传：{{ task.submitted_count || 0 }}/{{ classDetail.studentCount }}人</span>
              </div>
              
              <!-- 学生视角显示提交状态 -->
              <div v-else class="info-item">
                <el-icon :color="task.user_submitted ? '#67c23a' : '#df3c2e'">
                  <Check v-if="task.user_submitted" />
                  <Warning v-else />
                </el-icon>
                <span :style="{ color: task.user_submitted ? '#67c23a' : '#df3c2e' }">
                  {{ task.user_submitted ? '已提交' : '未提交' }}
                </span>
              </div>
            </div>
          </div>
          
          <!-- 操作按钮 -->
          <div class="task-actions">
            <el-button 
              type="primary" 
              size="small"
              @click="goToTaskDetail(task)"
            >
              {{ userRole === 'teacher' ? '查看详情' : (task.user_submitted ? (task.task_finish ? '查看作文' : '等待批改') : '立即上传') }}
            </el-button>
            <!-- 老师：直接显示删除按钮 -->
            <el-button 
              v-if="userRole === 'teacher'" 
              type="danger" 
              size="small"
              @click="handleDeleteConfirm(task.id)"
            >
              删除
            </el-button>
          </div>
        </el-card>
        
        <!-- 空状态 -->
        <el-empty 
          v-if="taskList.length === 0" 
          :description="userRole === 'teacher' ? '暂无作文题目，点击右上角发布' : '老师还没有发布作文题目'"
        >
          <el-button v-if="userRole === 'teacher'" type="primary" @click="showCreateTaskDialog = true">
            发布第一个题目
          </el-button>
        </el-empty>
      </div>
    </div>

    <!-- 发布新题目对话框（保持不变） -->
    <el-dialog
      v-model="showCreateTaskDialog"
      title="发布新作文题目"
      width="600px"
      class="task-dialog"
    >
      <el-form 
        :model="taskForm" 
        :rules="taskRules"
        ref="taskFormRef"
        label-width="80px"
        class="task-form"
      >
        <el-form-item label="题目要求" prop="requirement">
          <el-input 
            v-model="taskForm.requirement" 
            type="textarea"
            :rows="6"
            placeholder="请输入作文要求，如：字数要求、写作方向、评分标准等"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateTaskDialog = false" :icon="Close">取消</el-button>
          <el-button type="primary" @click="submitTask" :loading="submitting" :icon="Check">
            确认发布
          </el-button>
        </span>
      </template>
    </el-dialog>
    <!-- 学生列表对话框 -->
    <el-dialog
      v-model="studentDialogVisible"
      title="班级人员列表"
      width="400px"
      class="student-dialog"
      :close-on-click-modal="false"
    >
      <div class="student-list" v-loading="studentLoading">
        <div 
          v-for="student in studentList" 
          :key="student.id"
          class="student-item"
        >
          <el-avatar 
            :size="40" 
            :src="defaultAvatar"
            class="student-avatar"
          />
          <span class="student-name">{{ student.name }}</span>
          <span class="role" v-if="student.role=='teacher'">老师</span>
        </div>
        
        <!-- 空状态 -->
        <el-empty 
          v-if="studentList.length === 0" 
          description="暂无学生"
          :image-size="80"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  ArrowLeft, Plus, Calendar, Document, 
  Check, Warning, ArrowDown, Key, User,
  Edit, Delete, Close
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import useUserStore from '@/stores/user.js'
import classApi from '@/api/classes'
import taskApi from '@/api/tasks'
import useCommentStore from '@/stores/dashboard.js'
const commentStore = useCommentStore()
const isAnalyzing = computed(() => commentStore.isAnalyzing)
// 班级详情缓存 key
const CLASS_DETAIL_STORAGE_KEY = 'class_detail_info'
const props = defineProps({
  classId: {
    type: [Number],
    required: false  // 改为非必需，因为可能从路由来
  }
})
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const classId = computed(() => props.classId || route.params.classId) 

// 用户角色
const userRole = computed(() => userStore.role)

// 带过期时间缓存（3分钟）
const setSessionWithExpire = (key, data, expireMinutes = 3) => {
  const obj = {
    data: data,
    time: Date.now(),
    expire: expireMinutes * 60 * 1000
  }
  sessionStorage.setItem(key, JSON.stringify(obj))
}

// 读取并自动判断过期
const getSessionWithExpire = (key) => {
  const item = sessionStorage.getItem(key)
  if (!item) return null
  try {
    const obj = JSON.parse(item)
    if (Date.now() - obj.time > obj.expire) {
      sessionStorage.removeItem(key)
      return null
    }
    return obj.data
  } catch (e) {
    return null
  }
}

// 班级详情数据
const classDetail = reactive({
  className: '',
  classCode: '',
  studentCount: 0,
  teacherName: '',
  createTime: '',
  isActive: true
})
const taskList = ref([])
const loading = ref(false)

// 发布题目对话框
const showCreateTaskDialog = ref(false)
const submitting = ref(false)
const taskFormRef = ref(null)
const taskForm = reactive({
  class_id: 0,
  requirement: ''
})

const taskRules = {
  requirement: [
    { required: true, message: '请输入题目要求', trigger: 'blur' }
  ]
}

// 复制班级码
const copyClassCode = (code) => {
  navigator.clipboard.writeText(code).then(() => {
    ElMessage.success('邀请码已复制到剪贴板')
  })
}

// 获取班级详情和题目列表
const fetchClassData = async () => {
  loading.value = true
  try {
    // if(isAnalyzing.value){
    //   const cacheData = getSessionWithExpire(CLASS_DETAIL_STORAGE_KEY)
    //   if (cacheData) {
    //     console.log('作文分析中，使用班级缓存')
    //     let tasks = cacheData.tasks || []
    //     tasks = tasks.map((task) => {
    //       const localSubmitted = localStorage.getItem(`submitted_task_${task.id}`)
    //       const finalSubmitted = localSubmitted ? true : task.user_submitted
    //       if (task.user_submitted) {
    //         localStorage.removeItem(`submitted_task_${task.id}`)
    //       }
    //       return { ...task, user_submitted: finalSubmitted }
    //     })
    //     classDetail.className = cacheData.className
    //     classDetail.classCode = cacheData.classCode
    //     classDetail.studentCount = cacheData.studentCount
    //     classDetail.teacherName = cacheData.teacherName
    //     classDetail.createTime = cacheData.createTime
    //     taskList.value = tasks || []
    //     taskForm.class_id = cacheData.id
    //     loading.value = false
    //     return
    //   }
    // }
    const response = await classApi.getClassDetail(classId.value)
    console.log('班级详情接口返回:', response);
    if(response.status==200){
      classDetail.className = response.data.className
      classDetail.classCode = response.data.classCode
      classDetail.studentCount = response.data.studentCount
      classDetail.teacherName = response.data.teacherName
      classDetail.createTime = response.data.createTime
      taskList.value = response.data.tasks || []
      taskForm.class_id = response.data.id
      // let tasks = response.data.tasks || [];
      // tasks = tasks.map((task) => {
      //   // 1. 先看本地有没有这个任务的提交标记
      //   const localSubmitted = localStorage.getItem(`submitted_task_${task.id}`);
        
      //   // 2. 如果本地有标记，强制设为已提交；否则用后端返回的状态
      //   const finalSubmitted = localSubmitted ? true : task.user_submitted;
        
      //   // 3. 如果后端已经返回true，说明数据已同步，删除本地标记
      //   if (task.user_submitted) {
      //     localStorage.removeItem(`submitted_task_${task.id}`);
      //   }
      //   // 4. 返回处理后的任务对象
      //   return {
      //     ...task,
      //     user_submitted: finalSubmitted,
      //   };
      // });
      // // 5. 赋值给taskList
      // taskList.value = tasks;
      // taskForm.class_id = response.data.id;
      // // 存入缓存 3 分钟
      // setSessionWithExpire(CLASS_DETAIL_STORAGE_KEY, {
      //   ...response.data,
      //   tasks: tasks
      // }, 3)
    }
  } catch (error) {
    ElMessage.error('获取班级信息失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 格式化日期
const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

// 发布题目
const submitTask = async () => {
  if (!taskFormRef.value) return
  await taskFormRef.value.validate()
  submitting.value = true
  try {
    const response = await taskApi.createTask({
      class_id: classId.value,
      requirement: taskForm.requirement.trim()
    })
    
    if(response.status==200 || response.status==201){
      ElMessage.success('题目发布成功')
      showCreateTaskDialog.value = false
      submitting.value = false
      taskForm.requirement=''
      await fetchClassData()
    }
  } catch (error) {
    ElMessage.error('发布失败')
  } finally {
    submitting.value = false
  }
}

// 进入题目详情
const goToTaskDetail = (task) => {
  if (userRole.value === 'teacher') {
    router.push(`/classes/class/${classId.value}/task/${task.id}`)
  } else {
    if (!task.user_submitted) {
      // 学生：跳转到根路径（analysis.vue），并传递任务信息
      router.push({
        path: '/myClass/upload', 
        query: {
          requirement: task.requirement,
          taskId: task.id,
          classId: classId.value
        }
      })
    } else {
      if(!task.task_finish){
        ElMessage.info('作文已提交，等待老师批改中...')
        return
      } else{
        router.push({
          path: '/myClass/dashboard',
          query: { historyId: task.essay_id }
        })
      }
    }
  }
}

// 显示删除确认框
const handleDeleteConfirm = async (id) => {
  try {
    // 弹出确认对话框
    await ElMessageBox.confirm(
      '确定要删除这个作文题目吗？删除后相关的学生作文也将被删除，此操作不可恢复！',
      '删除确认',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'warning', // 警告类型，显示黄色图标
        center: true, // 居中显示
        draggable: true // 可拖拽
      }
    )
    
    // 用户点击确认后执行删除操作
    await handleDeleteTask(id)
  } catch (error) {
    // 用户点击取消，提示操作已取消
    ElMessage.info('已取消删除操作')
  }
}

// 执行删除操作
const handleDeleteTask = async (id) => {
  try{
    await taskApi.deleteTask(id);
    ElMessage.success('题目删除成功')
    fetchClassData()
    
  }catch{
    ElMessage.error('题目删除失败')
  }
}

// 学生列表相关
const studentDialogVisible = ref(false)
const studentLoading = ref(false)
const studentList = ref([])
const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'

// 显示学生列表
const showStudentList = async () => {
  studentDialogVisible.value = true
  studentLoading.value = true
  
  try {
    // 调用获取班级学生列表的 API
    const response = await classApi.getClassStudents(classId.value)
    console.log('学生列表接口返回:', response)
    
    if (response.status === 200) {
      const { teacher, students } = response.data.data || {};
      const list=[]
      list.push({...teacher})
      list.push(...students)
      studentList.value=list
    } else {
      ElMessage.error('获取学生列表失败')
    }
  } catch (error) {
    console.error('获取学生列表失败:', error)
    ElMessage.error('获取学生列表失败')
  } finally {
    studentLoading.value = false
  }
}
import { watch } from 'vue'

watch(() => classId.value, (newId) => {
  if (newId) {
    fetchClassData()
  }
}, { immediate: true })
</script>

<style scoped>

/* 只保留必要的样式，删除多余的动画和效果 */
.class-detail {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

/* 顶部区域 */
.detail-header {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  display: flex;
  position: relative;      /* 为绝对定位提供参考 */
  justify-content: space-between;
  align-items: center;
}

.header-left {
  align-items: center;
}

.back-btn {
  font-size: 14px;
  padding: 4px 12px !important;
  border-radius: 20px;
  position: absolute;
  top: 15px;              /* 向上浮出 */
  left: 10px;              /* 与左边距对齐 */
  z-index: 10;
}

.class-info{
  margin-left: 80px
}

.class-name {
  font-size: 22px;
  font-weight: 600;
  color: #1f2f3d;
  margin: 0 0 12px 0;
}

.class-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px; /*子元素之间的间距*/
  font-size: 14px;
  color: #75787d;
}

.meta-icon {
  color: #409EFF;
}

.class-code {
  color: #606266;
  font-weight: 500;
  font-family: monospace;
}

.publish-btn {
  background: #409EFF;
  border: none;
}

/* 可点击的meta-item */
.meta-item.clickable {
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 4px 8px;
  border-radius: 6px;
  margin: -4px -8px;  /* 抵消padding，保持布局不变 */
}

.meta-item.clickable:hover {
  background-color: #f0f7ff;
  color: #409EFF;
}

.meta-item.clickable:hover .meta-icon {
  color: #409EFF;
  transform: scale(1.1);
}

.meta-item.clickable:hover .meta-value {
  color: #409EFF;
}

.meta-item.clickable .meta-icon {
  transition: transform 0.2s ease;
}

/* 题目列表区域 - 简化 */
.tasks-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2f3d;
  margin: 0;
}

.task-count {
  color: #909399;
  font-size: 14px;
  background: #f0f2f5;
  padding: 4px 12px;
  border-radius: 20px;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-card {
  border-radius: 8px;
  transition: all 0.3s;
}

.task-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1) !important;
}

.task-content {
  padding: 16px;
}

.task-requirement {
  font-size: 16px;
  color: #303133;
  line-height: 1.6;
  margin-bottom: 16px;
}

.task-info {
  display: flex;
  gap: 24px;
  color: #909399;
  font-size: 14px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.task-actions {
  padding: 12px 16px;
  border-top: 1px solid #f0f2f5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
/* 学生列表对话框 */
.student-dialog :deep(.el-dialog__body) {
  padding: 20px;
  max-height: 500px;
  overflow-y: auto;
}

.student-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.student-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 8px;
  background: #f8fafc;
  transition: all 0.2s;
}

.student-item:hover {
  background: #f0f2f5;
  transform: translateX(4px);
}

.student-avatar {
  flex-shrink: 0;
  border: 2px solid #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.student-name {
  font-size: 15px;
  font-weight: 500;
  color: #1f2f3d;
}

.role{
  margin-left:180px ;
  color:#94979b;
}


/* 响应式 */
@media screen and (max-width: 768px) {
  .detail-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .class-meta {
    flex-direction: column;
    gap: 8px;
  }
  
  .task-info {
    flex-direction: column;
    gap: 8px;
  }
  
  .task-actions {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .student-dialog {
    width: 90% !important;
  }
}
</style>