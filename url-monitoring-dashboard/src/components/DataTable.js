// src/components/DataTable.js
import React from 'react';
import { AgGridReact } from 'ag-grid-react';
import useStore from '../store/useStore';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import DetailView from './DetailView';
import { motion } from 'framer-motion';

function DataTable() {
  const { filteredData, setSelectedRow } = useStore();
  const gridRef = React.useRef();

  const columns = [
    { headerName: 'ID', field: 'id', sortable: true, filter: true },
    { headerName: 'URL', field: 'url', sortable: true, filter: true },
    { headerName: 'Status', field: 'status', sortable: true, filter: true },
    { headerName: 'Last Checked', field: 'last_checked', sortable: true, filter: true },
    { headerName: 'Log', field: 'log', sortable: true, filter: true },
  ];

  const onRowClicked = (event) => {
    setSelectedRow(event.data);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col md:flex-row"
    >
      <div className="ag-theme-alpine" style={{ height: 600, width: '100%' }}>
        <AgGridReact
          ref={gridRef}
          rowData={filteredData}
          columnDefs={columns}
          rowSelection="single"
          onRowClicked={onRowClicked}
          pagination={true}
          paginationPageSize={35}
          animateRows={true}
          domLayout="autoHeight"
        />
      </div>
      <div className="w-full md:w-1/2 p-4">
        <DetailView />
      </div>
    </motion.div>
  );
}

export default DataTable;
