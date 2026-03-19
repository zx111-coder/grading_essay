//utils/request.js
import axios from 'axios';
const instance=axios.create({
    timeout:5000
})
//浏览器状态码
const errorHandle=(status,data)=>{
    let message = '';
    switch(status){
        case 400:
            message = data?.detail || data?.message || '请求错误';
            console.log("请求错误:", message);
            break;
        case 401:
            message = data?.detail || data?.message || '登录已过期，请重新登录';
            console.log("服务器认证失败");
            break;
        case 403:
            message = '没有权限访问';
            console.log("服务器拒绝访问");
            break;
        case 404:
            message = '请求地址不存在';
            console.log("请求地址出错");
            break;
        case 408:
            message = '请求超时';
            console.log("请求超时"); 
            break;
        case 500:
            message = '服务器内部错误';
            console.log("服务器内部错误");
            break;
        case 501:
            message = '服务未实现';
            console.log("服务未实现");
            break;
        case 502:
            message = '网关错误';
            console.log("网关错误");
            break;
        case 503:
            message = '服务不可用';
            console.log("服务不可用");
            break;
        case 504:
            message = '网关超时';
            console.log("网关超时");
            break;
        case 505:
            message = 'HTTP版本不受支持';
            console.log("HTTP版本不受支持");
            break;
        default:
            message = data?.detail || data?.message || '未知错误';
            console.log(info);
    }
    // ✅ 显示错误信息到界面
    if (message) {
        ElMessage.error(message);
    }
}

// ✅ 不需要 token 的接口白名单
const whiteList = [
    '/api/auth/login',
    '/api/auth/register'
];

//请求拦截器
instance.interceptors.request.use(
    config=>{
        // ✅ 检查是否是白名单接口
        const isWhiteList = whiteList.some(path => config.url.includes(path));
        if (!isWhiteList) {
            const userinfo = localStorage.getItem('userinfo') || sessionStorage.getItem('userinfo');
            const userData = JSON.parse(userinfo);
            const token = userData.token;
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
        }else {
            console.log('白名单接口，不需要token:', config.url);
        }
        //请求前的处理
        console.log('发送请求:', config.url, config.data);  
        return config;
    },
    error=>{
        console.error('请求拦截器错误:', error);
        return Promise.reject(error);
    }
)
//响应拦截器
instance.interceptors.response.use(
    response=>{
        //响应后的处理
        return response;
    },
    error=>{
        console.log("error响应错误:",error);
        if(error.response){
            errorHandle(error.response.status,error.response.data);
        }else if(error.request){
            console.log('没有收到响应:', error.request);
            ElMessage.error('网络连接失败，请检查后端服务');
        }else {
            // 请求配置出错
            console.log('请求配置错误:', error.message);
            ElMessage.error('请求配置错误');
        }
        return Promise.reject(error);
    }
)
export default instance;