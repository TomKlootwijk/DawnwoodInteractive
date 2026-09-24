from pathlib import Path
import io
import json
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
stream=io.StringIO()
suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
text=stream.getvalue()
(ROOT/'results').mkdir(exist_ok=True)
(ROOT/'results/test_report.txt').write_text(text,encoding='utf-8')
summary={'suite':'unified symbolic workbench','tests_run':result.testsRun,
         'failures':len(result.failures),'errors':len(result.errors),
         'successful':result.wasSuccessful()}
(ROOT/'results/test_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(text)
raise SystemExit(0 if result.wasSuccessful() else 1)
