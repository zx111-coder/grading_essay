<template>
  <div class="my-classes-container">
    <!-- 情况1：未加入班级 - 显示加入班级界面 -->
    <div v-if="!hasClass" class="no-class-view">
      <!-- 加入班级卡片 -->
      <el-card class="join-card" shadow="hover">
        <div class="join-content">
          <div class="icon-wrapper">
            <el-icon class="join-icon"><School /></el-icon>
          </div>
          <h3 class="join-title">还没有加入班级？</h3>
          <p class="join-desc">输入邀请码，开启你的写作之旅</p>
          
          <div class="code-input-wrapper">
            <el-input
              v-model="classCode"
              placeholder="输入班级邀请码"
              show-word-limit
              class="code-input"
              @keyup.enter="handleJoinClass"
            >
              <template #prefix>
                <el-icon><Key /></el-icon>
              </template>
            </el-input>
            
            <el-button 
              type="primary" 
              @click="handleJoinClass" 
              :loading="joining"
              class="join-action-btn"
            >
              加入班级
            </el-button>
          </div>

          <p class="join-tip">
            <el-icon><InfoFilled /></el-icon>
            邀请码可以向老师索取
          </p>
        </div>
      </el-card>

      <!-- 加入后的好处 -->
      <div class="benefits-section">
        <h4 class="benefits-title">加入班级后你可以</h4>
        <div class="benefits-grid">
          <div class="benefit-item">
            <div class="benefit-icon" style="background: #ecf5ff; color: #409eff">
              <el-icon><DocumentAdd /></el-icon>
            </div>
            <span>接收作文题目</span>
          </div>
          <div class="benefit-item">
            <div class="benefit-icon" style="background: #f0f9eb; color: #67c23a">
              <el-icon><Edit /></el-icon>
            </div>
            <span>在线写作提交</span>
          </div>
          <div class="benefit-item">
            <div class="benefit-icon" style="background: #fdf6ec; color: #e6a23c">
              <el-icon><DataLine /></el-icon>
            </div>
            <span>查看评分反馈</span>
          </div>
          <div class="benefit-item">
            <div class="benefit-icon" style="background: #fef0f0; color: #f56c6c">
              <el-icon><Trophy /></el-icon>
            </div>
            <span>追踪进步轨迹</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 情况2：已加入班级 - 直接显示班级详情 -->
    <div v-else class="has-class-view">
      <ClassDetail 
        :classId="classId"
        @leave-class="handleLeaveClass"
      />
    </div>

    <!-- 加入成功提示 -->
    <el-dialog
      v-model="showSuccessDialog"
      title="🎉 加入成功"
      width="360px"
      class="success-dialog"
      :show-close="false"
      :close-on-click-modal="false"
    >
      <div class="success-content">
        <div class="success-icon-wrapper">
          <el-icon class="success-icon" color="#67c23a" size="48"><CircleCheck /></el-icon>
        </div>
        <p class="success-text">成功加入班级</p>
        <p class="success-class-name">"{{ newClassName }}"</p>
      </div>
      <template #footer>
        <el-button type="primary" @click="showSuccessDialog = false" class="success-btn" round>
          开始学习
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Plus, Key, School, InfoFilled, 
  CircleCheck, Edit, DataLine, Trophy, DocumentAdd
} from '@element-plus/icons-vue'
import ClassDetail from './class_details.vue'
import studentApi from '@/api/student' 

// 状态管理
const hasClass = ref(false) // 是否已加入班级
const classId = ref(0) // 班级信息
const classCode = ref('') // 输入的邀请码
const joining = ref(false) // 加入中状态

// 成功弹窗
const showSuccessDialog = ref(false)
const newClassName = ref('')

// 获取学生班级信息
const fetchMyClass = async () => {
  try {
    // 调用API获取学生已加入的班级
    const response = await studentApi.getMyClass()
    console.log("学生加入的班级信息响应：", response);
    if (response.data) {
      hasClass.value = true
      classId.value = response.data.class_id
    }
  } catch (error) {
    console.error('获取班级信息失败', error)
    // 如果没有班级，hasClass保持false
  }
}

// 加入班级
const handleJoinClass = async () => {
  if (!classCode.value) {
    ElMessage.warning('请输入班级邀请码')
    return
  }
  
  joining.value = true
  
  try {
    // 调用加入班级API
    const response = await studentApi.joinClass(classCode.value)
    console.log("加入班级响应：", response);
    if (response.status === 200 || response.statusText === "OK") {
      // 加入成功
      newClassName.value = response.data.class_name
      classId.value = response.data.class_id
      hasClass.value = true
      
      // 显示成功弹窗
      showSuccessDialog.value = true
      // 清空输入
      classCode.value = ''
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '加入失败，请检查邀请码')
  } finally {
    joining.value = false
  }
}

// 退出班级（从班级详情组件触发）
const handleLeaveClass = () => {
  hasClass.value = false
  classId.value = 0
  ElMessage.success('已退出班级')
}

onMounted(() => {
  fetchMyClass()
})
</script>

<style scoped>
.my-classes-container {
  background: #f5f7fa;
  min-height: 100%;
}

/* 未加入班级的样式 */
.no-class-view {
  max-width: 1000px;
  margin: 0 auto;
  padding: 40px 20px;
}

/* 加入班级卡片 */
.join-card {
  border-radius: 24px;
  border: none;
  transition: all 0.3s;
  margin-bottom: 60px;
  background: linear-gradient(135deg, #ffffff 0%, #fafcff 100%);
}

.join-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 30px rgba(0, 0, 0, 0.08) !important;
}

.join-content {
  padding: 48px 40px;
  text-align: center;
}

.icon-wrapper {
  width: 96px;
  height: 96px;
  background: linear-gradient(135deg, #ecf5ff 0%, #d9ecff 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
}

.join-icon {
  font-size: 48px;
  color: #409eff;
}

.join-title {
  font-size: 28px;
  font-weight: 600;
  color: #1f2f3d;
  margin: 0 0 12px 0;
  line-height: 1.3;
}

.join-desc {
  font-size: 16px;
  color: #6b7785;
  margin-bottom: 32px;
  line-height: 1.6;
}

.code-input-wrapper {
  max-width: 520px;
  margin: 0 auto 24px;
  display: flex;
  gap: 12px;
}

.code-input {
  flex: 1;
  width: 80%;
}

.code-input :deep(.el-input__wrapper) {
  border-radius: 40px;
  height: 52px;
  padding: 0 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
  background: #f8fafd;
  border: 1px solid #e6eaf0;
  transition: all 0.3s;
}

.code-input :deep(.el-input__wrapper:hover) {
  border-color: #409eff;
  background: white;
}

.code-input :deep(.el-input__wrapper.is-focus) {
  border-color: #409eff;
  background: white;
  box-shadow: 0 0 0 4px rgba(64, 158, 255, 0.1);
}

.code-input :deep(.el-input__inner) {
  text-align: left;
  font-size: 16px;
  letter-spacing: 2px;
  font-weight: 500;
  height: 50px;
}

.code-input :deep(.el-input__prefix) {
  color: #909399;
}

.join-action-btn {
  height: 52px;
  padding: 0 36px;
  border-radius: 40px;
  font-size: 16px;
  font-weight: 500;
  background: #409eff;
  border: none;
  transition: all 0.3s;
  min-width: 130px;
}

.join-action-btn:hover {
  background: #66b1ff;
  transform: scale(1.02);
}

.join-tip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #8a939f;
  font-size: 14px;
  background: #f8fafd;
  padding: 8px 20px;
  border-radius: 40px;
  margin: 0;
}

.join-tip .el-icon {
  font-size: 16px;
  color: #409eff;
}

/* 加入后的好处 */
.benefits-section {
  text-align: center;
}

.benefits-title {
  font-size: 20px;
  font-weight: 600;
  color: #1f2f3d;
  margin: 0 0 32px 0;
  position: relative;
  display: inline-block;
}

.benefits-title::after {
  content: '';
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 40px;
  height: 3px;
  background: linear-gradient(90deg, #409eff, #79bbff);
  border-radius: 2px;
}

.benefits-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.benefit-item {
  background: white;
  padding: 28px 20px;
  border-radius: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  border: 1px solid #edf2f7;
}

.benefit-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.06);
  border-color: transparent;
}

.benefit-icon {
  width: 64px;
  height: 64px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  transition: all 0.3s;
}

.benefit-item:hover .benefit-icon {
  transform: scale(1.1);
}

.benefit-item span {
  font-size: 15px;
  font-weight: 500;
  color: #2c3e50;
}

/* 成功弹窗 */
.success-dialog :deep(.el-dialog__header) {
  padding: 24px 24px 0;
  margin: 0;
}

.success-dialog :deep(.el-dialog__title) {
  font-size: 20px;
  font-weight: 600;
  color: #1f2f3d;
}

.success-dialog :deep(.el-dialog__body) {
  padding: 24px 24px 20px;
}

.success-content {
  text-align: center;
}

.success-icon-wrapper {
  width: 88px;
  height: 88px;
  background: #f0f9eb;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  animation: scaleIn 0.4s ease-out;
}

.success-icon {
  font-size: 48px;
}

.success-text {
  font-size: 18px;
  color: #1f2f3d;
  font-weight: 500;
  margin: 0 0 8px 0;
}

.success-class-name {
  font-size: 20px;
  color: #409eff;
  font-weight: 600;
  margin: 0;
  line-height: 1.4;
}

.success-dialog :deep(.el-dialog__footer) {
  padding: 0 24px 32px;
}

.success-btn {
  width: 100%;
  height: 48px;
  border-radius: 30px;
  font-size: 16px;
  font-weight: 500;
  background: #409eff;
  border: none;
  transition: all 0.3s;
}

.success-btn:hover {
  background: #66b1ff;
  transform: scale(1.02);
}

/* 动画 */
@keyframes scaleIn {
  from {
    transform: scale(0);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

/* 响应式 */
@media (max-width: 768px) {
  .no-class-view {
    padding: 20px;
  }
  
  .join-content {
    padding: 32px 20px;
  }
  
  .join-title {
    font-size: 24px;
  }
  
  .join-desc {
    font-size: 14px;
  }
  
  .code-input-wrapper {
    flex-direction: column;
  }
  
  .join-action-btn {
    width: 100%;
  }
  
  .benefits-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  
  .benefit-item {
    padding: 20px 16px;
  }
  
  .benefit-icon {
    width: 56px;
    height: 56px;
    font-size: 24px;
  }
}

@media (max-width: 480px) {
  .benefits-grid {
    grid-template-columns: 1fr;
  }
  
  .join-icon {
    width: 80px;
    height: 80px;
    font-size: 40px;
  }
  
  .join-title {
    font-size: 22px;
  }
}
</style>