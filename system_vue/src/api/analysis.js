// api/analysis.js
import path from './path.js';
import axios from '../utils/request.js';

const api = {
    // 旧的同步接口
    async setEssayInfo(data) {
        const formData = new FormData()
        formData.append('grade', data.grade)
        formData.append('requirements', data.requirements)
        formData.append('upload_time', data.uploadTime)
        formData.append('analysis_text', data.content)
        if (data.taskId) {
            formData.append('task_id', data.taskId)
        }
        const res = await axios.post(path.baseUrl + '/analysis/sync', formData);
        return res;
    },

    // 新的流式接口
    async analyzeEssayStream(data, onProgress, onComplete, onError) {
        const formData = new FormData()
        formData.append('user_id', data.user_id)
        formData.append('grade', data.grade)
        formData.append('requirements', data.requirements)
        formData.append('upload_time', data.uploadTime)
        formData.append('analysis_text', data.content)
        if (data.taskId) {
            console.log('analysis.js代码包含taskId:', data.taskId);
            formData.append('task_id', data.taskId)
        }
        let reader = null;
        
        try {
            const response = await fetch(path.baseUrl + '/analysis', {
                method: 'POST',
                body: formData,
            });

            console.log('analysis响应:', response);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';
            let streamActive = true;

            while (streamActive) {
                const { done, value } = await reader.read();
                if (done) {
                    console.log('流读取完成');
                    break;
                }

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (!line.trim()) continue;

                    try {
                        const eventMatch = line.match(/event: (\w+)/);
                        const dataMatch = line.match(/data: (.+)/s);

                        if (eventMatch && dataMatch) {
                            const eventName = eventMatch[1];
                            const jsonData = JSON.parse(dataMatch[1].trim());
                            console.log("eventName:", eventName);
                            console.log("jsonData:", jsonData);
                            // 通用进度回调
                            if (onProgress) {
                                onProgress({
                                    event: eventName,
                                    data: jsonData.data,
                                    complete: jsonData.complete
                                });
                            }

                            // 处理完成事件
                            if (eventName === 'final_result') {
                                if (onComplete) onComplete(jsonData.data);
                                streamActive = false;
                                break;
                            }

                            // 处理错误事件
                            if (eventName === 'error') {
                                if (onError) onError(jsonData.data);
                                streamActive = false;
                                break;
                            }

                            // 如果事件标记为complete，也结束
                            if (jsonData.complete) {
                                streamActive = false;
                                break;
                            }
                        }
                    } catch (e) {
                        console.error('解析SSE数据失败:', e, line);
                    }
                }

                if (!streamActive) break;
            }
        } catch (error) {
            console.error('网络错误:', error);
            if (onError) onError(error);
            throw error;
        } finally {
            if (reader) {
                try {
                    await reader.cancel();
                } catch (e) {
                    console.error('取消reader失败:', e);
                }
            }
        }
    }
};

export default api;