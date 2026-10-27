$ErrorActionPreference = 'Stop'
$raizProjeto = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$destinoArquivo = Join-Path $raizProjeto 'arquivo/estudo_barreiras_2026-10-20'
if (Test-Path -LiteralPath $destinoArquivo) { throw 'Arquivo já existe; inspecionar antes de repetir.' }
$pastas = @('analise','barreiras','baseline_ar1','camada_dados','configuracoes','dados','docs','experimentos','historico','modelo','pre_processamento','scripts','tests','tmp')
$itens = $pastas + @('AGENTS.md','plano.md','README.md','requirements.txt','run_barreiras.py','dataview/src','dataview/public','dataview/tests','dataview/scripts','dataview/.dados','dataview/README.md')
$caminhos = @()
foreach ($relativo in $itens) {
  $origem = [IO.Path]::GetFullPath((Join-Path $raizProjeto $relativo))
  $destino = [IO.Path]::GetFullPath((Join-Path $destinoArquivo ('projeto/' + $relativo)))
  if (!$origem.StartsWith($raizProjeto + [IO.Path]::DirectorySeparatorChar) -or !$destino.StartsWith($destinoArquivo + [IO.Path]::DirectorySeparatorChar)) { throw 'Caminho fora da área autorizada.' }
  if (Test-Path -LiteralPath $origem) { $caminhos += [pscustomobject]@{relativo=$relativo;origem=$origem;destino=$destino} }
}
New-Item -ItemType Directory -Path $destinoArquivo | Out-Null
git -C $raizProjeto rev-parse HEAD | Set-Content -LiteralPath (Join-Path $destinoArquivo 'commit_origem.txt') -Encoding utf8
git -C $raizProjeto status --short | Set-Content -LiteralPath (Join-Path $destinoArquivo 'estado_git.txt') -Encoding utf8
$manifesto = @()
foreach ($item in $caminhos) {
  $arquivos = if ((Get-Item -LiteralPath $item.origem).PSIsContainer) { Get-ChildItem -LiteralPath $item.origem -File -Recurse -Force } else { Get-Item -LiteralPath $item.origem }
  foreach ($arquivo in $arquivos) {
    $rel = [IO.Path]::GetRelativePath($raizProjeto, $arquivo.FullName).Replace('\','/')
    $manifesto += [pscustomobject]@{caminho=$rel;bytes=$arquivo.Length;sha256=(Get-FileHash -LiteralPath $arquivo.FullName -Algorithm SHA256).Hash.ToLower()}
  }
  Write-Output ('Inventariado: ' + $item.relativo)
}
$manifesto | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $destinoArquivo 'manifesto_antes.json') -Encoding utf8
foreach ($item in $caminhos) {
  New-Item -ItemType Directory -Force -Path ([IO.Path]::GetDirectoryName($item.destino)) | Out-Null
  Move-Item -LiteralPath $item.origem -Destination $item.destino
  Write-Output ('Arquivado: ' + $item.relativo)
}
# Preservar os arquivos de infraestrutura web que continuarão no projeto ativo.
Get-ChildItem -LiteralPath (Join-Path $raizProjeto 'dataview') -File -Force | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $destinoArquivo ('projeto/dataview/' + $_.Name)) }
Copy-Item -LiteralPath (Join-Path $raizProjeto '.gitignore') -Destination (Join-Path $destinoArquivo 'projeto/.gitignore')
$verificados = 0
foreach ($item in $manifesto) {
  $arquivo = Join-Path $destinoArquivo ('projeto/' + $item.caminho)
  if ((Get-FileHash -LiteralPath $arquivo -Algorithm SHA256).Hash.ToLower() -ne $item.sha256) { throw ('Divergência: ' + $item.caminho) }
  $verificados++
}
[pscustomobject]@{status='preservado_verificado';arquivos=$verificados;bytes=($manifesto | Measure-Object bytes -Sum).Sum;verificado_utc=[DateTime]::UtcNow.ToString('o');observacao='Movimentação local com hashes antes/depois; não é cópia externa de segurança.'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $destinoArquivo 'verificacao.json') -Encoding utf8
Write-Output ('Preservação verificada: ' + $verificados + ' arquivos.')
