$ErrorActionPreference = 'Stop'
$raizProjeto = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$registro = Join-Path $raizProjeto 'registros/fechamento_ramos_diarios'
Set-Location -LiteralPath $raizProjeto
if (Test-Path -LiteralPath (Join-Path $registro 'lancamento.json')) { throw 'Lançamento já registrado; investigar antes de retomar.' }
Add-Type -TypeDefinition @'
using System.Runtime.InteropServices;
public static class VigiliaFechamentoRamos {
    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern uint SetThreadExecutionState(uint flags);
}
'@
$vigilia = [VigiliaFechamentoRamos]::SetThreadExecutionState([uint32]2147483649)
if ($vigilia -eq 0) { throw 'Falha ao solicitar prevenção temporária de suspensão.' }
try {
    $processoTreino = Start-Process -FilePath 'wsl.exe' -ArgumentList '-d Ubuntu --cd /mnt/c/Users/MuriloRFM/Documents/GitHub/CryptoCasting --exec /home/murilorfm/.venvs/cc/bin/python -B -u -m experimentos.fechamento_ramos_diarios executar' -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $registro 'executor.stdout.log') -RedirectStandardError (Join-Path $registro 'executor.stderr.log')
    @{utc=[DateTime]::UtcNow.ToString('o');pid_windows=$processoTreino.Id;pid_guardiao=$PID;vigilia_solicitada=$true;modo='processo local; sem agendamento ou alteração permanente de energia'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $registro 'lancamento.json') -Encoding utf8
    $processoTreino.WaitForExit()
    $processoTreino.Refresh()
    @{utc=[DateTime]::UtcNow.ToString('o');exit_code=$processoTreino.ExitCode} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $registro 'encerramento_lancador.json') -Encoding utf8
} finally {
    [void][VigiliaFechamentoRamos]::SetThreadExecutionState([uint32]2147483648)
}
