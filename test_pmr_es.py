import sys
sys.path.insert(0, r'c:\Users\ruancanling\Desktop\ERP VIBE CODING\site-packages')
from py_mini_racer import MiniRacer
ctx = MiniRacer()
tests = [
    ('var + object', "var a = 1; var b = {x: 1}; a + b.x;"),
    ('const (ES6)', "const a = 1; const b = {x: 2}; a + b.x;"),
    ('let (ES6)',   "let a = 1; a + 2;"),
    ('arrow fn',    "var f = x => x+1; f(5);"),
    ('async fn',    "(async function(){ return 42; })().then(r=>r);"),
    ('template lit',"var x = 1; var s = 'x=' + x; s;"),
    ('default param',"function f(a=1){return a;} f();"),
    ('destructuring',"var {a,b} = {a:1,b:2}; a + b;"),
]
for name, code in tests:
    try:
        r = ctx.eval(code)
        print(f"  {name}: PASS -> {r}")
    except Exception as e:
        print(f"  {name}: FAIL -> {str(e)[:150]}")
