import { defineStore } from 'pinia';
//名为userInfo的状态存储,state是存储状态
const useUserStore = defineStore('userInfo', {
  state: () => ({
    userid: 0, // 用户ID
    username: '未登录',
    role:'student',
    token:'',
    rememberMe: false
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,  // 是否登录(布尔值)
    isAdmin: (state) => state.role === 'admin',  // 是否是管理员
  },
  //actions修改状态的方法
  actions: {
    setUserInfo(Form, remember = false) { 
      this.userid = Form.user_id
      this.username = Form.username
      this.role = Form.role
      this.token = Form.access_token
      this.rememberMe = remember;
      this.saveToStorage(); // 保存到对应的 storage
    },
    // 保存到对应的 storage
    saveToStorage() {
      const userData = {
        userid: this.userid,
        username: this.username,
        role: this.role,
        token: this.token,
        rememberMe: this.rememberMe
      };
      if (this.rememberMe) {
        localStorage.setItem('userinfo', JSON.stringify(userData));
      } else {
        sessionStorage.setItem('userinfo', JSON.stringify(userData));
      }
    },
    // 从 storage 恢复
    restoreFromStorage() {
      // 优先从 localStorage
      let data = localStorage.getItem('userinfo');
      let storage = 'localStorage';
      
      if (!data) {
        data = sessionStorage.getItem('userinfo');
        storage = 'sessionStorage';
      }
      
      if (data) {
        try {
          const userData = JSON.parse(data);
          this.userid = userData.userid || 0;
          this.username = userData.username || '未登录';
          this.role = userData.role || 'student';
          this.token = userData.token || '';
          this.rememberMe = userData.rememberMe || false;
          console.log(`从 ${storage} 恢复用户信息`);
          return true;
        } catch (error) {
          console.error('恢复用户信息失败:', error);
        }
      }
      return false;
    },
    // 清除用户名的方法
    clearUserInfo() {
      this.userid = 0 // 清除用户ID
      this.username = '未登录'
      this.role = 'user'
      this.token = '' // 清除token
      this.rememberMe = false;
      localStorage.removeItem('userinfo');
      sessionStorage.removeItem('userinfo');
    }
  },
  // persist: {
  //   key: 'userinfo',           // localStorage 的 key 名
  //   storage: sessionStorage,      // 使用 localStorage 存储
  //   paths: ['user_id', 'username', 'role', 'token'] // 指定要持久化的字段
  // },
})

export default useUserStore;