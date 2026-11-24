$ErrorActionPreference = 'Stop'
$raizProjeto = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$registro = Join-Path $raizProjeto 'registros/generalizacao_moedas'
Set-Location -LiteralPath $raizProjeto
Add-Type -TypeDefinition @'
using System.Runtime.InteropServices;
public static class VigiliaTreino {
    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern uint SetThreadExecutionState(uint flags);
}
'@
# Mantém o sistema acordado somente durante este processo; não altera plano de energia.
$vigilia = [VigiliaTreino]::SetThreadExecutionState([uint32]2147483649)
if ($vigilia -eq 0) { throw 'Não foi possível solicitar prevenção temporária de suspensão.' }
try {
    $p = Start-Process -FilePath 'wsl.exe' -ArgumentList '-d Ubuntu --cd /mnt/c/Users/MuriloRFM/Documents/GitHub/CryptoCasting --exec /home/murilorfm/.venvs/cc/bin/python -B -u -m experimentos.generalizacao_moedas executar' -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $registro 'executor.stdout.log') -RedirectStandardError (Join-Path $registro 'executor.stderr.log')
    @{utc=[DateTime]::UtcNow.ToString('o');pid_windows=$p.Id;pid_guardiao=$PID;vigilia_solicitada=$true;modo='processo local; sem tarefa agendada; sem alteração permanente de energia'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $registro 'lancamento.json') -Encoding utf8
    $p.WaitForExit()
    $p.Refresh()
    @{utc=[DateTime]::UtcNow.ToString('o');exit_code=$p.ExitCode} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $registro 'encerramento_lancador.json') -Encoding utf8
} finally {
    [void][VigiliaTreino]::SetThreadExecutionState([uint32]2147483648)
}
