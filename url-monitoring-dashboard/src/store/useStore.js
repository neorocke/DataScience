// src/store/useStore.js
import { create } from 'zustand';

const useStore = create((set) => ({
  // 데이터 상태
  data: [],
  filteredData: [],
  
  // 상태 필터링을 위한 전체 및 선택된 상태 목록
  availableStatuses: [],
  selectedStatuses: [],
  
  // 검색 쿼리 및 선택된 행
  searchQuery: '',
  selectedRow: null,
  
  // 사이드바 가시성 상태
  isSidebarOpen: false,
  
  // 상태 설정 함수들
  setData: (data) => set({ data, filteredData: data }),
  setAvailableStatuses: (statuses) => set({ availableStatuses: statuses }),
  
  setSelectedStatuses: (updater) =>
    typeof updater === 'function'
      ? set((state) => ({ selectedStatuses: updater(state.selectedStatuses) }))
      : set({ selectedStatuses: updater }),
  
  setSearchQuery: (query) => set({ searchQuery: query }),
  setSelectedRow: (row) => set({ selectedRow: row }),
  
  // 사이드바 토글 함수
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  closeSidebar: () => set({ isSidebarOpen: false }),
  
  // 데이터 필터링 함수
  filterData: () =>
    set((state) => ({
      filteredData: state.data.filter(
        (item) =>
          Array.isArray(state.selectedStatuses) &&
          state.selectedStatuses.includes(item.status) &&
          (item.id.toString().includes(state.searchQuery) ||
            item.url.includes(state.searchQuery))
      ),
    })),
}));

export default useStore;
