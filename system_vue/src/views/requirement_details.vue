<template>
    <div class="essay-history">
      <!-- 顶部导航和信息 -->
      <div class="history-header">
        <div class="header-left">
          <el-button type="primary" link @click="router.back()" class="back-btn">
            <el-icon><ArrowLeft /></el-icon>返回
          </el-button>
          <div class="task-info">
            <h1 class="task-title">作文要求</h1>
            <p>{{ taskInfo.requirement || '作文题目' }}</p>
            <div class="task-meta">
              <span class="meta-item">
                <el-icon><Document /></el-icon>
                已提交：{{ statistics.submitted }}/{{ statistics.total }}人
              </span>
              <span class="meta-item">
                <el-icon><Checked /></el-icon>
                平均分：{{ statistics.averageScore }}分
              </span>
              <span class="meta-item">
                <el-icon><Calendar /></el-icon>
                发布时间：{{ formatDate(taskInfo.createdAt) }}
              </span>
            </div>
          </div>
        </div>
        
        <!-- 排序和筛选 -->
        <div class="header-right">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索学生姓名"
            :prefix-icon="Search"
            clearable
            class="search-input"
          />
        </div>
      </div>
  
      <!-- 统计卡片 -->
      <div class="statistics-cards">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-item">
            <div class="stat-icon" style="background: #ecf5ff; color: #409eff">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">总提交人数</div>
              <div class="stat-value">{{ statistics.submitted }}</div>
            </div>
          </div>
        </el-card>
        
        <el-card class="stat-card" shadow="hover">
          <div class="stat-item">
            <div class="stat-icon" style="background: #f0f9eb; color: #67c23a">
              <el-icon><Star /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">最高分</div>
              <div class="stat-value">{{ statistics.maxScore }}</div>
            </div>
          </div>
        </el-card>
        
        <el-card class="stat-card" shadow="hover">
          <div class="stat-item">
            <div class="stat-icon" style="background: #fdf6ec; color: #e6a23c">
              <el-icon><DataLine /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">平均分</div>
              <div class="stat-value">{{ statistics.averageScore }}</div>
            </div>
          </div>
        </el-card>
        
        <el-card class="stat-card" shadow="hover">
          <div class="stat-item">
            <div class="stat-icon" style="background: #fef0f0; color: #f56c6c">
              <el-icon><Timer /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">平均字数</div>
              <div class="stat-value">{{ statistics.averageWordCount }}</div>
            </div>
          </div>
        </el-card>
      </div>
  
      <!-- 作文列表 -->
      <div class="essay-list-section">
        <div class="section-header">
          <h2 class="section-title">📚 学生作文列表</h2>
          <span class="essay-count">共 {{ filteredEssays.length }} 篇作文</span>
        </div>
  
        <el-table
          :data="paginatedEssays"
          style="width: 100%"
          stripe
          v-loading="loading"
          @row-click="viewEssayDetail"
          class="essay-table"
        >
          <el-table-column prop="studentName" label="学生姓名" width="120">
            <template #default="{ row }">
              <div class="student-info">
                <el-avatar :size="32" :src="row.avatar || defaultAvatar" />
                <span>{{ row.student_name }}</span>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="grade" label="年级" width="100">
            <template #default="{ row }">
              <el-tag size="small" effect="plain">{{getGradeLabel(row.grade) }}</el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="essayTitle" label="作文题目" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              <span>{{ row.title }}</span>
            </template>
          </el-table-column>
          
          <el-table-column prop="wordCount" label="字数" width="100" sortable :sort-method="sortByWordCount">
            <template #default="{ row }">
              <span>{{ row.word_count }}字</span>
            </template>
          </el-table-column>
          
          <el-table-column prop="score" label="分数" width="100" sortable>
            <template #default="{ row }">
              <el-tag :type="getScoreType(row.score,row.grade)" size="large" effect="dark" class="score-tag">
                {{ row.score }}分
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="submitTime" label="上传时间" width="180" sortable>
            <template #default="{ row }">
              <div class="time-info">
                <el-icon><Calendar /></el-icon>
                <span>{{ formatDate(row.submitTime) }}</span>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button 
                  type="primary" 
                  link 
                  @click.stop="viewEssayDetail(row)"
                  class="action-btn"
                >
                  查看
                </el-button>
                <el-button 
                  type="warning" 
                  link 
                  @click.stop="handleReject(row)"
                  class="action-btn"
                >
                  打回
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
  
        <!-- 分页 -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="filteredEssays.length"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
  
      <!-- 作文详情抽屉 -->
      <el-drawer
        v-model="drawerVisible"
        :title="currentEssayTitle"
        size="70%"
        direction="rtl"
        class="essay-drawer"
        destroy-on-close
        @close="handleDrawerClose"
      >
        <div v-loading="drawerLoading" class="drawer-content">
          <!-- 当数据加载完成后，渲染 dashboard 组件 -->
          <Dashboard 
            v-if="currentEssayId"
            :essay-id="currentEssayId"
            :readonly="true"
          />
          <el-empty v-else description="暂无数据" />
        </div>
      </el-drawer>
    </div>
  </template>
  
  <script setup>
  import { ref, reactive, computed, onMounted } from 'vue'
  import { useRouter, useRoute } from 'vue-router'
  import { ElMessage } from 'element-plus'
  import { 
    ArrowLeft, Document, Checked, Calendar, Sort, Search,
    User, Star, DataLine, Timer, Download
  } from '@element-plus/icons-vue'
  import dayjs from 'dayjs'
  import taskApi from '@/api/tasks'
  import getGradeLabel from '@/utils/grade'
  import Dashboard from '@/views/dashboard.vue'
  import historyApi from '@/api/history'

  const router = useRouter()
  const route = useRoute()
  const taskId = route.params.taskId
  
  // 数据状态
  const loading = ref(false)
  const taskInfo = ref({})
  const essays = ref([])
  
  // 排序和筛选
  const sortOrder = ref('desc')
  const searchKeyword = ref('')
  
  // 分页
  const currentPage = ref(1)
  const pageSize = ref(10)
  
  // 默认头像
  const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'
  
  // 统计数据
  const statistics = computed(() => {
    const total = essays.value.length //学生上交的作文篇数
    if (total === 0) {
      return {
        submitted: 0,
        total: taskInfo.value.student_count,
        maxScore: 0,
        averageScore: 0,
        averageWordCount: 0
      }
    }
    
    const scores = essays.value.map(e => e.score)
    const maxScore = Math.max(...scores)
    const averageScore = Math.round(scores.reduce((a, b) => a + b, 0) / total)
    const averageWordCount = Math.round(
      essays.value.reduce((a, b) => a + (b.word_count || 0), 0) / total
    )
    
    return {
      submitted: total,
      total: taskInfo.value.student_count || 0, // 班级总人数，从班级信息获取
      maxScore,
      averageScore,
      averageWordCount
    }
  })
  
  // 过滤和排序后的作文列表
  const filteredEssays = computed(() => {
    let filtered = essays.value
    
    // 搜索过滤
    if (searchKeyword.value) {
      filtered = filtered.filter(e => 
        e.student_name.includes(searchKeyword.value)
      )
    }
    
    // 排序
    return [...filtered].sort((a, b) => {
      if (sortOrder.value === 'desc') {
        return b.score - a.score
      } else {
        return a.score - b.score
      }
    })
  })
  
  // 分页数据
  const paginatedEssays = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    return filteredEssays.value.slice(start, end)
  })
  
  // 获取分数标签类型
  const getScoreType = (score,grade) => {
    const maxScore = (grade >= 10 && grade <= 12) ? 60 : 100
    const percentage = (score / maxScore) * 100
    if (percentage >= 90) return 'success'
    if (percentage >= 75) return 'primary'
    if (percentage >= 60) return 'warning'
    return 'danger'
  }
  
  // 格式化日期
  const formatDate = (date) => {
    return dayjs(date).format('YYYY-MM-DD')
  }

  
  // 字数排序方法
  const sortByWordCount = (a, b) => {
    return a.wordCount - b.wordCount
  }
  
  // 分页变化
  const handleSizeChange = (val) => {
    pageSize.value = val
    currentPage.value = 1
  }
  
  const handleCurrentChange = (val) => {
    currentPage.value = val
  }

  // 抽屉状态
  const drawerVisible = ref(false)
  const drawerLoading = ref(false)
  const currentEssayId = ref(null)
  const currentEssayTitle = ref('')
  // 查看作文详情
  const viewEssayDetail = (row) => {
    currentEssayId.value = row.id
    currentEssayTitle.value = `${row.student_name}的作文`
    drawerVisible.value = true  // 打开抽屉，会触发 @open 事件
  }

  // 抽屉关闭时清理数据
  const handleDrawerClose = () => {
    currentEssayId.value = null
  }

  // 获取数据
  const fetchData = async () => {
    loading.value = true
    try {
      const task_res= await taskApi.getTaskDetail(taskId)
      console.log('作文题目详情接口响应：', task_res);
      const essay_res=await taskApi.getEssays(taskId)
      console.log('学生上传历史记录接口响应：',essay_res);
      if(task_res.status==200){
          taskInfo.value = task_res.data
      }
      if(essay_res.status==200){
          essays.value = essay_res.data
      }
      
    } catch (error) {
      ElMessage.error('获取数据失败')
    } finally {
      loading.value = false
    }
  }

  // 打回作文
  const handleReject = (row) => {
    ElMessageBox.confirm(
      `确定要将 ${row.student_name} 的作文打回吗？`,
      '打回确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).then(async () => {
      try {
        // 调用打回API
        const response = await taskApi.rejectEssay(row.id)
        console.log('打回响应:', response);
        if (response.status === 200) {
          ElMessage.success('已打回作文')
          // 刷新列表
          fetchData()
        }
      } catch (error) {
        ElMessage.error('打回失败')
      }
    }).catch(() => {})
  }
  
  onMounted(() => {
    fetchData()
  })
  </script>
  
  <style>
  /* 不加 scoped，但用类名限定范围 */
  .essay-drawer .el-drawer__body {
    padding: 0 !important;
    background: #f5f7fa !important;
    overflow: hidden;
  }
  </style>

  <style scoped>
  .essay-history {
    padding: 24px;
    max-width: 1400px;
    margin: 0 auto;
    background: #f5f7fa;
    min-height: calc(100vh - 60px);
  }
  
  /* 头部区域 */
  .history-header {
    background: white;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
    display: flex;
    flex-direction: column;  /* 改为垂直布局 */
    position: relative;      /* 为绝对定位提供参考 */
  }
  
  .header-left {
    display: flex;
    gap: 24px;
    align-items: center;
    flex: 0 1 auto;
  }
  
  /* 右侧区域 - 强制靠右 */
  .header-right {
    display: flex;
    gap: 16px;
    align-items: center;
    flex-wrap: wrap;
    margin-left: auto;  /* 关键：自动左边距，强制靠右 */
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
  
  .back-btn:hover {
    transform: translateY(-1px);
  }

  .task-info{
    margin: 0 80px;
  }
  .task-info h1 {
    font-size: 22px;
    font-weight: 600;
    color: #1f2f3d;
  }
  
  
  .task-meta {
    display: flex;
    gap: 24px;
    color: #75787d;
    font-size: 14px;
    margin:8px 0 0 0;
  }
  
  .meta-item {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .search-input {
    width: 220px;
  }
  
  /* 统计卡片 */
  .statistics-cards {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-bottom: 24px;
  }
  
  .stat-card {
    border: none;
    border-radius: 12px;
    transition: all 0.3s;
  }
  
  .stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1) !important;
  }
  
  .stat-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px;
  }
  
  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
  }
  
  .stat-info {
    flex: 1;
  }
  
  .stat-label {
    color: #909399;
    font-size: 13px;
    margin-bottom: 4px;
  }
  
  .stat-value {
    font-size: 24px;
    font-weight: 600;
    color: #1f2f3d;
  }
  
  /* 表格区域 */
  .essay-list-section {
    background: white;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  }
  
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }
  
  .section-title {
    font-size: 18px;
    font-weight: 600;
    color: #1f2f3d;
    margin: 0;
  }
  
  .essay-count {
    color: #909399;
    font-size: 14px;
    background: #f0f2f5;
    padding: 4px 12px;
    border-radius: 20px;
  }
  
  .essay-table {
    margin-top: 16px;
  }
  
  .essay-table :deep(.el-table__row) {
    cursor: pointer;
    transition: background-color 0.3s;
  }
  
  .essay-table :deep(.el-table__row:hover) {
    background-color: #f5f7fa !important;
  }
  
  .student-info {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .score-tag {
    font-weight: 600;
    min-width: 60px;
    text-align: center;
  }
  
  .time-info {
    display: flex;
    align-items: center;
    gap: 4px;
    color: #606266;
  }
  
  /* 操作按钮组 */
  .action-buttons {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .action-btn {
    padding: 4px 8px !important;
    font-size: 13px;
  }

  .action-btn.el-button--warning {
    color: #eb3d3d;
  }

  .action-btn.el-button--warning:hover {
    color: #f39e9e;
    background: transparent;
  }

  /* 分页 */
  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
  
  /* 抽屉样式 */

  .drawer-content {
    height: 100%;
    overflow-y: auto;
    /* padding: 20px; */
    background: #f5f7fa;
  }
  
  .student-card {
    border-radius: 12px;
  }
  
  .student-header {
    display: flex;
    gap: 16px;
    margin-bottom: 16px;
  }

  .stat-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
    color: #606266;
    font-size: 14px;
  }
  
  .stat-row:last-child {
    margin-bottom: 0;
  }
  
  .score-highlight {
    color: #f56c6c;
    font-weight: 600;
    font-size: 16px;
  }
  
  .essay-content-card,
  .comment-card {
    border-radius: 12px;
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .essay-content {
    padding: 8px 0;
  }
  
  .paragraph {
    margin-bottom: 16px;
    line-height: 1.8;
    color: #303133;
  }
  
  .comment-content {
    padding: 8px 0;
    line-height: 1.8;
    color: #606266;
    font-style: italic;
  }
  
  /* 响应式 */
  @media screen and (max-width: 1024px) {
    .statistics-cards {
      grid-template-columns: repeat(2, 1fr);
    }
  }
  
  @media screen and (max-width: 768px) {
    .history-header {
      flex-direction: column;
      align-items: flex-start;
    }
    
    .header-right {
      width: 100%;
    }
    
    .search-input {
      width: 100%;
    }
    
    .statistics-cards {
      grid-template-columns: 1fr;
    }
    
    .task-meta {
      flex-direction: column;
      gap: 8px;
    }
  }
  </style>