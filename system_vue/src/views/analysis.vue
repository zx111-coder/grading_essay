<template>
    <div class="analysis-container">     
      <!-- 上传区域 -->
      <div class="upload-section">
        <div class="upload-area" @click="triggerFileInput" @dragover.prevent @drop="handleDrop">
          <input 
            type="file" 
            ref="fileInput"
            @change="handleFileChange"
            accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
            multiple
            style="display: none"
          >
          
          <div v-if="uploadData.files.length === 0" class="upload-placeholder">
            <div class="upload-icon">
              <span>📄</span>
              <span>🖼️</span>
              <span>📝</span>
            </div>
            <h3>点击或拖拽上传文件</h3>
            <p class="upload-hint">支持 PDF、Word 文档或图片文件，可一次性上传多个文件</p>
            <p class="file-types">支持的格式：PDF、DOCX、JPG、JPEG、PNG</p>
          </div>
          
          <div v-else class="uploaded-files">
            <h3>已上传的文件 ({{ uploadData.files.length }})</h3>
            <div class="files-list">
              <div v-for="(file, index) in uploadData.files" :key="index" class="file-item">
                <div class="file-icon">
                  {{ getFileIcon(file.name) }}
                </div>
                <div class="file-info">
                  <p class="file-name">{{ file.name }}</p>
                  <p class="file-size">{{ formatFileSize(file.size) }}</p>
                </div>
                <button @click.stop="removeFile(index)" class="remove-btn">×</button>
              </div>
            </div>
          </div>
        </div>
        
        <div class="upload-controls">
          <div class="control-group">
            <label for="grade-select">选择年级：</label>
            <div class="grade-radios">
              <div v-for="grade in grades" :key="grade.value" class="radio-item">
                <input 
                  type="radio" 
                  :id="'grade-' + grade.value"
                  :value="grade.value"
                  v-model="uploadData.grade"
                  name="essay-grade"
                >
                <label :for="'grade-' + grade.value">{{ grade.label }}</label>
              </div>
            </div>
          </div>
          
          <div class="control-group">
            <label for="requirements">作文要求：</label>
            <textarea 
              id="requirements"
              v-model="uploadData.requirements"
              placeholder="请输入作文要求（可不填）..."
              rows="3"
            ></textarea>
          </div>
          
          <div class="control-group">
            <button 
              @click="handleUpload"
              :disabled="uploadData.files.length === 0 || isUploading"
              class="upload-btn"
            >
              {{ isUploading ? '上传中...' : '上传' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 确认上传弹窗  -->
      <div v-if="showConfirmDialog" class="confirm-dialog-overlay">
        <div class="confirm-dialog">
          <div class="dialog-header">
            <h3>确认上传</h3>
            <button @click="showConfirmDialog = false" class="close-btn">×</button>
          </div>
          <div class="dialog-content">
            <p>您将上传 {{ uploadData.files.length }} 个文件进行分析：</p>
            <ul class="file-list-dialog">
              <li v-for="(file, index) in uploadData.files" :key="index">
                {{ file.name }}
              </li>
            </ul>
            <div class="dialog-details">
              <p><strong>年级：</strong> {{ uploadData.grade !== 0 ? getGradeLabel(uploadData.grade) : '未选择' }}</p>
              <p v-if="uploadData.requirements"><strong>作文要求：</strong> {{ uploadData.requirements }}</p>
            </div>
            <p class="confirm-text">确认开始处理这些文件吗？</p>
          </div>
          <div class="dialog-actions">
            <button @click="showConfirmDialog = false" class="cancel-btn">取消</button>
            <button @click="confirmUpload" class="confirm-btn">确认上传</button>
          </div>
        </div>
      </div>

      <!-- 后端处理后的文字显示 -->
      <div v-if="showContent" class="result-dialog-overlay">
        <div class="result-dialog">
          <!-- 弹窗头部 -->
          <div class="dialog-header">
            <h3>识别结果</h3>
            <button @click="showContent = false" class="close-btn">×</button>
          </div>
          <!-- 弹窗内容 -->
          <div class="dialog-content result-content">
            <div class="text-container">
              <div class="edit-item">
                <span>【作文年级】</span>
                <el-select 
                  v-model="analysisText.grade" 
                  placeholder="请选择作文年级"
                  style="width: 120px; margin-left: 8px;"
                  class="grade-select-center" 
                >
                  <el-option
                    v-for="item in grades"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
              </div>
              <div class="edit-item">
                <span>【作文要求】</span>
                <el-input 
                  v-model="analysisText.requirements" 
                  placeholder="请输入/编辑作文要求"
                  style="width: calc(100% - 80px); margin-left: 8px;"
                />
              </div>
              <div class="edit-item">
                <span>【作文内容】</span>
                <el-input
                  v-model="analysisText.content"
                  type="textarea"
                  placeholder="请编辑作文内容（支持换行/分段）"
                  :rows="10"
                  class="formatted-textarea"
                  style="width: calc(100% - 80px); margin-left: 8px; margin-top: 8px;"
                  resize="none"
                />
              </div>
            </div>
          </div>
          <!-- 弹窗底部按钮 -->
          <div class="dialog-actions">
            <button @click="showContent = false" class="cancel-btn">取消</button>
            <button @click="startAnalysis" class="analysis-btn">
              开始分析
            </button>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref,reactive,onMounted } from 'vue'
  import { ElMessage } from 'element-plus'
  import 'element-plus/es/components/message/style/css'
  import upload_api from '@/api/upload.js'
  import analysis_api from '@/api/analysis.js'
  import {useRouter, useRoute} from 'vue-router'
  import useCommentStore from '@/stores/dashboard.js';
  import useUserStore from '@/stores/user.js';
  // 文件上传相关
  const fileInput = ref(null)
  // 定义上传数据对象
  const uploadData = reactive({
    files: [],          // 文件列表
    grade: 0,         // 年级数组
    requirements: '',   // 作文要求  
    taskId: 0,      // 关联的任务ID
    classId: 0      // 关联的班级ID 
  })
  // const uploadedFiles = ref([])
  const isUploading = ref(false)
  const commentStore = useCommentStore();
  const userStore = useUserStore();
  // 关键：将 Store 实例暴露到全局 window 对象
  window.commentStore = commentStore
  // 年级选择
  const grades = ref([
    { value: 1, label: '一年级' },
    { value: 2, label: '二年级' },
    { value: 3, label: '三年级' },
    { value: 4, label: '四年级' },
    { value: 5, label: '五年级' },
    { value: 6, label: '六年级' },
    { value: 7, label: '初一' },
    { value: 8, label: '初二' },
    { value: 9, label: '初三' },
    { value: 10, label: '高一' },
    { value: 11, label: '高二' },
    { value: 12, label: '高三' },
  ])
  // const selectedGrades = ref([])
  
  // 作文要求
  // const requirements = ref('')
  
  // 处理后文本
  const analysisText = reactive({
    user_id:userStore.userid,
    grade:0,
    requirements:'',
    content:'',
    uploadTime:'',
    words_count:0,
    taskId: null
  })
  
  // 确认对话框
  const showConfirmDialog = ref(false)
  const showContent = ref(false)
  // 触发文件选择
  const triggerFileInput = () => {
    fileInput.value.click()
  }
  
  // 处理文件选择
  const handleFileChange = (event) => {
    const files = Array.from(event.target.files)
    addFiles(files)
  }
  
  // 处理拖放
  const handleDrop = (event) => {
    event.preventDefault()
    const files = Array.from(event.dataTransfer.files)
    addFiles(files)
  }
  
  // 添加文件
  const addFiles = (files) => {
    // 过滤只接受指定类型的文件
    const validFiles = files.filter(file => {
      const validTypes = ['application/pdf', 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'image/jpeg', 'image/jpg', 'image/png']
      return validTypes.includes(file.type) || 
             file.name.match(/\.(pdf|docx|jpg|jpeg|png)$/i)
    })
    
    uploadData.files = [...uploadData.files, ...validFiles]
  }
  
  // 删除文件
  const removeFile = (index) => {
    uploadData.files.splice(index, 1)
  }
  
  // 获取文件图标
  const getFileIcon = (fileName) => {
    if (fileName.match(/\.(pdf)$/i)) return '📄'
    if (fileName.match(/\.(docx)$/i)) return '📝'
    if (fileName.match(/\.(jpg|jpeg|png)$/i)) return '🖼️'
    return '📎'
  }
  
  // 格式化文件大小
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }
  
  // 获取年级标签
  const getGradeLabel = (value) => {
    if(!value) return ''
    const grade = grades.value.find(g => g.value === value)
    return grade ? grade.label : ''
  }

  // 格式化当前时间为「YYYY-MM-DD HH:mm:ss」格式（上传时间专用）
  const formatCurrentTime = () => {
    const date = new Date()
    const year = date.getFullYear()
    // 月份/日期/小时/分钟 补0成2位数
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hour = String(date.getHours()).padStart(2, '0')
    const minute = String(date.getMinutes()).padStart(2, '0')
    return `${year}-${month}-${day} ${hour}:${minute}`
  }  

  // 处理上传
  const handleUpload = () => {
    if(!uploadData.files.length){
      ElMessage.warning('请上传至少一个文件！')
      return
    }
    if(uploadData.grade===0){
      ElMessage.warning('请选择对应的年级！')
      return
    }
    showConfirmDialog.value = true
  }

  // 确认上传
  const confirmUpload = async() => {
    isUploading.value = true
    showConfirmDialog.value = false
    console.log('上传接口数据：', uploadData);
    try{
      const response=await upload_api.setEssayInfo(uploadData);
      console.log('上传接口响应：',response);
      if(response.data.code === 200){
        ElMessage.success(response.data.msg);
        analysisText.grade=response.data.data.grade;
        analysisText.requirements=response.data.data.requirements;
        analysisText.content=response.data.data.total_ocr_text;
        analysisText.words_count=response.data.data.words_count;
        showContent.value=true;
        console.log('analysisText:',analysisText);
      }else {
      // 后端业务错误（如文件格式错）
        ElMessage.error(response.data.msg);
      }
    }catch(error){
      // 网络错误/后端未启动/接口404
      console.error('上传请求失败：', error);
      ElMessage.error('上传失败，请稍后重试！');
    }finally {
      // 无论成功/失败，都关闭上传中状态
      isUploading.value=false;
    }
  }

  // 开始分析按钮设置
  const router=useRouter()
  const route=useRoute()

  const startAnalysis = async() => {
    if(!analysisText.content.trim()){
      ElMessage.warning('作文内容不能为空！')
      return
    }
    if (analysisText.grade === 0) {
      ElMessage.warning('请选择作文年级！')
      return
    }
    try {
      // progressText.value = '正在提交分析结果...'
      analysisText.uploadTime=formatCurrentTime();
      analysisText.taskId=uploadData.taskId; // 关联任务ID，方便后续查询
      commentStore.requirements=analysisText.requirements;
      commentStore.essay=analysisText.content;
      commentStore.words_count=analysisText.words_count;
      commentStore.grade=analysisText.grade;
      commentStore.upload_time=analysisText.uploadTime
      // 1. 启动分析流
      commentStore.startAnalysis(analysisText);
      // 2. 立即跳转
      router.push('/dashboard');
    } catch (error) {
      console.error('启动分析失败:', error);
      ElMessage.error('启动分析失败，请重试');
    }
  }
  onMounted(() => {
    // 检查是否有从班级详情传递过来的作文要求
    if (route.query.requirement) {
      uploadData.requirements = route.query.requirement
      console.log('从班级详情获取的作文要求:', route.query.requirement)
    }
    
    // 如果有 taskId，可以保存起来，后续上传时关联
    if (route.query.taskId) {
      uploadData.taskId = Number(route.query.taskId)
      console.log('从班级详情获取的任务ID:', uploadData.taskId)
    }
    
  })
  </script>
  
  <style scoped>
  *{
    padding: 0;
    margin: 0;
  }
  .analysis-container {
    padding: 20px;
    margin: 0 auto;
    /* background-color: #219653; */
  }
  
  .page-header {
    margin-bottom: 30px;
  }
  
  .page-header h1 {
    color: #2c3e50;
    margin-bottom: 10px;
    font-size: 2rem;
  }
  
  .subtitle {
    color: #7f8c8d;
    font-size: 1rem;
  }
  
  .upload-section {
    background: #f8f9fa;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin-bottom: 30px;
    overflow: hidden;
  }
  
  .upload-area {
    background: white;
    border: 3px dashed #dfe6e9;
    margin: 20px;
    border-radius: 8px;
    min-height: 250px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    cursor: pointer;
    transition: border-color 0.3s, background-color 0.3s;
    padding: 20px;
  }
  
  .upload-area:hover {
    border-color: #3498db;
    background-color: #f8fafc;
  }
  
  .upload-placeholder {
    text-align: center;
    color: #636e72;
  }
  
  .upload-icon {
    font-size: 3rem;
    margin-bottom: 20px;
  }
  
  .upload-icon span {
    margin: 0 10px;
  }
  
  .upload-hint {
    margin: 15px 0;
    font-size: 1.1rem;
    color: #2c3e50;
  }
  
  .file-types {
    color: #7f8c8d;
    font-size: 0.9rem;
  }
  
  .uploaded-files {
    width: 100%;
  }
  
  .uploaded-files h3 {
    color: #2c3e50;
    margin-bottom: 15px;
    text-align: center;
  }
  
  .files-list {
    max-height: 200px;
    overflow-y: auto;
  }
  
  .file-item {
    display: flex;
    align-items: center;
    padding: 12px;
    border: 1px solid #eee;
    border-radius: 6px;
    margin-bottom: 8px;
    background: #f8f9fa;
  }
  
  .file-icon {
    font-size: 1.5rem;
    margin-right: 12px;
  }
  
  .file-info {
    flex: 1;
  }
  
  .file-name {
    margin: 0;
    font-weight: 500;
    color: #2c3e50;
    word-break: break-all;
  }
  
  .file-size {
    margin: 5px 0 0 0;
    font-size: 0.8rem;
    color: #7f8c8d;
  }
  
  .remove-btn {
    background: #e74c3c;
    color: white;
    border: none;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    cursor: pointer;
    font-size: 1.2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.2s;
  }
  
  .remove-btn:hover {
    background: #c0392b;
  }
  
  .upload-controls {
    padding: 20px;
    background: #f8f9fa;
    /* border-top: 1px solid #eee; */
  }
  
  .control-group {
    margin-bottom: 20px;
  }
  
  .control-group label {
    display: block;
    margin-bottom: 8px;
    font-weight: 600;
    color: #2c3e50;
  }
  
  .grade-radios {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
  }
  
  .radio-item {
    display: flex;
    align-items: center;
  }
  
  .radio-item input {
    margin-right: 8px;
  }
  
  .radio-item label {
    margin: 0;
    font-weight: normal;
    cursor: pointer;
  }
  
  textarea {
    width: 100%;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-family: inherit;
    font-size: 0.95rem;
    resize: vertical;
    transition: border-color 0.3s;
  }
  
  textarea:focus {
    outline: none;
    border-color: #3498db;
    box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
  }
  
  .upload-btn {
    background: #3498db;
    color: white;
    border: none;
    padding: 14px 30px;
    font-size: 1.1rem;
    border-radius: 6px;
    cursor: pointer;
    width: 100%;
    font-weight: 600;
    transition: background 0.3s, transform 0.2s;
  }
  
  .upload-btn:hover:not(:disabled) {
    background: #2980b9;
    transform: translateY(-2px);
  }
  
  .upload-btn:disabled {
    background: #bdc3c7;
    cursor: not-allowed;
  }
  
  .upload-btn:active:not(:disabled) {
    transform: translateY(0);
  }
  
  /* 识别结果弹窗样式 */
  .result-dialog-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    padding: 20px 0;
  }
  
  .result-dialog {
    background: white;
    border-radius: 12px;
    width: 90%;
    max-width: 800px; /* 比确认弹窗宽，适配文本编辑 */
    max-height: 90vh; /* 限制最大高度，避免超出屏幕 */
    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }
  
  .result-content {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
  }
  
  .text-container {
    background: #f8f9fa;
    border: 1px solid #eee;
    border-radius: 6px;
    padding: 20px;
    max-height: none;
    margin-bottom: 20px;
  }
  
  .edit-item {
    width: 100%;
    margin-bottom: 12px;
    display: flex;
    align-items: flex-start;
    line-height: 32px; /* 和输入框高度对齐 */
  }
  .edit-item span {
    font-weight: 500;
    white-space: nowrap; /* 标签不换行 */
  }
  /* 让年级选择下拉框选项居中 */
  .el-select-dropdown .el-select-dropdown__item {
    text-align: center !important;
    justify-content: center !important;
    padding: 0 20px !important;
  }
  /* 最后一个项取消底部外边距 */
  .edit-item:last-child {
    margin-bottom: 0;
  }
  .edit-item .formatted-textarea{
    white-space: pre-wrap; /* 保留换行和所有空格 */
    word-wrap: break-word; /* 超长文字自动换行 */
    font-family: "SimSun", "Microsoft YaHei", sans-serif; /* 适配中文字体，让全角空格显示更准确 */
    line-height: 1.8; /* 增大行高，提升可读性 */
    letter-spacing: 0.5px; /* 优化中文排版 */
  }
  .dialog-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    background: #f8f9fa;
    border-bottom: 1px solid #eee;
  }
  
  .dialog-header h3 {
    margin: 0;
    color: #2c3e50;
  }
  
  .close-btn {
    background: none;
    border: none;
    font-size: 1.5rem;
    color: #7f8c8d;
    cursor: pointer;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
  }
  
  .close-btn:hover {
    background: #eee;
    color: #e74c3c;
  }
  
  .dialog-content {
    padding: 20px;
  }
  
  .file-list-dialog {
    max-height: 150px;
    overflow-y: auto;
    background: #f8f9fa;
    padding: 10px;
    border-radius: 6px;
    margin: 10px 0;
  }
  
  .dialog-details {
    margin: 15px 0;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 6px;
  }
  
  .dialog-details p {
    margin: 8px 0;
  }
  
  .confirm-text {
    font-weight: 600;
    color: #2c3e50;
    margin-top: 20px;
    text-align: center;
  }
  
  .dialog-actions {
    display: flex;
    justify-content: flex-end;
    padding: 20px;
    gap: 15px;
    border-top: 1px solid #eee;
  }
  
  .cancel-btn {
    background: #95a5a6;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 600;
    transition: background 0.3s;
  }
  
  .cancel-btn:hover {
    background: #7f8c8d;
  }
  
  .confirm-btn {
    background: #3498db;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 600;
    transition: background 0.3s;
  }
  
  .confirm-btn:hover {
    background: #2980b9;
  }
  
  .analysis-btn {
    background: #27ae60;
    color: white;
    border: none;
    padding: 10px 20px; /* 适配弹窗按钮尺寸 */
    font-size: 1rem; /* 适配弹窗按钮尺寸 */
    border-radius: 6px;
    cursor: pointer;
    font-weight: 600;
    transition: background 0.3s, transform 0.2s;
  }
  
  .analysis-btn:hover {
    background: #219653;
    transform: translateY(-2px);
  }
  
  .analysis-btn:active {
    transform: translateY(0);
  }
  
  @media (max-width: 768px) {
    .analysis-container {
      padding: 15px;
    }
    
    .grade-checkboxes {
      grid-template-columns: repeat(2, 1fr);
    }
    
    .upload-icon {
      font-size: 2.5rem;
    }
    .result-dialog {
      width: 95%;
      max-height: 85vh;
    }
  }
  /* 确认对话框样式 */
  .confirm-dialog-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }
  
  .confirm-dialog {
    background: white;
    border-radius: 12px;
    width: 90%;
    max-width: 500px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    overflow: hidden;
  }
  
  .dialog-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    background: #f8f9fa;
    border-bottom: 1px solid #eee;
  }
  
  .dialog-header h3 {
    margin: 0;
    color: #2c3e50;
  }
  
  .close-btn {
    background: none;
    border: none;
    font-size: 1.5rem;
    color: #7f8c8d;
    cursor: pointer;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
  }
  
  .close-btn:hover {
    background: #eee;
    color: #e74c3c;
  }
  
  .dialog-content {
    padding: 20px;
  }
  
  .file-list-dialog {
    max-height: 150px;
    overflow-y: auto;
    background: #f8f9fa;
    padding: 10px;
    border-radius: 6px;
    margin: 10px 0;
  }
  
  .dialog-details {
    margin: 15px 0;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 6px;
  }
  
  .dialog-details p {
    margin: 8px 0;
  }
  
  .confirm-text {
    font-weight: 600;
    color: #2c3e50;
    margin-top: 20px;
    text-align: center;
  }
  
  .dialog-actions {
    display: flex;
    justify-content: flex-end;
    padding: 20px;
    gap: 15px;
    border-top: 1px solid #eee;
  }
  
  .cancel-btn {
    background: #95a5a6;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 600;
    transition: background 0.3s;
  }
  
  .cancel-btn:hover {
    background: #7f8c8d;
  }
  
  .confirm-btn {
    background: #3498db;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 600;
    transition: background 0.3s;
  }
  
  .confirm-btn:hover {
    background: #2980b9;
  }
  
  @media (max-width: 768px) {
    .analysis-container {
      padding: 15px;
    }
    
    .grade-checkboxes {
      grid-template-columns: repeat(2, 1fr);
    }
    
    .upload-icon {
      font-size: 2.5rem;
    }
    .text-container {
      max-height: 300px; /* 小屏降低最大高度 */
    }
  }
  </style>
  