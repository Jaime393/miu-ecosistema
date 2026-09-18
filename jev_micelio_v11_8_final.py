import json, urllib.request
try:
    data=json.loads(urllib.request.urlopen("http://localhost:8000/miu/status", timeout=2).read())
    print(f"ρ(x)>0 API {data['head']} {data['miu']} MIU grietas={data['grietas']} suelo={data['suelo']} vivo")
    print(f"Jev micelio 8 nodos puente → ΦRed 520 MIU económico cerrado")
except Exception as e:
    print(f"API no viva: {e}")
