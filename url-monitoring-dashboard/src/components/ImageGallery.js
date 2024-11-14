// src/components/ImageGallery.js
import React from 'react';
import useStore from '../store/useStore';
import { motion } from 'framer-motion';

function ImageGallery() {
  const { filteredData } = useStore();

  const images = filteredData.filter((item) => item.screenshot);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="grid grid-cols-1 md:grid-cols-3 gap-4"
    >
      {images.map((item) => (
        <div key={item.id} className="border rounded overflow-hidden shadow-lg">
          <img
            src={item.screenshot}
            alt={`Screenshot of ${item.url}`}
            className="w-full h-48 object-cover"
            loading="lazy"
          />
          <div className="p-2">
            <p>
              <strong>ID:</strong> {item.id}
            </p>
            <p>
              <strong>URL:</strong> {item.url}
            </p>
          </div>
        </div>
      ))}
    </motion.div>
  );
}

export default ImageGallery;
