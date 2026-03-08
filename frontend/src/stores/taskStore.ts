import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type TaskStatus = 
  | 'pending'
  | 'parsing'
  | 'generating'
  | 'validating'
  | 'executing'
  | 'exporting'
  | 'completed'
  | 'failed'

export interface Task {
  id: string
  user_description: string
  status: TaskStatus
  volume?: number
  bounding_box?: {
    x: number
    y: number
    z: number
  }
  error_message?: string
  step_file_url?: string
  stl_file_url?: string
  created_at: string
  updated_at?: string
}

interface TaskStore {
  tasks: Task[]
  currentTask: Task | null
  isLoading: boolean
  addTask: (task: Task) => void
  updateTask: (task: Task) => void
  setCurrentTask: (task: Task | null) => void
  setLoading: (loading: boolean) => void
  fetchTasks: () => Promise<void>
}

export const useTaskStore = create<TaskStore>()(
  persist(
    (set, get) => ({
      tasks: [],
      currentTask: null,
      isLoading: false,

      addTask: (task) => {
        set((state) => ({
          tasks: [task, ...state.tasks]
        }))
      },

      updateTask: (updatedTask) => {
        set((state) => ({
          tasks: state.tasks.map((t) =>
            t.id === updatedTask.id ? updatedTask : t
          ),
          currentTask:
            state.currentTask?.id === updatedTask.id
              ? updatedTask
              : state.currentTask
        }))
      },

      setCurrentTask: (task) => set({ currentTask: task }),
      setLoading: (loading) => set({ isLoading: loading }),

      fetchTasks: async () => {
        try {
          const response = await fetch('/api/v1/tasks/')
          if (response.ok) {
            const tasks = await response.json()
            set({ tasks })
          }
        } catch (error) {
          console.error('Failed to fetch tasks:', error)
        }
      }
    }),
    {
      name: 'text-to-cad-tasks'
    }
  )
)
