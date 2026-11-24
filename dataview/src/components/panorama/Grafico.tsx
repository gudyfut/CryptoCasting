'use client';
import dynamic from 'next/dynamic';
import type { EChartsOption } from 'echarts';
const ECharts = dynamic(() => import('echarts-for-react'), { ssr: false, loading: () => <div className="carregando-grafico">Preparando visualização…</div> });
export const cores = ['#24796f', '#de7558', '#8996b6', '#aaa592', '#34445c', '#b99969', '#7e8d6e', '#ab7b94'];
export default function Grafico({ opcoes, altura = 320, aoClicar, rotulo }: { opcoes: EChartsOption; altura?: number; aoClicar?: (e: { dataIndex: number; seriesIndex: number }) => void; rotulo: string }) {
  return <div className="grafico" role="figure" aria-label={rotulo}><ECharts option={{ animationDuration: 400, textStyle: { fontFamily: 'Arial, sans-serif', color: '#697382' }, color: cores, ...opcoes }} notMerge style={{ height: altura, width: '100%' }} onEvents={aoClicar ? { click: aoClicar } : undefined} opts={{ renderer: 'svg' }} /></div>;
}
