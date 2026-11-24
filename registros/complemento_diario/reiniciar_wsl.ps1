$ErrorActionPreference = 'Stop'
$destinoRegistro = 'C:\Users\MuriloRFM\Documents\GitHub\CryptoCasting\registros\complemento_diario\reinicio_wsl_administrador.json'
$reciboReinicio = @{ inicio = (Get-Date).ToUniversalTime().ToString('o'); situacao = 'iniciando'; autorizado_usuario = $true }
try {
    $servicoWsl = Get-Service -Name WslService
    $servicoWsl.Stop()
    try { $servicoWsl.WaitForStatus('Stopped', [TimeSpan]::FromSeconds(20)) }
    catch {
        $processoServicoWsl = Get-Process -Name wslservice -ErrorAction Stop
        $reciboReinicio.pid_servico_encerrado = $processoServicoWsl.Id
        $processoServicoWsl | Stop-Process -Force -ErrorAction Stop
        Start-Sleep -Seconds 2
    }
    Start-Service -Name WslService
    $servicoWsl = Get-Service -Name WslService
    $servicoWsl.WaitForStatus('Running', [TimeSpan]::FromSeconds(20))
    $reciboReinicio.situacao = 'servico_reiniciado'
} catch {
    $reciboReinicio.situacao = 'falha'
    $reciboReinicio.erro = $_.Exception.Message
} finally {
    $reciboReinicio.fim = (Get-Date).ToUniversalTime().ToString('o')
    $reciboReinicio | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $destinoRegistro -Encoding utf8
}
