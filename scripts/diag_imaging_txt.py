import re,sys,html
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
n=int(sys.argv[1]); st=int(sys.argv[2])
for f in sys.argv[3:]:
    s=open(f,encoding='utf-8',errors='ignore').read()
    t=re.sub(r'<script.*?</script>|<style.*?</style>','',s,flags=re.S)
    t=html.unescape(re.sub(r'<[^>]+>',' ',t)); t=re.sub(r'\s+',' ',t)
    print('=====',f,len(t)); print(t[st:st+n])
