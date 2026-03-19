import path from './path.js';
import axios from '../utils/request.js';

const api={
    async setUserInfo(data){
        const res= await axios.post(path.baseUrl+'/users',data);
        return res;
    },
    async getUserInfo(){
        const res=await axios.get(path.baseUrl+'/users');
        return res;
    } 
}
export default api;