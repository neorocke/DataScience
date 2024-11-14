// src/components/Tabs.js
import { Tab } from '@headlessui/react';
import classNames from 'classnames';
import DataTable from './DataTable';
import Charts from './Charts';
import ImageGallery from './ImageGallery';
import StatusDescriptions from './StatusDescriptions';

function TabsComponent() {
  return (
    <Tab.Group>
      <Tab.List className="flex p-1 space-x-1 bg-blue-900/20 rounded-xl">
        {['데이터 필터링', '요약 차트 보기', '이미지 전체 보기', '상태 코드 설명'].map((tab) => (
          <Tab
            key={tab}
            className={({ selected }) =>
              classNames(
                'w-full py-2.5 text-sm leading-5 font-medium text-blue-700 rounded-lg',
                selected
                  ? 'bg-white shadow'
                  : 'text-blue-100 hover:bg-white/[0.12] hover:text-white'
              )
            }
          >
            {tab}
          </Tab>
        ))}
      </Tab.List>
      <Tab.Panels className="mt-2">
        <Tab.Panel>
          <DataTable />
        </Tab.Panel>
        <Tab.Panel>
          <Charts />
        </Tab.Panel>
        <Tab.Panel>
          <ImageGallery />
        </Tab.Panel>
        <Tab.Panel>
          <StatusDescriptions />
        </Tab.Panel>
      </Tab.Panels>
    </Tab.Group>
  );
}

export default TabsComponent;
