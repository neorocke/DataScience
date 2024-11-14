// src/components/StatusDescriptions.js
import React from 'react';
import { InformationCircleIcon } from '@heroicons/react/24/outline';
import { motion } from 'framer-motion';

const statusDescriptions = {
  STATUS_OK: '정상 응답',
  STATUS_REDIRECT: '리다이렉트 발생',
  STATUS_CLIENT_ERROR: '클라이언트 오류 (4xx 상태 코드)',
  STATUS_SERVER_ERROR: '서버 오류 (5xx 상태 코드)',
  STATUS_EMPTY_CONTENT: '빈 페이지 감지',
  STATUS_YOUTUBE_PRIVATE: '유튜브 비공개 동영상 감지',
  STATUS_YOUTUBE_DELETED: '유튜브 삭제된 동영상 감지',
  STATUS_YOUTUBE_AGE_RESTRICTED: '유튜브 연령 제한 동영상 감지',
  STATUS_YOUTUBE_REGION_BLOCKED: '유튜브 지역 제한 동영상 감지',
  STATUS_YOUTUBE_UNAVAILABLE: '유튜브 동영상 사용 불가 감지',
  STATUS_ERROR: '기타 처리 중 오류 발생',
};

function StatusDescriptions() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="card"
    >
      <h2 className="text-xl font-semibold mb-4 flex items-center">
        <InformationCircleIcon className="w-6 h-6 mr-2 text-primary" />
        상태 코드 설명
      </h2>
      <p>이 프로젝트에서 사용하는 상태 코드에 대한 설명입니다.</p>
      <ul className="mt-4 space-y-2">
        {Object.entries(statusDescriptions).map(([code, description]) => (
          <li key={code} className="flex items-start">
            <span className="font-medium text-gray-900 dark:text-gray-300">{code}:</span>
            <span className="ml-2 text-gray-700 dark:text-gray-400">{description}</span>
          </li>
        ))}
      </ul>
    </motion.div>
  );
}

export default StatusDescriptions;
