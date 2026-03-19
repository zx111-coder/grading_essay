<template>
  <div class="login-page">
    <div class="login-wrapper">
      <!-- 左侧品牌区（保持风格统一） -->
      <div class="left-side">
        <div class="brand-content">
          <h1>智能作文批改系统</h1>
          <p>AI 辅助写作 · 精准评分 · 快速提升</p>
          <div class="decoration-icon">✍️ 📖 ✨</div>
        </div>
      </div>

      <!-- 右侧登录表单 -->
      <div class="right-side">
        <div class="form-box">
          <h2>账号登录</h2>
          <p class="desc">欢迎回来，高效写作从这里开始</p>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-width="80px"
            class="login-form"
          >
            <!-- 用户名/账号 -->
            <el-form-item label="用户名" prop="username">
              <el-input 
                v-model="form.username" 
                prefix-icon="el-icon-user"
              />
            </el-form-item>

            <!-- 密码 -->
            <el-form-item label="密码" prop="password">
              <el-input 
                v-model="form.password" 
                type="password" 
                show-password 
                prefix-icon="el-icon-lock"
              />
            </el-form-item>

            <!-- 记住密码 -->
            <el-form-item class="remember-item">
              <el-checkbox v-model="rememberMe">记住我，下次自动登录</el-checkbox>
            </el-form-item>

            <!-- 登录按钮 -->
            <el-form-item>
              <el-button 
                type="primary" 
                class="btn-login" 
                @click="handleLogin" 
                round
                :loading="loading"
              >
                {{ loading ? '登录中...' : '立即登录' }}
              </el-button>
            </el-form-item>

            <!-- 注册跳转 -->
            <div class="register-link">
              <p>还没有账号？<router-link to="/register">立即注册</router-link></p>
            </div>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage} from 'element-plus'
import { useRouter } from 'vue-router'
import useUserStore from '@/stores/user';
import user_api from '@/api/user.js';

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const userStore = useUserStore();
// 表单数据
const form = reactive({
  username: '',
  password: '',
  role:'student'
})
const rememberMe = ref(false);
// 登录表单验证规则：仅保留必填校验（移除所有格式/复杂度验证）
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// 登录处理逻辑
const handleLogin = async () => {
  // 第一步：仅验证用户名/密码是否为空
  if (!formRef.value) return
  try {
    const response = await user_api.loginUserInfo(form);
    console.log("登录返回信息", response);
    if (response.statusText=='OK') {
        // 更新用户状态
        userStore.setUserInfo(response.data, rememberMe.value);
        ElMessage.success({
        message: '登录成功！',
        duration: 1500
        });
        router.push('/');
    }else {
        ElMessage.error(response.data?.message || '登录失败');
    }
  } catch (error) {
    console.log('登录失败！')
  } finally {
      loading.value = false;
  }
}

</script>

<style scoped>
/* 样式完全保留，仅保证界面美观 */
.login-page {
  width: 100vw;
  height: 100vh;
  background: #f7f8fa;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-wrapper {
  width: 900px;
  height: 550px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
  display: flex;
  overflow: hidden;
}

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

.login-form {
  width: 100%;
}

.remember-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
/* 调整“记住我”被选中之后的颜色 */
:deep(.el-checkbox.is-checked .el-checkbox__label) {
  color: #588cbc;
}

.btn-login {
  width: 80%;
  height: 44px;
  font-size: 16px;
  margin-top: 10px;
  background-color: #273747;
  border-color: #273747;
}

.register-link {
  text-align: center;
  font-size: 13px;
  color: #666;
  margin-top: 10px;
}

.register-link a {
  color: #588cbc;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
}

.register-link a:hover {
  color: #588cbc;
  text-decoration: underline;
  background-color: transparent !important;
}
</style>