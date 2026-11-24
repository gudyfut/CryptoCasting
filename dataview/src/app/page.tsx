import Panorama from '@/components/panorama/Panorama';
import { carregarPanorama, disponibilidadeFontes } from '@/lib/panorama-servidor';
import { carregarEvolucao } from '@/lib/evolucao-servidor';
import { carregarFichas } from '@/lib/fichas-servidor';
export const dynamic = 'force-dynamic';
export default async function Pagina({ searchParams }: { searchParams: Promise<{ etapa?: string; aba?: string; vista?: string }> }) {
  const parametros = await searchParams;
  const [disponibilidade, evolucao, fichas, panorama] = await Promise.all([disponibilidadeFontes(), carregarEvolucao(), carregarFichas(), carregarPanorama()]);
  return <Panorama dados={panorama} disponibilidade={disponibilidade} evolucao={evolucao} fichas={fichas} inicial={parametros} />;
}
