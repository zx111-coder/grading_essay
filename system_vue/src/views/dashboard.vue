<template>
  <div class="dashboard-content">
    <!-- 添加测试按钮 - 只在开发环境显示 -->
    <!-- <div v-if="isDevelopment" class="test-controls">
      <el-button type="warning" size="small" @click="handleTest" :loading="isAnalyzing">
        免费测试模式
      </el-button>
    </div> -->
    <div v-if="error" class="error-card">
      <el-icon class="error-icon"><CircleClose /></el-icon>
      <div class="error-text">{{ error?.message || '分析失败，请重试' }}</div>
      <el-button type="primary" size="small" @click="handleRetry">重新分析</el-button>
    </div>

    <div v-else-if="isAnalyzing || comment || jsonComment" class="score-container">
      <!-- 1. 作文基础信息折叠面板 -->
      <el-collapse v-model="activePanel" class="essay-info-panel">
        <el-collapse-item name="essayComment">
          <template #title>
            <span class="essay-title-bold">原作文内容</span>
          </template>
          <div class="essay-content">
            <div class="uploadTime">{{ formatTime(uploadTime) }}</div>
            {{ essayInfo || '暂无作文内容' }}
          </div>
          <div class="essay-info">
            <span class="grade">{{getGradeLabel(grade)}}</span>
            <span class="wordsCount">{{wordsCount}}字</span>
          </div>
        </el-collapse-item>
        <el-collapse-item name="essayBaseInfo">
          <template #title>
            <span class="essay-title-bold">作文要求</span>
          </template>
          <div class="essay-requirements">
              {{ requirements || '未明确要求' }}
          </div>
        </el-collapse-item>
      </el-collapse>

      <!-- 2. 总分卡片（仅分析完成后显示） -->
      <div v-if="jsonComment" class="total-score-card">
        <div class="score-circle-wrapper">
          <div class="score-circle" :style="scoreCircleStyle">
            <span class="score-num">{{ displayScore }}</span>
            <span class="num">总分</span>
          </div>
          <div class="score-level" :style="scoreLevelStyle">
            {{ getScoreLevel(jsonComment?.scores?.score) }}
          </div>
        </div>
        <div class="scores-wrapper">
          <!-- 满分值标签 - 放在语言表达正上方 -->
          <div class="max-score-header">
            <MaxScoreEditor
              v-model="customMaxScore"
              :min="1"
              :max="200"
              :step="5"
              size="small"
              compact
              :confirm-message="getConfirmMessage"
              @change="handleMaxScoreChange"
            />
          </div>
          <div class="sub-scores">
            <div class="sub-score-item">
              <span class="label">内容具体</span>
              <span class="value">{{ adjustedScores.content }}/{{ adjustedScores.contentMax }}</span>
            </div>
            <div class="sub-score-item">
              <span class="label">语言表达</span>
              <span class="value">{{ adjustedScores.language }}/{{ adjustedScores.languageMax }}</span>
            </div>
            <div class="sub-score-item">
              <span class="label">逻辑规范</span>
              <span class="value">{{ adjustedScores.structure }}/{{ adjustedScores.structureMax }}</span>
            </div>
            <div class="sub-score-item">
              <span class="label">基础规范</span>
              <span class="value">{{ adjustedScores.basic }}/{{ adjustedScores.basicMax }}</span>
            </div>
          </div>
        </div>
        <div class="summary-comment">
          <h4>总评</h4>
          <p>{{ jsonComment?.sum || '暂无总评' }}</p>
        </div>
      </div>

      <!-- 3. 实时分析内容展示 -->
      <div class="real-time-content">
        <div class="content-header">
          <h3>AI 分析详情</h3>
          <el-tag v-if="isAnalyzing" type="info">分析中...</el-tag>
          <el-tag v-else type="success">分析完成</el-tag>
        </div>
        <div class="content-body">
          <!-- 加载中 -->
          <div v-if="!comment && isAnalyzing" class="loading-text">
            <el-skeleton :rows="8" animated />
          </div>
          <!-- 显示分析内容 - 直接使用文本，保留换行-->
          <MarkdownRenderer 
            v-else-if="comment" 
            :content="comment" 
            class="analysis-wrapper"
          /> 
          <!-- 空状态 -->
          <div v-else class="empty-analysis">
            <el-empty description="暂无分析详情" />
          </div>

        </div>
      </div>
    </div>

    <!-- 空状态（未开始分析） -->
    <div v-else class="empty-state">
      <el-empty description="暂无分析数据" />
      <el-button type="primary" @click="router.push('/')" class="upload_btn">前往上传</el-button>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, watchEffect, nextTick } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';// 导入 ElDivider
import { CircleClose } from '@element-plus/icons-vue';
import useCommentStore from '@/stores/dashboard.js';
import getGradeLabel from '@/utils/grade';
import historyApi from '@/api/history.js'
import MarkdownRenderer from '@/components/markdown.vue' 
import MaxScoreEditor from '@/components/scoreEditor.vue';
const commentStore = useCommentStore();
const router = useRouter();
const route = useRoute()
const activePanel = ref(); //绑定作文信息展示面板
////////////////////////////////////////////////////////////////
// commentStore.isAnalyzing= false;
// commentStore.comment ="好的，同学，很高兴能读到你的作文。作为一名语文老师，我会认真阅读你的文字，并给出我的建议，希望能帮助你写得更好。\n\n**一、粗略点评**\n\n这篇以《一起听蛙》为题的作文，紧扣“倾听”这一主题，通过描写聆听蛙鸣的经历，巧妙地将自然之音与历史人物、文化典故联系起来，表达了对古人精神世界的倾听与思考。文章结构清晰，从个人体验出发，层层递进，最终升华主题。最大的优点是立意深远，语言富有文采，引用了大量古诗词，展现了你的阅读积累。全文699字，符合字数要求，文体为散文/记叙文，也符合“文体自选”的要求。最需要注意的问题是部分段落内部逻辑可以更紧密，个别语句的衔接可以更自然。\n\n**二、吸睛改写**\n\n*   **标题改写**：原标题《一起听蛙》点明了事件，但可以更具诗意和深度。例如《蛙鸣声里听千年》或《倾听，一场跨越时空的对话》。\n*   **开头改写**：你的开头（段落2）已经很有意境，直接引用《记承天寺夜游》的句子，营造了静谧的氛围。可以稍作调整，让“倾听”的动作更突出：“‘庭下如积水空明……’ 月色如水，我独坐窗前，屏息凝神，侧耳倾听。那水田中传来的，不是简单的聒噪，而是一首铿锵有力、撼人心魄的自然交响曲——蛙鸣。”\n*   **结尾改写**：你的结尾（段落10）呼应开头，富有哲理。可以再强化一下“倾听”带来的成长感：“今夜，我不再是孤单的听者。我与稼轩同听豪情，与放翁共感悲愤，在万千蛙鼓中，我倾听到了华夏血脉里奔流不息的回响。原来，真正的倾听，是让心灵向历史敞开，在声音的密林里，找到精神的故乡。”\n\n**三、作文改错**\n\n1.  **错别字/笔误**：\n    *   段落4：“强虏灰飞烟灭”应为“樯橹灰飞烟灭”。\n    *   段落5：“稻花香里说丰年，听取蛙声一片”是辛弃疾的词，你在段落4已提到辛弃疾，此处应保持人名一致。\n    *   段落8：“铁马冰河入梦来”是陆游的诗句，人物上下文需一致。\n2.  **语句不通顺**：\n    *   段落3：“一切仿佛凝固起来，静谧的，幽深的，动听的……” 这里“凝固”与“动听”在感觉上略有矛盾。可以改为：“一切仿佛慢了下来，周遭是如此的静谧与幽深，唯有那动听的蛙鸣，清晰地叩击着耳鼓。”\n    *   段落7：“而今我竟能通过蛙鸣……进行对话” 这句话稍显冗长。可以简化为：“而今，我竟能透过这亘古不变的蛙鸣，与千百年前的灵魂对话。”\n3.  **标点使用**：全文逗号使用较多，部分长句可以考虑用分号或句号断开，使节奏更清晰。例如段落2末尾“……交响曲，撼人心魄……” 后面可以用句号。\n\n**四、文体分析**\n\n本文是一篇**抒情散文**，融合了写景、叙事与议论。\n*   **结构**：非常清晰。**段落1（标题）** 点题。**段落2-3** 是“起”，描写眼前听蛙的场景与感受。**段落4-9** 是“承”与“转”，主体部分，通过蛙鸣联想（辛弃疾、陆游、普通农夫），展开对历史与文化的倾听与思考。**段落10** 是“合”，总结升华，点明倾听的意义。\n*   **逻辑与段落作用**：以“蛙鸣”为线索，从实（自然之声）到虚（历史之音），从个人感受到文化共鸣，逻辑层层推进。段落4、6、8分别引述不同人物，构成并列又递进的关系。段落5、7、9则起到抒发感想、衔接过渡的作用。\n\n**五、作文亮点**\n\n1.  **立意高远，构思巧妙**：你没有停留在“倾听自然声音”的层面，而是将“蛙鸣”作为一把钥匙，打开了通向古典诗词和历史情怀的大门，真正做到了“在倾听中成长”，这是本文最出色的地方。\n2.  **文化底蕴深厚**：熟练且恰当地引用了苏轼、辛弃疾、陆游等人的名句，并与“蛙”的意象紧密结合，显示了丰富的阅读积累和良好的文化素养。\n3.  **语言优美，富有诗意**：如“铿锵有力的蛙鸣”、“自然的乐师”、“心灵的共鸣”等表达，以及整体营造的静谧深邃的意境，都体现了你较强的语言驾驭能力。\n\n**六、写作建议**\n\n1.  **强化“倾听”的细节描写**：在开头听蛙的部分（段落2-3），可以更细致地描写你“如何”倾听。例如：“我闭上眼睛，让呼吸慢下来，那些起初混杂的鸣叫渐渐分出了声部：高亢的是领唱，低沉的是和声，间歇处还有几声清脆的独奏……” 这样能让“倾听”的动作更具体可感。\n2.  **理顺联想之间的过渡**：从辛弃疾到陆游的转换（段落6到段落8）可以更自然。可以加一个简短的过渡句，如“这慷慨的蛙鸣尚未远去，另一阵夹杂着风雨声的蛙鼓，又将我的思绪带到了边关与梦乡……”\n3.  **让感悟更个人化**：在段落9联想到古代农夫后，可以简短地联系一下自己。例如：“听着想着，我忽然觉得，这蛙鸣也像是在催促着我这个田野边的少年，莫负光阴，努力生长。” 这样能使文章的情感落脚点更扎实，紧扣“我们共同在倾听中成长”的题目要求。\n\n', 'sum': '同学，你的这篇《一起听蛙》让老师眼前一亮！你巧妙地以‘蛙鸣’为线索，将一次普通的夜晚聆听，写成了一场穿越时空的文化之旅，立意非常新颖深刻。文中信手拈来的古诗词引用，展现了你不俗的阅读积累，也让文章充满了诗意的美感。结构上从实到虚，层层推进，也很清晰。如果能在开头将‘倾听’时的细微感受写得更具体，在历史人物联想之间加上更流畅的过渡，并最终将宏大的感悟与个人的成长更紧密地结合，这篇文章将会更加完美。你已经拥有了非常优秀的写作潜质，请保持这份对文字的敏感和热爱，继续广泛阅读，勤于练笔，未来可期！";
// commentStore.json_comment = {'scores':{'score': 90, 'content': 33, 'structure': 18, 'language': 22, 'basic': 15}, 'sum': '同学，你的这篇《一起听蛙》让老师眼前一亮！你巧妙地以‘蛙鸣’为线索，将一次普通的夜晚聆听，写成了一场穿越时空的文化之旅，立意非常新颖深刻。文中信手拈来的古诗词引用，展现了你不俗的阅读积累，也让文章充满了诗意的美感。结构上从实到虚，层层推进，也很清晰。如果能在开头将‘倾听’时的细微感受写得更具体，在历史人物联想之间加上更流畅的过渡，并最终将宏大的感悟与个人的成长更紧密地结合，这篇文章将会更加完美。你已经拥有了非常优秀的写作潜质，请保持这份对文字的敏感和热爱，继续广泛阅读，勤于练笔，未来可期！'};
// commentStore.essay ='一起听蛙\r\n\r\n\u3000\u3000“庭下水积空明，水中藻荇交横……” 我独自坐在窗前，倾听着水田中那铿锵有力的蛙鸣，宛如在欣赏一首交响曲，撼人心魄……\r\n\r\n\u3000\u3000我静静地听着，痴痴地看着，一切仿佛凝固起来，静谧的，幽深的，动听的……\r\n\r\n\u3000\u3000忽然一束灯光出现在水田中，他四处张望着，寻觅着，搜索着……不一会儿，他好像发现了什么似的，灯光也不再惊疑不定，此时此刻他俨然一个狙击手瞄准目标一样，全神贯注，雷打不动……\r\n\r\n\u3000\u3000我的心也随之紧张起来，他在干什么？难道又有……不会的，我立刻否定了心中的猜疑，继续看着，祈祷着，希望刚才的那个假设永远也不会成为现实……\r\n\r\n\u3000\u3000说时迟，那时快，只见那灯光跃动了一下，“他扑上去了！” 我的心揪得更紧了。紧接着刚才那优美绝伦的蛙群大合奏没有了，只剩下那杂乱无章而又略带凄凉的蛙鸣——听着这一切，我的心 “咯噔” 一下，冷冷的，我的思绪变得凌乱不忘初心潮如滚滚江水开始翻涌奔腾——\r\n\r\n\u3000\u3000从那灯光的迅捷可以看得出刚才那人的举动。我的心也随着他的举动而一次次地揪着，甚至揪得很紧…… 结束了，该收场了，灯光离开了，我听到一声声的悲鸣随他而去，黑暗中，我仿佛看到了他那满脸堆着笑的面庞，以及他那鼓鼓的蛇皮袋。\r\n\r\n\u3000\u3000水田里的“杂光”消失了，四野里又恢复了平静，只是不再是 “听取蛙声一片” 热闹场面，只留下那 “苟全性命” 之蛙对逝去者的哀鸣，似乎在吟诵着 “三年羁旅客，今日又南冠…… 欲别故乡难”。\r\n\r\n\u3000\u3000倾听着凄戚的蛙鸣，一股冲动冲击着我的心灵，难道人们就不能坐下来与我一起听蛙吗？难道非要听那蛙痛苦的鸣叫吗？难道还要听那农药带来的痛楚心扉的呻吟吗？难道……\r\n\r\n\u3000\u3000人类啊，让我们都静下心来，一起倾听那欢快的蛙鸣吧，倾听那人与自然的和谐之音吧……';
// commentStore.grade =3;
// commentStore.requirements ='倾听，就是集中精力，开动脑筋，认真听取。一个谦虚好学的人，一个懂得善待他人的人，一个善于反省、强不息的人，永远懂得倾听。\r\n倾听，是亲近自然的方式；倾听，是接受信息的渠道；倾听，是真诚沟通的桥梁；倾听，是净化心灵的艺术倾听自然的声音，倾听美妙的音乐，倾听师长、朋友、同学真挚温暖的话语…… 我们共同在倾听中成长。\r\n请以“倾听”为话题，写一篇文章。\r\n要求：\r\n1.所写内容必须在话题范围之内。\r\n2.立意自定。\r\n3.文体自选（诗歌除外）。\r\n4.题目自拟。\r\n5.不少于 600 字。\r\n6.要求有自己的体验和感悟，不得抄袭；文中不得出现真实的校名人名。';
// commentStore.words_count =699;
// commentStore.upload_time ='2026-02-16 16:41';
////////////////////////////////////////////////////////////////
const props = defineProps({
  essayId: {
    type: [String, Number],
    default: null
  },
  readonly: {
    type: Boolean,
    default: false
  }
})
// 计算属性
const isAnalyzing = computed(() => commentStore.isAnalyzing);
const comment=computed(() => commentStore.comment); 
const jsonComment = computed(() => commentStore.json_comment);
const error = computed(() => commentStore.error);
const essayInfo = computed(() => commentStore.essay);
const grade = computed(() => commentStore.grade);
const requirements = computed(() => commentStore.requirements);
const wordsCount = computed(() => commentStore.words_count);
const uploadTime = computed(() => commentStore.upload_time);

//修改满分值的相关逻辑
const customMaxScore = ref(null) // 存储用户自定义的满分值
// 根据年级获取默认满分值
const getDefaultMaxScore = () => {
  const currentGrade = grade.value || 0
  // 1-9年级：100分；10-12年级：60分
  return currentGrade >= 1 && currentGrade <= 9 ? 100 : 60
}
// 初始化满分值
const defaultMaxScore = getDefaultMaxScore()
if (!customMaxScore.value) {
  customMaxScore.value = defaultMaxScore
}
const ORIGINAL_MAX_SCORE = computed(() => {
  const currentGrade = grade.value || 0
  return currentGrade >= 10 ? 60 : 100
})
const ORIGINAL_SUB_SCORES = computed(() => {
  const isHighSchool = (grade.value || 0) >= 10
  if (isHighSchool) {
    // 60分制的分配：21,15,15,9（总和60）
    return {
      content: 21,
      language: 15,
      structure: 15,
      basic: 9
    }
  } else {
    // 100分制的分配：35,25,25,15（总和100）
    return {
      content: 35,
      language: 25,
      structure: 25,
      basic: 15
    }
  }
})
const displayMaxScore = computed(() => {
  return customMaxScore.value || ORIGINAL_MAX_SCORE
})
// 计算缩放比例
const scaleRatio = computed(() => {
  return displayMaxScore.value / ORIGINAL_MAX_SCORE.value
})
// 计算调整后的各分项满分值
const adjustedMaxScores = computed(() => {
  const original = ORIGINAL_SUB_SCORES.value
  const content = Math.round(original.content * scaleRatio.value)
  const language = Math.round(original.language * scaleRatio.value)
  const structure = Math.round(original.structure * scaleRatio.value)
  const sumOfFirstThree = content + language + structure
  const basic = displayMaxScore.value - sumOfFirstThree
  return {
    content,
    language,
    structure,
    basic: basic >= 0 ? basic : 0 // 确保不为负数
  }
})
// 计算显示的总分（按比例调整）
const displayScore = computed(() => {
  const originalScore = jsonComment.value?.scores?.score || 0
  return Math.round(originalScore * scaleRatio.value)
})
// 计算调整后的各分项分数
const adjustedScores = computed(() => {
  const originalScores = jsonComment.value?.scores || {}
  const content = Math.round((originalScores.content || 0) * scaleRatio.value)
  const language = Math.round((originalScores.language || 0) * scaleRatio.value)
  const structure = Math.round((originalScores.structure || 0) * scaleRatio.value)
  const sumOfFirstThree = content + language + structure
  const basic = displayScore.value - sumOfFirstThree
  return {
    content,
    contentMax: adjustedMaxScores.value.content,
    language,
    languageMax: adjustedMaxScores.value.language,
    structure,
    structureMax: adjustedMaxScores.value.structure,
    basic: basic >= 0 ? basic : 0,
    basicMax: adjustedMaxScores.value.basic
  }
})
// 生成确认框消息
const getConfirmMessage = (oldValue, newValue) => {
  // 计算新总分和各分项分数预览
  const newTotalScore = Math.round((jsonComment.value?.scores?.score || 0) * (newValue / ORIGINAL_MAX_SCORE))
  // 计算新满分值下的各分项满分
  const newContentMax = Math.round(ORIGINAL_SUB_SCORES.content * newValue / ORIGINAL_MAX_SCORE)
  const newLanguageMax = Math.round(ORIGINAL_SUB_SCORES.language * newValue / ORIGINAL_MAX_SCORE)
  const newStructureMax = Math.round(ORIGINAL_SUB_SCORES.structure * newValue / ORIGINAL_MAX_SCORE)
  const sumOfFirstThreeMax = newContentMax + newLanguageMax + newStructureMax
  const newBasicMax = newValue - sumOfFirstThreeMax
  // 计算新分数
  const newContentScore = Math.round((jsonComment.value?.scores?.content || 0) * (newValue / ORIGINAL_MAX_SCORE))
  const newLanguageScore = Math.round((jsonComment.value?.scores?.language || 0) * (newValue / ORIGINAL_MAX_SCORE))
  const newStructureScore = Math.round((jsonComment.value?.scores?.structure || 0) * (newValue / ORIGINAL_MAX_SCORE))
  const sumOfFirstThreeScore = newContentScore + newLanguageScore + newStructureScore
  const newBasicScore = newTotalScore - sumOfFirstThreeScore
  return `确定要将满分值从 ${oldValue} 分改为 ${newValue} 分吗？\n\n` +
    `调整后分数预览：\n` +
    `总分：${displayScore.value} → ${newTotalScore}\n` +
    `内容具体：${adjustedScores.value.content}/${adjustedMaxScores.value.content} → ${newContentScore}/${newContentMax}\n` +
    `语言表达：${adjustedScores.value.language}/${adjustedMaxScores.value.language} → ${newLanguageScore}/${newLanguageMax}\n` +
    `逻辑规范：${adjustedScores.value.structure}/${adjustedMaxScores.value.structure} → ${newStructureScore}/${newStructureMax}\n` +
    `基础规范：${adjustedScores.value.basic}/${adjustedMaxScores.value.basic} → ${newBasicScore}/${newBasicMax}`
}
// 处理满分值变更
const handleMaxScoreChange = (newValue) => {
  // 这里可以添加额外的处理逻辑，比如记录日志等
  console.log('满分值已变更为:', newValue)
}

const formatTime = (timeStr) => {
  if (!timeStr) return '';
  const date = new Date(timeStr);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const handleRetry = () => {
if (essayInfo.value) {
  commentStore.startAnalysis(essayInfo.value);
  ElMessage.info('已重新开始分析');
} else {
  router.push('/');
}
};

// 获取评分等级
const getScoreLevel = (score) => {
  const maxScore = ORIGINAL_MAX_SCORE.value
  // 计算百分比用于渐变色判断
  const percentage = (score / maxScore) * 100
  if (percentage >= 88) return '优秀'
  if (percentage >= 75) return '良好'
  if (percentage >= 60) return '及格'
  return '待提升'
}
//等级样式
const scoreLevelStyle = computed(() => {
  const score = jsonComment.value?.scores?.score || 0;
  const level = getScoreLevel(score);
  
  const styles = {
    '优秀': {
      background: 'linear-gradient(135deg, #67c23a, #529b2e)',
      color: 'white',
      boxShadow: '0 4px 12px rgba(103, 194, 58, 0.4)'
    },
    '良好': {
      background: 'linear-gradient(135deg, #409eff, #1970c7)',
      color: 'white',
      boxShadow: '0 4px 12px rgba(64, 158, 255, 0.4)'
    },
    '及格': {
      background: 'linear-gradient(135deg, #e6a23c, #b88230)',
      color: 'white',
      boxShadow: '0 4px 12px rgba(230, 162, 60, 0.4)'
    },
    '待提升': {
      background: 'linear-gradient(135deg, #f56c6c, #c45656)',
      color: 'white',
      boxShadow: '0 4px 12px rgba(245, 108, 108, 0.4)'
    }
  };
  
  return styles[level] || styles['待提升'];
});

// 关键改动1：计算总分对应的圆环样式
const scoreCircleStyle = computed(() => {
  const score = jsonComment.value?.scores?.score || 0;
  const maxScore = ORIGINAL_MAX_SCORE.value
  // 计算百分比用于渐变色判断
  const percentage = (score / maxScore) * 100
  let gradient = '';
  // 分三个区间设置不同渐变色
  if (percentage < 60) {
    // 不及格：红橙渐变
    gradient = 'linear-gradient(135deg, #f52a2a, #fa8c16)';
  } else if (percentage >= 60 && percentage < 90) {
    // 良好：黄蓝渐变
    gradient = 'linear-gradient(135deg, #e6a23c, #409eff)';
  } else {
    // 优秀：绿蓝渐变
    gradient = 'linear-gradient(135deg, #409eff, #67c23a)';
  }
  return {
    background: gradient
  };
});

const loadHistoryDetail = async (essayId) => {
  try {
    // 调用API获取历史记录详情
    const res = await historyApi.getHistoryDetail(essayId);
    console.log('历史记录详情接口返回:', res);
    if (res.data.code === 200) {
      const data = res.data.data;
      
      // 更新 store 中的各个字段
      commentStore.essay=data.essay.content || "";  // 作文内容
      commentStore.grade=data.essay.grade || 0; 
      commentStore.requirements=data.essay.requirement || "";
      commentStore.words_count=data.essay.word_count || 0 ;  // 作文内容
      commentStore.upload_time=data.essay.upload_date || ''; 
      commentStore.comment=data.comment.details || ''; 
      commentStore.json_comment= {
        scores: data.comment.scores || {},  // scores 是 JSON 格式
        sum: data.comment.sum || ''         // sum 是字符串
      };
      
      // 如果有分析结果
      if (data.analysis_result) {
        // 如果 analysis_result 是 JSON 字符串，需要解析
        if (typeof data.analysis_result === 'string') {
          const analysisResult = JSON.parse(data.analysis_result);
          commentStore.setComment(analysisResult.comment || '');
          commentStore.setJsonComment(analysisResult);
        } else {
          // 如果已经是对象
          commentStore.setComment(data.analysis_result.comment || '');
          commentStore.setJsonComment(data.analysis_result);
        }
      }
    } else {
      ElMessage.error(res.data.message || '加载失败');
    }
  } catch (error) {
    console.error('加载历史记录详情失败:', error);
    ElMessage.error('加载历史记录详情失败');
  } finally {
    commentStore.isAnalyzing=false;
  }
}

watch(() => props.essayId, (newId) => {
  if (newId) {
    console.log("111111111111111111111essayid:", newId);
    
    loadHistoryDetail(newId)  // 直接使用已有的加载函数
  }
}, { immediate: true });

// 页面挂载时监听流式分析
onMounted(async () => {
  // 如果没有 essayId，才处理原有的逻辑
  if (!props.essayId) {
    const historyId = route.query.historyId
    if (historyId) {
      await loadHistoryDetail(historyId)
    } else if (commentStore.streamPromise) {
      try {
        await commentStore.streamPromise;
        ElMessage.success('作文分析完成！');
      } catch (err) {
        if (err) {
          ElMessage.error(`分析失败：${err?.message || '未知错误'}`);
        }
      }
    }
  }
});
</script>

<style scoped>
/* 样式保持不变，但添加预格式化文本 */
.analysis-wrapper {
  width: 100%;
  min-height: 300px;
  content-visibility: auto;  /* 强制渲染 */
}

.dashboard-content {
padding: 24px;
height: 100%;
box-sizing: border-box;
background-color: #f5f7fa;
}

.error-card {
padding: 20px;
background: #fef0f0;
border: 1px solid #fdb9b9;
border-radius: 8px;
display: flex;
align-items: center;
gap: 12px;
margin-bottom: 20px;
}

.error-icon {
color: #f56c6c;
font-size: 24px;
}

.error-text {
flex: 1;
color: #f56c6c;
font-size: 14px;
}

.essay-info-panel {
 margin-bottom: 20px;
 box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}


:deep(.el-collapse-item__header) {
  padding-right: 0 !important;
}

/* 箭头设置 */
:deep(.el-collapse-item__arrow) {
  margin-right: 8px !important; /* 箭头和标题文字的间距 */
  margin-left: 0 !important;    /* 移除箭头默认的左边距 */
}

/* 下拉框的标题 */
.essay-title-bold {
  padding-left: 16px;
  font-size: 15px; /* 字号放大（默认一般14px，可按需调18px/20px） */
  font-weight: bold; /* 加粗（也可写font-weight: 700） */
  color: #2c3e50; /* 可选：加深字体颜色，更醒目 */
}

/* 下拉框的作文内容 */
.essay-content {
  padding: 16px;
  line-height: 1.8;
  color: #606266;
  white-space: pre-wrap;
  position: relative;
}

/* 将上传时间定位到右上角 */
.essay-content .uploadTime {
  position: absolute;
  top: 16px;
  right: 16px;
  color: #909399;
  font-size: 13px;
  background: #fff; /* 加背景避免文字重叠 */
  padding-left: 8px;
}

.essay-info{
  text-align: right;
  color: #909399;
  font-size: 13px;
  margin:30px 16px 0 16px;
}

.essay-info .grade{
  margin-right: 10px;
}
/* 作文基础信息描述列表 */
.essay-requirements {
  padding: 16px;
  line-height: 1.8;
  color: #606266;
  white-space: pre-wrap;
}

/* 总分卡片  */
.total-score-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  display: flex;
  align-items: flex-start; /* 改为顶部对齐 */
  gap: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  flex-wrap: wrap;
  position: relative;
}
/* 将圆圈和等级文字放在一个容器中 */
.score-circle-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px; /* 圆圈和文字的间距 */
  margin-top: 15px;
}
.score-circle {
width: 110px;
height: 110px;
border-radius: 50%;
background: linear-gradient(135deg, #409eff, #67c23a);
display: flex;
flex-direction: column;
align-items: center;
justify-content: center;
color: #fff;
}

.score-num {
font-size: 36px;
font-weight: bold;
line-height: 1;
}
.num{
font-size: 13px;
margin-top:10px;
}
.score-level {
  font-size: 18px;
  font-weight: 600;
  padding: 6px 24px;
  border-radius: 40px;
  letter-spacing: 1px;
  transition: all 0.3s ease;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.scores-wrapper {
  flex: 1;
  position: relative;
}

.max-score-header {
  position: absolute;
  top: -10px;
  right: -12px;
  z-index: 5;
}
/* 调整子分数网格的样式 */
.sub-scores {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-top: 50px;
}

.sub-score-item {
display: flex;
justify-content: space-between;
align-items: center;
padding: 12px;
background: #f8f9fa;
border-radius: 6px;
}

.sub-score-item .label {
color: #303133;
font-size: 14px;
}

.sub-score-item .value {
color: #409eff;
font-weight: 600;
font-size: 16px;
}
/* 语言表达项的特殊样式，用于定位满分值标签 */
.sub-score-item:nth-child(2) {
  position: relative;
}
.summary-comment {
flex: 2;
padding-left: 24px;
border-left: 1px solid #e6e6e6;
}

.summary-comment h4 {
margin: 0 0 8px 0;
color: #303133;
font-size: 16px;
}

.summary-comment p {
color: #606266;
line-height: 1.8;
margin: 0;
}

.real-time-content {
background: #fff;
border-radius: 8px;
padding: 20px;
box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.content-header {
display: flex;
justify-content: space-between;
align-items: center;
margin-bottom: 16px;
padding-bottom: 8px;
border-bottom: 1px solid #e6e6e6;
}

.content-header h3 {
margin: 0;
color: #303133;
font-size: 18px;
}

.content-body {
min-height: 300px;
position: relative;
}

.loading-text {
padding: 10px 0;
width: 100%;
}

.empty-analysis {
display: flex;
align-items: center;
justify-content: center;
gap: 8px;
height: 300px;
color: #909399;
font-size: 14px;
}

.empty-state {
display: flex;
flex-direction: column;
align-items: center;
justify-content: center;
height: 60vh;
color: #909399;
}

.upload_btn {
  margin-top: 20px;
  width: 200px;
  font-size: 16px;
}
</style>