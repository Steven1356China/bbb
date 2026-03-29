<template>
  <div class="problems-page">
    <div class="container">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold">题库</h1>
        <button v-if="isAdmin" @click="showCreateModal = true" class="btn btn-primary">
          <i class="fas fa-plus mr-2"></i>创建题目
        </button>
      </div>
      
      <!-- 搜索和筛选 -->
      <div class="filters mb-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <input
              v-model="search"
              placeholder="搜索题目..."
              class="input"
              @input="debouncedSearch"
            />
          </div>
          <div>
            <select v-model="difficulty" class="input" @change="loadProblems">
              <option value="">全部难度</option>
              <option value="easy">简单</option>
              <option value="medium">中等</option>
              <option value="hard">困难</option>
            </select>
          </div>
          <div>
            <select v-model="tag" class="input" @change="loadProblems">
              <option value="">全部标签</option>
              <option v-for="t in tags" :key="t" :value="t">{{ t }}</option>
            </select>
          </div>
          <div>
            <select v-model="status" class="input" @change="loadProblems">
              <option value="">全部状态</option>
              <option value="solved">已解决</option>
              <option value="attempted">尝试过</option>
              <option value="unsolved">未解决</option>
            </select>
          </div>
        </div>
      </div>
      
      <!-- 题目列表 -->
      <div class="problems-list">
        <div v-if="loading" class="text-center py-8">
          <i class="fas fa-spinner fa-spin text-2xl text-primary"></i>
        </div>
        
        <div v-else-if="problems.length === 0" class="text-center py-8 text-gray-500">
          暂无题目
        </div>
        
        <ProblemCard
          v-else
          v-for="problem in problems"
          :key="problem.id"
          :problem="problem"
          class="mb-3"
        />
      </div>
      
      <!-- 分页 -->
      <div v-if="totalPages > 1" class="flex justify-center mt-6">
        <nav class="flex gap-2">
          <button
            v-for="page in pages"
            :key="page"
            @click="gotoPage(page)"
            :class="['btn', page === currentPage ? 'btn-primary' : 'btn-outline']"
          >
            {{ page }}
          </button>
        </nav>
      </div>
    </div>
    
    <!-- 创建题目模态框 -->
    <CreateProblemModal
      v-if="showCreateModal"
      @close="showCreateModal = false"
      @created="handleProblemCreated"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import ProblemCard from '../components/ProblemCard.vue'
import CreateProblemModal from '../components/CreateProblemModal.vue'
import api from '../api'

export default {
  name: 'Problems',
  components: {
    ProblemCard,
    CreateProblemModal
  },
  setup() {
    const store = useStore()
    const search = ref('')
    const difficulty = ref('')
    const tag = ref('')
    const status = ref('')
    const problems = ref([])
    const tags = ref([])
    const loading = ref(true)
    const currentPage = ref(1)
    const totalPages = ref(1)
    const showCreateModal = ref(false)
    
    const isAdmin = computed(() => store.state.user?.role === 'admin')
    
    const pages = computed(() => {
      const pageCount = 5
      const start = Math.max(1, currentPage.value - Math.floor(pageCount / 2))
      const end = Math.min(totalPages.value, start + pageCount - 1)
      return Array.from({ length: end - start + 1 }, (_, i) => start + i)
    })
    
    const loadProblems = async () => {
      loading.value = true
      try {
        const params = {
          page: currentPage.value,
          per_page: 20,
          difficulty: difficulty.value,
          tag: tag.value,
          search: search.value
        }
        
        const response = await api.get('/problems', { params })
        problems.value = response.data.problems
        totalPages.value = response.data.pages
      } catch (error) {
        console.error('加载题目失败:', error)
      } finally {
        loading.value = false
      }
    }
    
    const loadTags = async () => {
      try {
        const response = await api.get('/tags')
        tags.value = response.data
      } catch (error) {
        console.error('加载标签失败:', error)
      }
    }
    
    const debouncedSearch = debounce(() => {
      currentPage.value = 1
      loadProblems()
    }, 500)
    
    const gotoPage = (page) => {
      currentPage.value = page
      loadProblems()
    }
    
    const handleProblemCreated = () => {
      showCreateModal.value = false
      loadProblems()
    }
    
    onMounted(() => {
      loadProblems()
      loadTags()
    })
    
    return {
      search,
      difficulty,
      tag,
      status,
      problems,
      tags,
      loading,
      currentPage,
      totalPages,
      showCreateModal,
      isAdmin,
      pages,
      loadProblems,
      debouncedSearch,
      gotoPage,
      handleProblemCreated
    }
  }
}

function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}
</script>

<style scoped>
.grid {
  display: grid;
}
</style>
