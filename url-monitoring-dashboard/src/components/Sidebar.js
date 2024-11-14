// src/components/Sidebar.js
import { useEffect } from 'react';
import useStore from '../store/useStore';

function Sidebar() {
  const {
    availableStatuses,
    selectedStatuses,
    setSelectedStatuses,
    filterData,
    setSearchQuery,
  } = useStore();

  useEffect(() => {
    // availableStatuses가 변경되었을 때, selectedStatuses가 비어있다면 모든 상태를 선택하도록 설정
    if (availableStatuses.length > 0 && selectedStatuses.length === 0) {
      setSelectedStatuses(availableStatuses);
      filterData();
    }
  }, [availableStatuses, selectedStatuses, setSelectedStatuses, filterData]);

  const handleStatusChange = (e) => {
    const { value, checked } = e.target;
    setSelectedStatuses((prev) =>
      checked ? [...prev, value] : prev.filter((status) => status !== value)
    );
    filterData();
  };

  const handleSearch = (e) => {
    setSearchQuery(e.target.value);
    filterData();
  };

  // availableStatuses와 selectedStatuses가 배열인지 확인
  if (!Array.isArray(availableStatuses)) {
    console.error('availableStatuses is not an array:', availableStatuses);
    return null;
  }

  if (!Array.isArray(selectedStatuses)) {
    console.error('selectedStatuses is not an array:', selectedStatuses);
    return null;
  }

  return (
    <aside className="w-64 bg-gray-100 dark:bg-gray-900 p-4">
      <h2 className="text-xl font-semibold mb-4">필터</h2>
      <div>
        <h3 className="font-medium">상태 선택</h3>
        {availableStatuses.map((status) => (
          <div key={status} className="flex items-center mt-2">
            <input
              type="checkbox"
              value={status}
              onChange={handleStatusChange}
              checked={selectedStatuses.includes(status)}
              className="form-checkbox h-4 w-4 text-primary"
            />
            <label className="ml-2 text-gray-700 dark:text-gray-300">{status}</label>
          </div>
        ))}
      </div>
      <div className="mt-6">
        <h3 className="font-medium">검색</h3>
        <input
          type="text"
          placeholder="ID 또는 URL 검색"
          onChange={handleSearch}
          className="w-full p-2 border rounded mt-2 focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>
    </aside>
  );
}

export default Sidebar;
