<template>
  <div class="app-container">
    <!-- 左侧菜单 - 只有登录后才显示 -->
    <div class="sidebar" v-if="userStore.isLoggedIn" :class="{ 'sidebar-collapsed': isCollapsed }">
      <div class="sidebar-header">
        <h2 v-if="!isCollapsed">作文批改系统</h2>
        <el-tooltip 
          :content="isCollapsed ? '打开菜单' : '关闭菜单'" 
          placement="right"
          trigger="hover"
        >
          <!-- 收缩按钮 -->
          <el-button 
            circle 
            size="small" 
            class="collapse-btn"
            @click="toggleSidebar"
          >
            <el-icon size="18"><Menu /></el-icon>
          </el-button>
        </el-tooltip>
      </div>
      
      <el-menu
        router
        v-model:default-active="activePath"
        class="menu"
        :collapse="isCollapsed"
        :collapse-transition="false"
      > 
        <el-menu-item class="li" index="/">
          <el-icon class="icon"><DocumentAdd /></el-icon>
          <template #title>上传作文</template>
        </el-menu-item>
        <el-menu-item 
          v-if="isTeacher" 
          class="li" 
          index="/classes"
        >
          <el-icon class="icon"><DocumentChecked /></el-icon>
          <template #title>班级管理</template>
        </el-menu-item>
        <el-menu-item 
          v-if="isStudent" 
          class="li" 
          index="/myClass"
        >
          <el-icon class="icon"><DocumentChecked /></el-icon>
          <template #title>我的班级</template>
        </el-menu-item>
        <el-menu-item class="li" index="/dashboard">
          <el-icon class="icon"><DocumentChecked /></el-icon>
          <template #title>评分展示</template>
        </el-menu-item>
        <el-menu-item class="li" index="/history">
          <el-icon class="icon"><Memo /></el-icon>
          <template #title>历史记录</template>
        </el-menu-item>
      </el-menu>

      <!-- 用户信息 - 简约现代风格 -->
      <div class="user-modern" v-if="!isCollapsed && userStore.isLoggedIn">
        <div class="modern-left">
          <el-avatar :size="42" class="modern-avatar" :style="{ backgroundColor: avatarColor }">
            {{ userStore.username?.charAt(0).toUpperCase() }}
          </el-avatar>
          <div class="modern-info">
            <div class="modern-name">{{ userStore.username }}</div>
            <div class="modern-role-badge" :class="userStore.role">
              <span class="badge-dot"></span>
              {{ getRoleName(userStore.role) }}
            </div>
          </div>
        </div>
        <div class="modern-right">
          <el-tooltip content="退出登录" placement="top">
            <el-button class="modern-logout" text @click="handleLogout">
              <el-icon><SwitchButton /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </div>
      
      <!-- 收缩状态下的退出按钮 -->
      <div class="collapsed-logout" v-if="isCollapsed && userStore.isLoggedIn">
        <el-tooltip content="退出登录" placement="right">
          <el-button 
            circle 
            size="small" 
            class="logout-icon"
            @click="handleLogout"
          >
            <el-icon><SwitchButton /></el-icon>
          </el-button>
        </el-tooltip>
      </div>
    </div>
    
    <!-- 右侧内容区域 -->
    <div class="main-content" :class="{ 'full-width': !userStore.isLoggedIn }">
      <!-- 顶部导航栏 - 登录后显示 -->
      <div class="custom-header" v-if="userStore.isLoggedIn">
        <h2>{{ route.meta.title }}</h2>
      </div>
      
      <!-- 主要内容区 -->
      <div class="custom-main" :class="{ 'no-header': !userStore.isLoggedIn }">
        <RouterView />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Menu, DocumentAdd, DocumentChecked, Memo, Setting, SwitchButton 
} from '@element-plus/icons-vue'
import useUserStore from '@/stores/user'
import useCommentStore from '@/stores/dashboard'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const commentStore = useCommentStore()
const isTeacher = computed(() => userStore.role === 'teacher')
const isStudent = computed(() => userStore.role === 'student')
const isCollapsed = ref(false)
const activePath = ref(route.path)
const avatarColor = ref('#409eff');//用户头像的颜色值
// 切换侧边栏
const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}

// 监听路由变化，更新激活菜单
watch(
  () => route.path,
  (newPath) => {
    activePath.value = newPath
  },
  { immediate: true }
)

// 获取角色名称
const getRoleName = (role) => {
  const roleMap = {
    'teacher': '教师',
    'student': '学生'
  }
  return roleMap[role] || role
}

// 退出登录
const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => { 
    userStore.clearUserInfo()
    commentStore.reset()
    ElMessage.success('已退出登录')
    router.push('/login')
  }).catch(() => {})
}
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.app-container {
  display: flex;
  height: 100vh;
  font-family: 'Microsoft YaHei', Arial, sans-serif;
  width: 100%;
  box-sizing: border-box;
}

.sidebar {
  width: 230px;
  background: linear-gradient(180deg, #2c3e50, #34495e);
  color: white;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  box-shadow: 2px 0 5px rgba(0,0,0,0.1);
  flex-shrink: 0;
}

.sidebar-collapsed {
  width: 60px !important;
}

.sidebar-header {
  padding: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.sidebar-header h2 {
  font-size: 1.3rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.collapse-btn {
  background: rgba(255,255,255,0.1);
  border: none;
  color: white;
  height: 28px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  flex-shrink: 0;
}

.collapse-btn:hover {
  background: rgba(255,255,255,0.2);
}

.menu {
  flex: 1;
  background: transparent;
  border-right: none !important;
}

:deep(.el-menu) {
  background: transparent !important;
  border-right: none !important;
}

:deep(.el-menu-item) {
  color: rgba(255,255,255,0.8) !important;
  background: transparent !important;
}

:deep(.el-menu-item:hover) {
  background: rgba(255,255,255,0.1) !important;
  color: white !important;
}

:deep(.el-menu-item.is-active) {
  background: rgba(52, 152, 219, 0.8) !important;
  color: white !important;
}
/* 修复菜单折叠时的激活项样式 */
:deep(.el-menu--collapse) {
  width: 60px !important;
}
:deep(.el-menu--collapse .el-menu-item) {
  width: 60px !important;
  min-width: 60px !important;
  max-width: 60px !important;
  padding: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}
:deep(.el-menu--collapse .el-menu-item .icon) {
  margin-right: 0 !important;
  font-size: 1.4rem;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 100%;
}

:deep(.el-menu--collapse .el-menu-item .el-icon) {
  margin-right: 0 !important;
  font-size: 1.4rem;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 100%;
}

.icon {
  font-size: 1.2rem;
  margin-right: 10px;
}
/* 用户个人信息 */
.user-modern {
  margin: 16px 12px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 50px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: all 0.3s;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.user-modern:hover {
  background: rgba(255, 255, 255, 0.1);
}

.modern-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.modern-avatar {
  background: #81536f !important;
  color: white;
  font-weight: bold;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.modern-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.modern-name {
  color: white;
  font-weight: 500;
  font-size: 1.1rem;
}

.modern-role-badge {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-left: 13px;
  font-size: 0.6rem;
  color: rgba(255, 255, 255, 0.7);
}

.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.modern-role-badge.admin .badge-dot { background: #f56c6c; }
.modern-role-badge.teacher .badge-dot { background: #e6a23c; }
.modern-role-badge.student .badge-dot { background: #67c23a; }

/* 退出登录按钮样式 */
.modern-logout {
  color: rgba(255, 255, 255, 0.882);
  padding: 6px;
  border-radius: 50%;
  transition: all 0.3s;
}
.modern-logout .el-icon {
  color: rgba(241, 206, 206, 0.882);
}
.modern-logout:hover {
  background: rgba(255, 255, 255, 0.1);
  
}
.modern-logout:hover .el-icon{
  color: #f56c6c;
}

.collapsed-logout {
  padding: 15px;
  display: flex;
  justify-content: center;
  border-top: 1px solid rgba(255,255,255,0.1);
}

.logout-icon {
  background: rgba(255,255,255,0.1);
  border: none;
  color: white;
  width: 30px;
  height: 30px;
}

.logout-icon:hover {
  background: rgba(255,255,255,0.2);
}

.main-content {
  flex: 1;
  height: 100%;
  background-color: #f5f7fa;
  overflow-y: auto;
  transition: all 0.3s ease;
}

.main-content.full-width {
  margin-left: 0;
}

.custom-header {
  position: fixed;
  top: 0;
  left: 230px;
  right: 0;
  background-color: #ffffff;
  border-bottom: 1px solid #e6e8f0;
  color: #333;
  padding: 16px 24px;
  z-index: 999;
  transition: left 0.3s ease;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

/* .custom-header h2 {
  font-size: 1.2rem;
  font-weight: 500;
  color: #2c3e50;
} */

.sidebar-collapsed + .main-content .custom-header {
  left: 60px;
}

.custom-main {
  margin-top: 68px;
  padding: 20px;
  min-height: calc(100vh - 68px);
}

.custom-main.no-header {
  margin-top: 0;
  padding: 0;
  min-height: 100vh;
}
</style>