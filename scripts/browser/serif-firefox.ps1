$ErrorActionPreference='Stop'
$root=__ROOT__
$profile=Join-Path $root 'profile'
New-Item -ItemType Directory $profile|Out-Null
$listener=[Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,0);$listener.Start();$port=$listener.LocalEndpoint.Port;$listener.Stop()
[IO.File]::WriteAllText((Join-Path $profile 'user.js'),('user_pref("marionette.port", '+$port+');'))
$p=Start-Process -FilePath __BINARY__ -ArgumentList @('--headless','--no-remote','--marionette','--profile',('"'+$profile+'"'),'about:blank') -PassThru -RedirectStandardOutput (Join-Path $root 'stdout.txt') -RedirectStandardError (Join-Path $root 'stderr.txt')
$script:id=0
function Read-Frame {
 $digits=''
 while($true){$b=$stream.ReadByte();if($b -lt 0){throw 'Firefox socket closed'};if($b -eq 58){break};$digits += [char]$b}
 $buf=[byte[]]::new([int]$digits);$offset=0
 while($offset -lt $buf.Length){$n=$stream.Read($buf,$offset,$buf.Length-$offset);if(!$n){throw 'Firefox socket closed'};$offset+=$n}
 return ([Text.Encoding]::UTF8.GetString($buf)|ConvertFrom-Json)
}
function Call-M($name,$params=@{}) {
 $script:id++
 $json=ConvertTo-Json -InputObject @(0,$script:id,$name,$params) -Depth 70 -Compress
 $bytes=[Text.Encoding]::UTF8.GetBytes($json);$prefix=[Text.Encoding]::ASCII.GetBytes(($bytes.Length.ToString()+':'))
 $stream.Write($prefix,0,$prefix.Length);$stream.Write($bytes,0,$bytes.Length)
 $reply=Read-Frame
 if($reply[2]){throw ($reply[2]|ConvertTo-Json -Compress)}
 return $reply[3]
}
try{
 for($i=0;$i -lt 60;$i++){
  try{$client=[Net.Sockets.TcpClient]::new();$client.Connect('127.0.0.1',$port);break}catch{$client.Dispose();Start-Sleep -Milliseconds 250}
 }
 $stream=$client.GetStream();$stream.ReadTimeout=200000;$stream.WriteTimeout=10000
 $hello=Read-Frame
 $session=Call-M 'WebDriver:NewSession' @{capabilities=@{alwaysMatch=@{acceptInsecureCerts=$true}}}
 Call-M 'WebDriver:SetWindowRect' @{width=1440;height=1050}|Out-Null
 Call-M 'WebDriver:Navigate' @{url=__PAGE__}|Out-Null
 $r=Call-M 'WebDriver:ExecuteAsyncScript' @{script=__CHECK__;args=@();newSandbox=$true;sandbox=$null;scriptTimeout=180000}
 if($r.value.failure){throw $r.value.failure}
 $report=@{version=$session.capabilities.browserVersion;result=$r.value}
 $report|ConvertTo-Json -Depth 20|Set-Content -Encoding UTF8 (Join-Path $root 'report.json')
 Call-M 'WebDriver:DeleteSession'|Out-Null
}finally{
 if($client){$client.Dispose()}
 $all=Get-CimInstance Win32_Process
 $owned=@($all|Where-Object {$_.CommandLine -and $_.CommandLine.Contains($profile)}|ForEach-Object {$_.ProcessId})
 do{$more=@($all|Where-Object {$owned -contains $_.ParentProcessId -and $owned -notcontains $_.ProcessId}|ForEach-Object {$_.ProcessId});$owned+=$more}while($more.Count)
 foreach($id in $owned){Stop-Process -Id $id -Force -ErrorAction SilentlyContinue}
 foreach($id in $owned){Wait-Process -Id $id -Timeout 10 -ErrorAction SilentlyContinue}
 $left=@(Get-CimInstance Win32_Process|Where-Object {$_.CommandLine -and $_.CommandLine.Contains($profile)})
 if($left.Count){throw 'Test browser processes remain'}
}
