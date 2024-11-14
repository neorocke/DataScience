// src/utils/loadData.js
import * as XLSX from 'xlsx';

export const loadDataFromExcel = async (file) => {
  const data = await file.arrayBuffer();
  const workbook = XLSX.read(data);
  const worksheet = workbook.Sheets[workbook.SheetNames[0]];
  const jsonData = XLSX.utils.sheet_to_json(worksheet);
  return jsonData;
};
