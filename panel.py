import React, { useEffect, useState } from 'react';
import axios from 'axios';

const Dashboard = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    // Her dakika veriyi çek
    const interval = setInterval(() => {
      axios.get('http://localhost:8000/api/matrix').then(res => setData(res.data));
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-gray-900 text-white min-h-screen p-4">
      <h1 className="text-2xl font-bold mb-4">BIST Swing/Intraday Trend & Hacim Sıkışması Patlama Terminali</h1>
      
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="bg-gray-800 text-gray-400">
            <tr>
              <th>Hisse</th>
              <th>Net Güç Skoru</th>
              <th>Sinyal</th>
              <th>Trend Kararı</th>
              <th>15 Dk Sonra Tahmin</th>
              <th>Sıkışma (Comp)</th>
              <th>Hacim (Vol)</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <tr key={i} className="border-b border-gray-700">
                <td className="py-2">{row.hisse}</td>
                <td className="py-2">{row.netGucSkoru}</td>
                <td className={`py-2 ${row.sinyal === 'GÜÇLÜ TREND' ? 'text-green-500' : 'text-yellow-500'}`}>{row.sinyal}</td>
                <td className="py-2">{row.trendKarari}</td>
                <td className="py-2 text-green-400 font-bold">{row.tahmin15dk}</td>
                <td className="py-2">{row.comp}</td>
                <td className="py-2">{row.vol}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Dashboard;
