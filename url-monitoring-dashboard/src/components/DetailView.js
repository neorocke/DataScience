// src/components/DetailView.js
import useStore from '../store/useStore';
import { motion } from 'framer-motion';
import { PhotoIcon } from '@heroicons/react/24/outline';

function DetailView() {
  const { selectedRow } = useStore();

  if (!selectedRow) {
    return <div>선택된 항목이 없습니다.</div>;
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="card"
    >
      <h3 className="text-lg font-semibold mb-2">선택된 URL 상세 정보</h3>
      <p>
        <strong>ID:</strong> {selectedRow.id}
      </p>
      <p>
        <strong>Status:</strong> {selectedRow.status}
      </p>
      <p>
        <strong>Last Checked:</strong> {selectedRow.last_checked}
      </p>
      <p>
        <strong>Log:</strong> {selectedRow.log}
      </p>
      {selectedRow.screenshot ? (
        <div className="mt-4">
          <h4 className="text-md font-medium mb-2 flex items-center">
            <PhotoIcon className="w-5 h-5 mr-1" />
            스크린샷
          </h4>
          <img
            src={selectedRow.screenshot}
            alt={`Screenshot of ${selectedRow.url}`}
            className="w-full h-auto object-cover rounded"
            loading="lazy"
          />
        </div>
      ) : (
        <div className="mt-4 text-danger">스크린샷을 사용할 수 없습니다.</div>
      )}
    </motion.div>
  );
}

export default DetailView;
