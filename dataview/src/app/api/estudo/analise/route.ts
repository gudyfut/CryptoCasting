import {NextRequest,NextResponse} from "next/server";
import {lerPublicacao} from "@/lib/estudo";
export const dynamic="force-dynamic";
export async function GET(req:NextRequest){
  const fase=req.nextUrl.searchParams.get("fase")??"";
  const arquivo=req.nextUrl.searchParams.get("arquivo")??"resumo.json";
  if(!["desenvolvimento","avaliacao"].includes(fase) || !/^(resumo\.json|metricas_por_ajuste\.csv|metricas_medias_seeds\.csv|financeiro\.csv|operacoes\/[A-Za-z0-9_]+\.json)$/.test(arquivo))return NextResponse.json({erro:"Seleção inválida."},{status:400});
  try{
    const corpo=await lerPublicacao(fase,arquivo);
    if(!corpo)return NextResponse.json({erro:"Análise completa ainda não publicada."},{status:404});
    return new NextResponse(corpo,{headers:{"Content-Type":arquivo.endsWith("csv")?"text/csv; charset=utf-8":"application/json; charset=utf-8","Cache-Control":"no-store",...(arquivo.endsWith("csv")?{"Content-Disposition":`attachment; filename="${fase}_${arquivo}"`}:{})}});
  }catch{return NextResponse.json({erro:"Integridade da análise não confirmada."},{status:503});}
}
