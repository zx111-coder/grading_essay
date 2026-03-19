<template>
  <div class="register-page">
    <div class="register-wrapper">
      <!-- 左侧品牌区 -->
      <div class="left-side">
        <div class="brand-content">
          <h1>智能作文批改系统</h1>
          <p>AI 辅助写作 · 精准评分 · 快速提升</p>
          <div class="decoration-icon">✍️ 📖 ✨</div>
        </div>
      </div>

      <!-- 右侧注册表单 -->
      <div class="right-side">
        <div class="form-box">
          <h2>创建账号</h2>
          <p class="desc">欢迎加入作文批改系统，开始高效学习</p>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-width="80px"
            class="register-form"
          >
            <!-- 角色 -->
            <el-form-item label="用户角色" prop="role">
              <el-radio-group v-model="form.role">
                <el-radio label="student">学生</el-radio>
                <el-radio label="teacher">教师</el-radio>
              </el-radio-group>
            </el-form-item>

            <!-- 用户名 -->
            <el-form-item label="用户名" prop="username">
              <el-input v-model="form.username" placeholder="请输入姓名/用户名" />
            </el-form-item>

            <!-- 密码 -->
            <el-form-item label="密码" prop="password">
              <el-input v-model="form.password" type="password" show-password placeholder="6-20位字母+数字" />
            </el-form-item>

            <!-- 确认密码 -->
            <el-form-item label="确认密码" prop="confirmPwd">
              <el-input v-model="form.confirmPwd" type="password" show-password placeholder="再次输入密码" />
            </el-form-item>

            <!-- 按钮 -->
            <el-form-item>
              <el-button type="primary" class="btn-register" @click="handleRegister" round :loading="loading">
                {{ loading ? '注册中...' : '立即注册' }}
              </el-button>
            </el-form-item>

            <div class="login-link">
              <p>已有账号？<router-link to="/">立即登录</router-link></p>
            </div>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import useUserStore from '../stores/user';
import user_api from '@/api/user.js'
import { useRouter } from 'vue-router';
const router = useRouter();
const userStore = useUserStore();
const loading = ref(false);
const formRef = ref(null);
const form = reactive({
  role: 'student',
  username: '',
  password: '',
  confirmPwd: ''
})

const rules = {
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度3-20个字符', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        // 复用你的用户名格式验证逻辑
        const username = value.trim()
        if (username && !/^[a-zA-Z0-9_\u4e00-\u9fa5]+$/.test(username)) {
          callback(new Error('用户名只能包含字母、数字、下划线或中文'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度6-20个字符', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        // 复用你的密码复杂度验证逻辑
        if (value) {
          const hasNumber = /\d/.test(value)
          const hasLetter = /[a-zA-Z]/.test(value)
          if (!hasNumber || !hasLetter) {
            callback(new Error('密码必须包含数字和字母'))
          } else {
            callback()
          }
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  confirmPwd: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (!value) {
          callback() // 必填验证由上一条规则处理，这里只处理一致性
        } else if (value !== form.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: ['blur', 'input']
    }
  ]
}

// 注册处理
const handleRegister = async () => {
  if(!formRef.value) return;
  // 调用Element Plus的表单验证方法
  try {
    // 全量验证表单，验证失败会直接抛出错误
    await formRef.value.validate();
  } catch (error) {
    // 验证失败时提示用户，不执行后续注册逻辑
    ElMessage.error('表单填写有误，请修正后再提交！');
    return; // 终止注册流程
  }
  loading.value = true;
  try {
    const response = await user_api.registerUserInfo(form);
    console.log("注册返回信息", response);
    if (response.statusText=='OK') {
      // 更新用户状态
      userStore.setUserInfo(response.data,false);
      
      ElMessage.success({
        message: '注册成功！',
        duration: 1000
      });
      router.push('/');
      // // 延迟跳转，让用户看到成功提示
      // setTimeout(() => {
        
      // }, 1000);
    } else {
      ElMessage.error(response.data?.message || '注册失败');
    }
  } catch (error) {
    console.log('注册错误:', error.response);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
/* 页面整体 */
.register-page {
  width: 100vw;
  height: 100vh;
  background: #f7f8fa;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 主容器 */
.register-wrapper {
  width: 900px;
  height: 550px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
  display: flex;
  overflow: hidden;
}

/* 左侧品牌区 */
.left-side {
  flex: 1;
  background: linear-gradient(180deg, #658eb7, #3f5b76);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.brand-content {
  text-align: center;
  padding: 20px;
}

.brand-content h1 {
  font-size: 28px;
  margin-bottom: 12px;
}

.brand-content p {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 20px;
}

.decoration-icon {
  font-size: 22px;
  opacity: 0.8;
}

/* 右侧表单 */
.right-side {
  width: 420px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.form-box {
  width: 100%;
}

.form-box h2 {
  font-size: 24px;
  color: #333;
  margin-bottom: 6px;
}

.desc {
  color: #909399;
  font-size: 13px;
  margin-bottom: 30px;
}

/* 表单 */
.register-form {
  width: 100%;
}

/* 角色前的小圆圈样式 */
:deep(.el-radio__input.is-checked .el-radio__inner) {
  background-color: #658eb7;  /* 使用左侧渐变起始色 */
  border-color: #658eb7;
}
:deep(.el-radio__input.is-checked + .el-radio__label) {
  color: #658eb7;
}
:deep(.el-radio__inner::after) {
  width: 5px;       /* 默认是6px，调大到8px（里面的实心小点） */
  height: 6px;      /* 默认是6px，调大到8px */
}
:deep(.el-radio__inner:hover) {
  border-color: #658eb7;
}

/* 注册按钮 */
.btn-register {
  width: 80%;
  height: 44px;
  font-size: 16px;
  margin-top: 10px;
  background-color: #273747;
  border-color: #273747;
}

/* 登录链接 */
.login-link {
  text-align: center;
  font-size: 13px;
  color: #666;
  margin-top: 10px;
}
.login-link a {
  color: #588cbc;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
}
.login-link a:hover {
  color: #588cbc;
  text-decoration: underline;
  background-color: transparent !important;
}
</style>