// api/user.js
import path from './path.js';
import instance from '../utils/request.js';

const api={
    async registerUserInfo(data){
        const res= await instance.post(path.authUrl+'/register',{
            username:data.username,
            password:data.password,
            role:data.role,
        });
        return res;
    },
    async loginUserInfo(data){
        const res= await instance.post(path.authUrl+'/login',{
            username:data.username,
            password:data.password,
        });
        return res;
    },
}
export default api;