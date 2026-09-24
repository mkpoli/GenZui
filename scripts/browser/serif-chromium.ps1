$ErrorActionPreference='Stop'
$root=__ROOT__
$browser=__BINARY__
$profile=Join-Path $root 'profile'
$active=Join-Path $profile 'DevToolsActivePort'
$p=Start-Process -FilePath $browser -ArgumentList @(__EXTRA__'--headless=new','--no-first-run','--no-default-browser-check','--disable-extensions','--disable-background-networking','--remote-debugging-port=0',('--user-data-dir="'+$profile+'"'),'about:blank') -PassThru -RedirectStandardOutput (Join-Path $root 'stdout.txt') -RedirectStandardError (Join-Path $root 'stderr.txt')
$script:id=0
function Call-CDP($method,$params=@{}){
 $script:id++
 $message=@{id=$script:id;method=$method;params=$params}|ConvertTo-Json -Depth 40 -Compress
 $bytes=[Text.Encoding]::UTF8.GetBytes($message)
 $ws.SendAsync([ArraySegment[byte]]::new($bytes),[Net.WebSockets.WebSocketMessageType]::Text,$true,[Threading.CancellationToken]::None).GetAwaiter().GetResult()|Out-Null
 while($true){
  $stream=[IO.MemoryStream]::new()
  do{
   $buffer=[byte[]]::new(65536)
   $task=$ws.ReceiveAsync([ArraySegment[byte]]::new($buffer),[Threading.CancellationToken]::None)
   if(!$task.Wait(25000)){throw 'CDP receive timeout'}
   $received=$task.Result
   $stream.Write($buffer,0,$received.Count)
  }while(!$received.EndOfMessage)
  $r=([Text.Encoding]::UTF8.GetString($stream.ToArray()))|ConvertFrom-Json
  if($r.id -eq $script:id){if($r.error){throw ($r.error|ConvertTo-Json -Compress)};return $r.result}
 }
}
function Evaluate($source){
 $r=Call-CDP 'Runtime.evaluate' @{expression=$source;returnByValue=$true;awaitPromise=$true}
 if($r.exceptionDetails){throw ($r.exceptionDetails.exception.description)}
 return $r.result.value
}
try{
 for($i=0;$i -lt 30 -and !(Test-Path $active);$i++){Start-Sleep -Milliseconds 500}
 if(!(Test-Path $active)){throw 'No DevTools endpoint'}
 $port=(Get-Content $active)[0]
 $targets=Invoke-RestMethod ('http://127.0.0.1:'+$port+'/json')
 $target=$targets|Where-Object {$_.type -eq 'page'}|Select-Object -First 1
 $ws=[Net.WebSockets.ClientWebSocket]::new()
 $ws.ConnectAsync([Uri]$target.webSocketDebuggerUrl,[Threading.CancellationToken]::None).GetAwaiter().GetResult()|Out-Null
 Call-CDP 'Page.enable'|Out-Null
 Call-CDP 'DOM.enable'|Out-Null
 Call-CDP 'CSS.enable'|Out-Null
 Call-CDP 'Emulation.setDeviceMetricsOverride' @{width=1450;height=1550;deviceScaleFactor=1;mobile=$false}|Out-Null
 Call-CDP 'Page.navigate' @{url=__PAGE__}|Out-Null
 for($i=0;$i -lt 40;$i++){Start-Sleep -Milliseconds 500;if((Evaluate 'document.readyState') -eq 'complete'){break}}
 Evaluate 'Promise.all([...document.fonts].map(f=>f.load())).then(()=>document.fonts.ready).then(()=>true)'|Out-Null
 $report=@{}
 $report.fontFaces=Evaluate '[...document.fonts].map(f=>({family:f.family,weight:f.weight,status:f.status}))'
 $report.fonts=@{}
 $doc=Call-CDP 'DOM.getDocument'
 foreach($probe in (Evaluate '[...document.querySelectorAll("[data-probe]")].map(e=>e.id)')){
  $node=Call-CDP 'DOM.querySelector' @{nodeId=$doc.root.nodeId;selector=('#'+$probe)}
  $report.fonts[$probe]=@((Call-CDP 'CSS.getPlatformFontsForNode' @{nodeId=$node.nodeId}).fonts)
 }
 $report.version=(Call-CDP 'Browser.getVersion').product
 $report|ConvertTo-Json -Depth 15|Set-Content -Encoding UTF8 (Join-Path $root 'report.json')
 $shot=Call-CDP 'Page.captureScreenshot' @{format='png'}
 [IO.File]::WriteAllBytes((Join-Path $root 'proof.png'),[Convert]::FromBase64String($shot.data))
 Call-CDP 'Browser.close'|Out-Null
}finally{
 if($ws){$ws.Dispose()}
 $all=Get-CimInstance Win32_Process
 $owned=@($all|Where-Object {$_.CommandLine -and $_.CommandLine.Contains($profile)}|ForEach-Object {$_.ProcessId})
 do{$more=@($all|Where-Object {$owned -contains $_.ParentProcessId -and $owned -notcontains $_.ProcessId}|ForEach-Object {$_.ProcessId});$owned+=$more}while($more.Count)
 foreach($id in $owned){Stop-Process -Id $id -Force -ErrorAction SilentlyContinue}
 foreach($id in $owned){Wait-Process -Id $id -Timeout 10 -ErrorAction SilentlyContinue}
 $left=@(Get-CimInstance Win32_Process|Where-Object {$_.CommandLine -and $_.CommandLine.Contains($profile)})
 if($left.Count){throw 'Test browser processes remain'}
}
