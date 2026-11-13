"""Run the downloaded program independently with networking disabled by the caller."""
import csv,hashlib,json,pathlib,subprocess,sys,tempfile
root=pathlib.Path('/tmp/downloads');sample='month,amount,label\n2026-01,19.90,"North, launch"\n2026-01,10.10,中文客户\n2026-02,2.50,Renewal\n2026-02,7.50,Support\n'
expected=[{'month':'2026-01','total':'30.00'},{'month':'2026-02','total':'10.00'}]
with tempfile.TemporaryDirectory(prefix='abx-independent-') as temporary:
 work=pathlib.Path(temporary);source=work/'sales.csv';source.write_text(sample)
 for turn in ('first','final'):
  program=root/turn/'aggregate.py';target=work/(turn+'.csv')
  subprocess.run([sys.executable,'-I',str(program),str(source),str(target)],check=True,capture_output=True,timeout=15)
  assert list(csv.DictReader(target.open()))==expected
  assert list(csv.DictReader((root/turn/'summary.csv').open()))==expected
 target=work/'shares.csv'
 subprocess.run([sys.executable,'-I',str(root/'final/aggregate.py'),str(source),str(target),'--with-share'],check=True,capture_output=True,timeout=15)
 shares=[{**expected[0],'share':'0.7500'},{**expected[1],'share':'0.2500'}]
 assert list(csv.DictReader(target.open()))==shares
 assert list(csv.DictReader((root/'final/shares.csv').open()))==shares
 continuity=json.loads((root/'final/continuity.json').read_text())
 assert continuity=={'first_summary_sha256':hashlib.sha256((root/'first/summary.csv').read_bytes()).hexdigest(),'monthly_total_sum':'40.00'}
 assert (root/'first/summary.csv').read_bytes()==(root/'final/summary.csv').read_bytes()
print(json.dumps({'downloadedCodeIndependentlyRun':True,'firstTotals':['30.00','10.00'],'secondShares':['0.7500','0.2500'],'secondTurnReadsFirstArtifact':True,'network':'none'}))
