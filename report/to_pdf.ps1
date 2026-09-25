param([string]$in, [string]$out)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open($in, $false, $true)
$doc.Fields.Update() | Out-Null
foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
$doc.SaveAs([ref]$out, [ref]17)
$doc.Close([ref]0)
$word.Quit()
