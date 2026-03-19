import path from './path.js';
import axios from '../utils/request.js';

const api={
    async setEssayInfo(data){
        const formData = new FormData()
        formData.append('grade', data.grade)
        formData.append('requirements', data.requirements)
        // 循环追加文件
        data.files.forEach(file => {
            formData.append('files', file)
        })
        const res= await axios.post(path.baseUrl+'/upload',formData,
            {
                timeout:30000,
                headers: {'Content-Type': undefined}
            }
        );
        return res;
    }
}
export default api;