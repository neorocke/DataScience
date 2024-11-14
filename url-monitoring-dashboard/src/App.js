// src/App.js
import React, { useEffect, useState } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Tabs from './components/Tabs';
import useStore from './store/useStore';
import { loadDataFromExcel } from './utils/loadData';
import axios from 'axios';
import './index.css';

function App() {
  const { setData, setAvailableStatuses, setSelectedStatuses } = useStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get('/data/processed_data.xlsx', {
          responseType: 'arraybuffer',
        });
        const data = await loadDataFromExcel(new Blob([response.data]));
        setData(data);

        // 전체 상태 목록 설정
        const uniqueStatuses = [...new Set(data.map((item) => item.status))];
        setAvailableStatuses(uniqueStatuses);

        // 초기 선택 상태는 모든 상태를 선택하도록 설정
        setSelectedStatuses(uniqueStatuses);
      } catch (error) {
        console.error('데이터 로딩 중 오류 발생:', error);
        setError('데이터를 불러오는 중 오류가 발생했습니다.');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [setData, setAvailableStatuses, setSelectedStatuses]);

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-800">
      <Sidebar />
      <div className="flex-1 overflow-auto">
        <Header />
        <main className="p-4">
          {loading ? (
            <div className="flex justify-center items-center h-full">
              <div className="loader ease-linear rounded-full border-8 border-t-8 border-gray-200 h-32 w-32"></div>
            </div>
          ) : error ? (
            <div className="text-red-500">{error}</div>
          ) : (
            <Tabs />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
