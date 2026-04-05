<template>
    <div class="history-container">
      <div class="page-header">
        <!-- 搜索和筛选 -->
        <div class="search-section">
          <el-input
            v-model="searchText"
            placeholder="搜索标题"
            :prefix-icon="Search"
            clearable
            style="width: 250px"
            @input="handleSearch"
          />
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :shortcuts="dateShortcuts"
            @change="handleDateSearch"
          />
        </div>
      </div>
  
      <!-- 历史记录表格 -->
      <el-card class="history-card">
        <el-table
          v-loading="loading"
          :data="historyList"
          style="width: 100%"
          stripe
          border
        >
          <el-table-column prop="title" label="作文名称" min-width="200">
            <template #default="{ row, $index }">
              <div class="title-wrapper" @mouseenter="hoverRow = $index" @mouseleave="hoverRow = null">
                <!-- 编辑状态 -->
                <div v-if="editingRow === row.id" class="edit-title">
                  <el-input
                    v-model="editTitleValue"
                    ref="titleInputRef"
                    size="small"
                    placeholder="请输入标题"
                    @keyup.enter="confirmEdit(row)"
                    @blur="handleBlur(row)"
                    @click.stop
                  />
                </div>
                <!-- 显示状态 -->
                <div v-else class="display-title">
                  <span class="title-text">{{ row.title || '无标题' }}</span>
                  <el-icon 
                    v-if="hoverRow === $index" 
                    class="edit-icon"
                    @click.stop="startEdit(row)"
                  >
                    <Edit />
                  </el-icon>
                </div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="upload_date" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.upload_date) }}
            </template>
          </el-table-column>
          
          <el-table-column prop="grade" label="年级" width="100">
            <template #default="{ row }">
              {{ getGradeLabel(row.grade) }}
            </template>
          </el-table-column>
          
          <el-table-column prop="word_count" label="字数" width="100">
            <template #default="{ row }">
              {{ row.word_count || 0 }}字
            </template>
          </el-table-column>
          
          <el-table-column prop="score" label="分数" width="100">
            <template #default="{ row }">
                {{ row.score || '未评分' }}
            </template>
          </el-table-column>

          <el-table-column prop="score" label="等级" width="100">
            <template #default="{ row }">
              <el-tag :type="getLevelType(getScoreLevel(row.score,row.grade))" size="small">
                {{ getScoreLevel(row.score,row.grade) }}
              </el-tag>
            </template>
          </el-table-column>
<!-- 
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'completed' ? 'success' : 'danger'" size="small">
                {{ row.status === 'completed' ? '已完成' : '失败' }}
              </el-tag>
            </template>
          </el-table-column> -->
          
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button 
                type="primary" 
                link 
                @click="viewHistoryDetail(row.id)"
                class="view-btn"
              >
                查看结果
              </el-button>
              <el-button 
                type="danger" 
                link 
                @click="handleDelete(row)"
                class="delete-btn"
                :icon="Delete"
                circle
                :disabled="row.task_id" 
                :class="{ 'delete-disabled': row.task_id }" 
              />
            </template>
          </el-table-column>
        </el-table>
  
        <!-- 分页 -->
        <div class="pagination-container" v-if="total > 0">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="total"
            :page-sizes="[10, 20, 30, 50]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted, markRaw, nextTick, computed, onUnmounted } from 'vue'
  import { useRouter } from 'vue-router'
  import { ElMessage, ElMessageBox } from 'element-plus'
  import { Search, Delete, Edit } from '@element-plus/icons-vue'
  import historyApi from '@/api/history.js'
  import useUserStore from '@/stores/user.js'
  import getGradeLabel from '@/utils/grade'
  import useCommentStore from '@/stores/dashboard.js'
  
  const router = useRouter()
  const userStore = useUserStore()
  const commentStore = useCommentStore()
  // 数据
  const loading = ref(false) // 加载状态
  const refreshTimer = ref(null) // 定时器引用
  const historyList = ref([]) // 历史记录列表
  const total = ref(0)
  const currentPage = ref(1) // 当前页
  const pageSize = ref(10)
  const searchText = ref('')
  const dateRange = ref([]) // 日期范围
  const isAnalyzing = computed(() => commentStore.isAnalyzing)// 判断是否正在分析中
  // 标题编辑相关的变量
  const hoverRow = ref(null)  // 当前鼠标悬停的行索引
  const editingRow = ref(null)  // 当前正在编辑的行ID
  const editTitleValue = ref('')  // 编辑框中的标题值
  const titleInputRef = ref(null)  // 输入框引用
  const isConfirming = ref(false) // 是否正在确认修改

  //开始编辑标题
  const startEdit = (row) => {
    editingRow.value = row.id
    editTitleValue.value = row.title || ''
    // 在下一个 tick 聚焦输入框
    nextTick(() => {
      if (titleInputRef.value) {
        titleInputRef.value.focus()
      }
    })
  }

  // 处理失去焦点事件
  const handleBlur = (row) => {
    if (isConfirming.value) return
    // 如果还在编辑状态，直接触发确认修改
    if (editingRow.value === row.id) {
      confirmEdit(row)
    }
  }

  // 确认修改
  const confirmEdit = async (row) => {
    if (!editingRow.value) return
    const newTitle = editTitleValue.value.trim()
    const oldTitle = row.title || '无标题'
    // 如果标题没有变化或者为空，直接取消编辑
    if (newTitle === row.title || !newTitle) {
      editingRow.value = null
      return
    }
    // 设置标志位，防止重复弹出
    isConfirming.value = true
    try {
      // 弹出确认框
      await ElMessageBox.confirm(
        `确定将标题从《${oldTitle}》修改为《${newTitle}》吗？`,
        '修改确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'info',
        }
      )
      
      // 调用修改标题的API
      const res = await historyApi.updateHistoryTitle(row.id, newTitle)
      if (res.data.code === 200) {
        ElMessage.success('标题修改成功')
        // 更新本地数据
        row.title = newTitle
        editingRow.value = null
      } else {
        ElMessage.error(res.data.message || '修改失败')
      }
    } catch (error) {
      if (error === 'cancel') {
        // 用户取消修改
        editingRow.value = null
      } else {
        console.error('修改标题失败:', error)
        ElMessage.error('修改失败，请重试')
      }
    }finally {
    // 无论成功或失败，都要重置标志位
    // 使用 setTimeout 延迟重置，确保事件处理完成
    setTimeout(() => {
      isConfirming.value = false
    }, 300)
  }
  }

  // 日期快捷选项
  const dateShortcuts = [
    {
      text: '最近一周',
      value: () => {
        const end = new Date()
        const start = new Date()
        start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
        return [start, end]
      },
    },
    {
      text: '最近一个月',
      value: () => {
        const end = new Date()
        const start = new Date()
        start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
        return [start, end]
      },
    },
    {
      text: '最近三个月',
      value: () => {
        const end = new Date()
        const start = new Date()
        start.setTime(start.getTime() - 3600 * 1000 * 24 * 90)
        return [start, end]
      },
    },
  ]
  
  // 获取历史记录
  const fetchHistory = async () => {
    loading.value = true
    try {
      const params = {
        page: currentPage.value,
        page_size: pageSize.value
      }
      
      // 如果有搜索条件
      if (searchText.value) {
        params.title = searchText.value
      }
      if (dateRange.value && dateRange.value.length === 2) {
        params.start_date = dateRange.value[0]
        params.end_date = dateRange.value[1]
      }
      
      const res = await historyApi.getUserHistory(userStore.userid, params)
      console.log('历史记录接口返回:', res);
      
      if (res.data.code === 200) {
        historyList.value = res.data.data.list.map(item => ({
          ...item,
          status: item.score ? 'completed' : 'failed'  // 根据是否有分数判断状态
        }))
        total.value = res.data.data.total
      } else {
        ElMessage.error(res.data.message)
      }
    } catch (error) {
      console.error('获取历史记录失败:', error)
      ElMessage.error('获取历史记录失败')
    } finally {
      loading.value = false
    }
  }
  
  // 查看历史记录详情 - 跳转到 dashboard
  const viewHistoryDetail = (essayId) => {
    if (isAnalyzing.value) {
      ElMessage.warning('当前有作文正在分析中，请稍后再查看历史记录')
      return
    }
    // 跳转到 dashboard，并传递 essayId 参数
    router.push({
      path: '/history/dashboard',
      query: { historyId: essayId }
    })
  }
  
  // 搜索
  const handleSearch = () => {
    currentPage.value = 1
    fetchHistory()
  }
  
  // 日期搜索
  const handleDateSearch = () => {
    currentPage.value = 1
    fetchHistory()
  }

  const DeleteIcon = markRaw(Delete)
  // 删除历史记录
  const handleDelete = (row) => {
    ElMessageBox.confirm(
        `确定要删除《${row.title || '无标题'}》这条记录吗？`,
        '删除确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
          icon: DeleteIcon,  // 添加删除图标
        }
    )
    .then(async () => {
        try {
          const res = await historyApi.deleteHistory(row.id)
          if (res.data.code === 200) {
            ElMessage.success('删除成功')
            // 重新获取当前页的数据
            fetchHistory()
          } else {
            ElMessage.error(res.data.message || '删除失败')
          }
        } catch (error) {
          console.error('删除历史记录失败:', error)
          ElMessage.error('删除失败，请重试')
        }
    })
    .catch(() => {
      // 用户取消删除
      ElMessage.info('已取消删除')
    })
  }
  // 格式化日期时间
  const formatDateTime = (dateStr) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hour = String(date.getHours()).padStart(2, '0')
    const minute = String(date.getMinutes()).padStart(2, '0')
    return `${year}-${month}-${day} ${hour}:${minute}`
  }
  
  // 获取评分等级
    const getScoreLevel = (score,grade) => {
      const maxScore = grade >= 10 ? 60 : 100
      // 计算百分比用于渐变色判断
      const percentage = (score / maxScore) * 100
      if (percentage >= 88) return '优秀'
      if (percentage >= 75) return '良好'
      if (percentage >= 60) return '及格'
      return '待提升'
    }
  // 等级标签类型
    const getLevelType = (status) => {
        const typeMap = {
            '优秀': 'success',
            '良好': 'primary',
            '及格': 'warning',
            '待提升': 'danger',
        };
        return typeMap[status] || 'info';
    };
  // 分页
  const handleSizeChange = (val) => {
    pageSize.value = val
    fetchHistory()
  }
  
  const handleCurrentChange = (val) => {
    currentPage.value = val
    fetchHistory()
  }
  
  onMounted(() => {
    fetchHistory()
    if(isAnalyzing.value) {
       // 每2分钟刷新一次
      refreshTimer.value = setInterval(() => {
        fetchHistory()
      }, 2 * 60 * 1000)
    }
  })
  onUnmounted(() => {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  })
  </script>
  
  <style scoped>
  .history-container {
    min-height: calc(100vh - 60px);
    background-color: #f5f7fa;
  }
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 16px;
  }
  
  .search-section {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }
  
  .history-card {
    border-radius: 8px;
  }

  /* 标题这行 */
  .title-wrapper {
    position: relative;
    width: 100%;
    min-height: 32px;
    display: flex;
    align-items: center;
  }

  /* 显示标题区域 */
  .display-title {
    display: flex;
    align-items: center;
    width: 100%;
    justify-content: space-between;
  }
  
  .title-text {
    font-weight: 500;
    color: #2c3e50;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1;
  }
  /* 编辑图标 */
  .edit-icon {
    font-size: 16px;
    color: #909399;
    cursor: pointer;
    margin-left: 8px;
    padding: 4px;
    border-radius: 4px;
    transition: all 0.2s ease;
    flex-shrink: 0;
  }

  .edit-icon:hover {
    color: #409eff;
    background-color: #ecf5ff;
  }

  /* 编辑状态 */
  .edit-title {
    width: 100%;
  }

  .edit-title :deep(.el-input__wrapper) {
    width: 100%;
    padding: 1px 8px;
  }

  .edit-title :deep(.el-input__inner) {
    height: 28px;
    line-height: 28px;
  }

  /* 操作列样式 */
    .operation-wrapper {
    display: flex;
    align-items: center;
    gap: 4px;
    position: relative;
    }

    .view-btn {
      background-color: transparent;
    }

    .delete-btn {
      opacity: 0;
      transform: scale(0.8);
      transition: all 0.3s ease;
      color: #f56c6c;
      margin-left: 60px;
      padding: 4px;
    }

    /* 删除按钮禁用状态 */
    .delete-btn.delete-disabled {
      opacity: 0.3 !important;
      color: #c0c4cc !important;
      cursor: not-allowed;
      pointer-events: auto;  /* 保持能够显示禁用提示 */
    }

    /* 禁用状态下悬停不改变样式 */
    .delete-btn.delete-disabled:hover {
      background-color: transparent;
      color: #c0c4cc !important;
    }

    /* 鼠标悬停整行时的效果 */
    .el-table__row:hover .delete-btn {
      opacity: 1;
      transform: scale(1);
    }

    /* 删除按钮悬停效果 */
    .delete-btn:hover {
    background-color: #fef0f0;
    color: #f56c6c;
    }

    /* 查看按钮样式 */
    .view-btn:hover {
    color: #409eff;
    background-color: transparent;
    }

  
  .pagination-container {
    margin-top: 24px;
    display: flex;
    justify-content: flex-end;
  }
  
  :deep(.el-table .cell) {
    white-space: nowrap;
  }
  
  @media (max-width: 768px) {
    .history-container {
      padding: 16px;
    }
    
    .page-header {
      flex-direction: column;
      align-items: flex-start;
    }
    
    .search-section {
      width: 100%;
    }
    
    .search-section .el-input,
    .search-section .el-date-picker {
      width: 100% !important;
    }
    
    .pagination-container {
      justify-content: center;
    }
  }
  </style>