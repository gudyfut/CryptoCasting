import type {Estado} from "@/lib/estudo";
export default function LinhaAndamento({estado:e,analisesAuditadas}:{estado:Estado;analisesAuditadas:number}){
  const entregas=[
    {titulo:'Preservar o estudo anterior',concluida:!!e.arquivoVerificado,descricao:'Arquivo histórico com manifesto e verificação de integridade.'},
    {titulo:'Fixar o novo desenho',concluida:!!e.execucao,descricao:'Protocolo, configuração e fontes vinculados à identidade da execução; exposição anterior declarada.'},
    {titulo:'Coletar e preparar dados',concluida:!!e.preparacaoAprovada,descricao:'Séries 2021–2025 com lacunas preservadas e alvos terminais rastreáveis.'},
    {titulo:'Qualificar a implementação',concluida:!!e.preparacaoAprovada&&e.piloto,descricao:'Contratos sintéticos, redes CUDA e piloto curto/longo reais verificados.'},
    {titulo:'Concluir o desenvolvimento',concluida:e.desenvolvimento,descricao:'Toda a grade DB1–DB4, incluindo referências, precisa estar auditada.'},
    {titulo:'Executar a avaliação posterior',concluida:e.avaliacao&&e.congelado,descricao:'B1–B4 somente depois do congelamento; mesma metodologia predefinida.'},
    {titulo:'Consolidar e auditar resultados',concluida:analisesAuditadas===2,descricao:'Escores, comparações pareadas, seeds e simulações das duas fases verificadas.'},
    {titulo:'Verificar a apresentação final',concluida:!!e.interfaceAprovada&&analisesAuditadas===2,descricao:'Métricas, filtros, gráficos e explicações conferidos com os resultados completos.'},
  ];
  return <><p className="nota"><b>{entregas.filter(r=>r.concluida).length} de {entregas.length} entregas do protocolo concluídas.</b> Esta é a organização operacional do estudo; não substitui o cronograma acadêmico acordado com o orientador.</p><ol className="etapas">{entregas.map((r,i)=><li key={r.titulo} className={r.concluida?'pronta':''}><b>{i+1}. {r.titulo}<small className="estado-etapa">{r.concluida?'Concluída':'Ainda não concluída'}</small></b><span>{r.descricao}</span></li>)}</ol></>;
}
