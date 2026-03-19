// api/classes.js
import path from './path.js';
import instance from '../utils/request.js';

const api={
    async getMyClass(){
        const res= await instance.get(path.stuUrl+'/my-class');
        return res;
    },
    async joinClass(classCode){
        const res= await instance.post(path.stuUrl+`/join/${classCode}`);
        return res;
    },
    async leaveClass(classId){
        const res= await instance.post(path.stuUrl+`/leave/${classId}`);
        return res;
    }
}
export default api;