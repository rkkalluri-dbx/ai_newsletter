/**
 * Zustand store for global application state
 */
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

// Types
export interface FilterState {
  // Project filters
  projectStatus: string | null;
  projectVendor: string | null;
  projectRegion: string | null;
  projectPriority: string | null;
  projectSearch: string;
  projectDateRange: { from: string | null; to: string | null };

  // Alert filters
  alertSeverity: string | null;
  alertType: string | null;
  alertAcknowledged: boolean | null;

  // Gantt filters
  ganttVendor: string | null;
  ganttRegion: string | null;
  ganttStatus: string | null;
}

export interface UIState {
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;
  selectedProjectId: string | null;
  selectedVendorId: string | null;
  darkMode: boolean;
}

export interface NotificationState {
  notifications: Array<{
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    message: string;
    timestamp: number;
  }>;
}

interface AppState extends FilterState, UIState, NotificationState {
  // Filter actions
  setProjectFilter: (key: keyof FilterState, value: unknown) => void;
  setAlertFilter: (key: keyof FilterState, value: unknown) => void;
  setGanttFilter: (key: keyof FilterState, value: unknown) => void;
  resetProjectFilters: () => void;
  resetAlertFilters: () => void;
  resetGanttFilters: () => void;
  resetAllFilters: () => void;

  // UI actions
  toggleSidebar: () => void;
  toggleSidebarCollapse: () => void;
  setSelectedProject: (id: string | null) => void;
  setSelectedVendor: (id: string | null) => void;
  toggleDarkMode: () => void;

  // Notification actions
  addNotification: (type: NotificationState['notifications'][0]['type'], message: string) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

const initialFilterState: FilterState = {
  projectStatus: null,
  projectVendor: null,
  projectRegion: null,
  projectPriority: null,
  projectSearch: '',
  projectDateRange: { from: null, to: null },
  alertSeverity: null,
  alertType: null,
  alertAcknowledged: null,
  ganttVendor: null,
  ganttRegion: null,
  ganttStatus: null,
};

const initialUIState: UIState = {
  sidebarOpen: true,
  sidebarCollapsed: false,
  selectedProjectId: null,
  selectedVendorId: null,
  darkMode: false,
};

const initialNotificationState: NotificationState = {
  notifications: [],
};

export const useAppStore = create<AppState>()(
  devtools(
    persist(
      (set) => ({
        // Initial state
        ...initialFilterState,
        ...initialUIState,
        ...initialNotificationState,

        // Filter actions
        setProjectFilter: (key, value) =>
          set((state) => ({ ...state, [key]: value }), false, 'setProjectFilter'),

        setAlertFilter: (key, value) =>
          set((state) => ({ ...state, [key]: value }), false, 'setAlertFilter'),

        setGanttFilter: (key, value) =>
          set((state) => ({ ...state, [key]: value }), false, 'setGanttFilter'),

        resetProjectFilters: () =>
          set(
            {
              projectStatus: null,
              projectVendor: null,
              projectRegion: null,
              projectPriority: null,
              projectSearch: '',
              projectDateRange: { from: null, to: null },
            },
            false,
            'resetProjectFilters'
          ),

        resetAlertFilters: () =>
          set(
            {
              alertSeverity: null,
              alertType: null,
              alertAcknowledged: null,
            },
            false,
            'resetAlertFilters'
          ),

        resetGanttFilters: () =>
          set(
            {
              ganttVendor: null,
              ganttRegion: null,
              ganttStatus: null,
            },
            false,
            'resetGanttFilters'
          ),

        resetAllFilters: () => set(initialFilterState, false, 'resetAllFilters'),

        // UI actions
        toggleSidebar: () =>
          set((state) => ({ sidebarOpen: !state.sidebarOpen }), false, 'toggleSidebar'),

        toggleSidebarCollapse: () =>
          set(
            (state) => ({ sidebarCollapsed: !state.sidebarCollapsed }),
            false,
            'toggleSidebarCollapse'
          ),

        setSelectedProject: (id) =>
          set({ selectedProjectId: id }, false, 'setSelectedProject'),

        setSelectedVendor: (id) =>
          set({ selectedVendorId: id }, false, 'setSelectedVendor'),

        toggleDarkMode: () =>
          set((state) => ({ darkMode: !state.darkMode }), false, 'toggleDarkMode'),

        // Notification actions
        addNotification: (type, message) =>
          set(
            (state) => ({
              notifications: [
                ...state.notifications,
                {
                  id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                  type,
                  message,
                  timestamp: Date.now(),
                },
              ],
            }),
            false,
            'addNotification'
          ),

        removeNotification: (id) =>
          set(
            (state) => ({
              notifications: state.notifications.filter((n) => n.id !== id),
            }),
            false,
            'removeNotification'
          ),

        clearNotifications: () =>
          set({ notifications: [] }, false, 'clearNotifications'),
      }),
      {
        name: 'gpc-reliability-storage',
        partialize: (state) => ({
          darkMode: state.darkMode,
          sidebarCollapsed: state.sidebarCollapsed,
        }),
      }
    ),
    { name: 'AppStore' }
  )
);

// Selector hooks for performance optimization
export const useProjectFilters = () =>
  useAppStore((state) => ({
    status: state.projectStatus,
    vendor_id: state.projectVendor,
    region: state.projectRegion,
    priority: state.projectPriority,
    search: state.projectSearch,
    date_from: state.projectDateRange.from,
    date_to: state.projectDateRange.to,
  }));

export const useAlertFilters = () =>
  useAppStore((state) => ({
    severity: state.alertSeverity,
    alert_type: state.alertType,
    acknowledged: state.alertAcknowledged,
  }));

export const useGanttFilters = () =>
  useAppStore((state) => ({
    vendor_id: state.ganttVendor,
    region: state.ganttRegion,
    status: state.ganttStatus,
  }));

export const useSidebar = () =>
  useAppStore((state) => ({
    open: state.sidebarOpen,
    collapsed: state.sidebarCollapsed,
    toggle: state.toggleSidebar,
    toggleCollapse: state.toggleSidebarCollapse,
  }));

export const useNotifications = () =>
  useAppStore((state) => ({
    notifications: state.notifications,
    add: state.addNotification,
    remove: state.removeNotification,
    clear: state.clearNotifications,
  }));
