//router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import useUserStore from '@/stores/user'
import { ElMessage } from 'element-plus'
const router = createRouter({
  history: createWebHistory(),
  routes: [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/login.vue'),
    meta: {
      title: '登录',
      requiresAuth: false  // 不需要登录
    }
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/register.vue'),
    meta: {
      title: '注册',
      requiresAuth: false  // 不需要登录
    }
  },
  {
    path: '/',
    name: 'analysis',
    component: () => import('@/views/analysis.vue'),
    meta: {
      title: '作文批改',  // 定义路由元信息（动态展示界面）
      requiresAuth: true,  // 需要登录
      roles: ['student', 'teacher']  // 允许所有角色访问
    }
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/dashboard.vue'),
    meta: {
      title: '作文点评',  // 定义路由元信息（动态展示界面）
      requiresAuth: true,  // 需要登录
      roles: ['student', 'teacher']  // 允许所有角色访问
    }
  },
  {
    path: '/classes',
    name: 'classes',
    component: () => import('@/views/create_class.vue'),
    meta: {
      title: '班级管理',  // 定义路由元信息（动态展示界面）
      requiresAuth: true,  // 需要登录
      roles: ['teacher']  
    }
  },
  {
    path: '/myClass',
    name: 'myClass',
    component: () => import('@/views/my_class.vue'),
    meta: {
      title: '我的班级',  // 定义路由元信息（动态展示界面）
      requiresAuth: true,  // 需要登录
      roles: ['student']  
    }
  },
  {
    path: '/history',
    name: 'history',
    component: () => import('@/views/history.vue'),
    meta: {
      title: '历史记录',  // 定义路由元信息（动态展示界面）
      requiresAuth: true,  // 需要登录
      roles: ['student', 'teacher']  
    }
  },
  {
    path: '/class/:classId',
    name: 'ClassDetail',
    component: () => import('@/views/class_details.vue'),  // 班级详情页面
    meta: { 
      requiresAuth: true,  // 需要登录
      title: '班级详情',
      roles: ['student', 'teacher']  
    }
  },
  {
    path: '/class/:classId/task/:taskId',
    name: 'RequirementDetail',
    component: () => import('@/views/requirement_details.vue'),  // 作文题目详情页面
    meta: { 
      requiresAuth: true,  // 需要登录
      title: '题目详情',
      roles: ['teacher']  
    }
  }
  // 404 页面
  // {
  //   path: '/:pathMatch(.*)*',
  //   name: 'not-found',
  //   component: () => import('@/views/404.vue'),
  //   meta: {
  //     title: '页面未找到',
  //     requiresAuth: false
  //   }
  // }
  ]
})
// 添加全局路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 作文批改系统` : '作文批改系统'
  
  // 获取用户 store
  const userStore = useUserStore()
  
  // 判断是否需要登录
  if (to.meta.requiresAuth) {
    // 需要登录但未登录
    if (!userStore.isLoggedIn) {
      next({
        path: '/login',
        query: { redirect: to.fullPath }  // 保存要跳转的页面，登录后跳回来
      })
      return
    }
    
    // 检查角色权限
    if (to.meta.roles && to.meta.roles.length > 0) {
      const userRole = userStore.role
      if (!to.meta.roles.includes(userRole)) {
        // 权限不足，跳转到首页
        ElMessage.error(`权限不足: 用户角色 普通${userRole} 无法访问 ${to.path}`); 
        next({ path: '/' })
        return
      }
    }
  }
  
  // 已登录用户访问登录/注册页，跳转到首页
  if (userStore.isLoggedIn && (to.path === '/login' || to.path === '/register')) {
    next({ path: '/' })
    return
  }
  
  // 其他情况正常放行
  next()
})
export default router