import ast, asyncio, os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
source=(Path(__file__).resolve().parents[1]/'web_identity.py').read_text()
config=next(n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.AsyncFunctionDef) and n.name=='config')
config.decorator_list=[]
async def run():
 for mode,expected in [('true',True),('false',False),('OFF',False),('1',True)]:
  os.environ['WEB_EARLY_ACCESS']=mode
  for state in ['empty','available','error']:
   bindings=SimpleNamespace(distinct=AsyncMock(return_value=['safe-id']))
   published=SimpleNamespace(find_one=AsyncMock(return_value={'_id':'safe'} if state=='available' else None))
   if state=='error':bindings.distinct.side_effect=RuntimeError('database unavailable')
   env={'os':os,'db':SimpleNamespace(web_operation_bindings=bindings,presentation_web_published=published),'enabled':lambda:True,'mail_ready':lambda:True,'registration_ready':lambda:True}
   exec(compile(ast.Module(body=[config],type_ignores=[]),'<config>','exec'),env)
   r=await env['config']();assert r['early_access'] is expected;assert r['catalog_state']==state;assert r['identity_enabled'] and r['registration_enabled']
   if state!='error':assert bindings.distinct.call_args.args[1]=={'publication_approved':True,'catalog_reference_safe':True}
 print('12 configuration/catalogue combinations passed; auth/registration preserved')
def test_launch_states():
 asyncio.run(run())
