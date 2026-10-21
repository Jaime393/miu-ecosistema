import json, re, requests, sys

# Busca código de verificación N8n en Gmail vía Zapier MCP
# Uso: python3 buscar_codigo.py $ZAPIER_URL
# Escribe código encontrado a /root/codigo_n8n.txt

ZAPIER_URL = sys.argv[1] if len(sys.argv) > 1 else ''

def buscar_codigo():
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "execute_zapier_read_action",
            "arguments": {
                "selected_api": "GoogleMailV2CLIAPI",
                "action": "search",
                "params": {"query": "newer_than:10m (from:n8n OR subject:(verify OR verification OR código OR code OR confirma OR n8n))"}
            }
        },
        "id": 1
    }
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    r = requests.post(ZAPIER_URL, json=payload, headers=headers, timeout=20)
    emails = []
    for line in r.text.split('\n'):
        if line.startswith('data: '):
            try:
                d = json.loads(line[6:])
                if 'result' in d:
                    c = d['result'].get('content', [])
                    if c and c[0].get('type') == 'text':
                        try: data = json.loads(c[0]['text']); emails = data.get('results', [])
                        except: pass
            except: pass
    print(f"Emails encontrados: {len(emails)}")
    for em in emails:
        raw = em.get('raw', {}); payload_ = raw.get('payload', {}); hdrs = payload_.get('headers', {})
        delivered_to = hdrs.get('Delivered-To', '').strip().lower()
        subject = hdrs.get('Subject', ''); snippet = em.get('snippet', '')
        print(f"\n  To: {delivered_to}\n  Subject: {subject[:100]}\n  Snippet: {snippet[:200]}")
        match = re.search(r'\b(\d{6})\b', subject + ' ' + snippet)
        if match:
            print(f"  → CÓDIGO: {match.group(1)}")
            return match.group(1), delivered_to, subject
    return None, None, None

if __name__ == '__main__':
    if not ZAPIER_URL:
        import subprocess
        result = subprocess.run(['grep', '-hEo', r'https://mcp\.zapier\.com/api/v1/connect\?token=[A-Za-z0-9=]+',
                                 '/data/data/com.termux/files/home/storage/shared/Download/claves.txt'],
                                capture_output=True, text=True)
        ZAPIER_URL = result.stdout.strip().split('\n')[0] if result.stdout.strip() else ''
    if not ZAPIER_URL: print("ERROR: ZAPIER_URL vacío"); sys.exit(1)
    print(f"Buscando en {ZAPIER_URL[:40]}...")
    codigo, to, subject = buscar_codigo()
    if codigo:
        print(f"\n✅ CÓDIGO ENCONTRADO: {codigo}\n   De: {to}\n   Subject: {subject[:80]}")
        with open('/root/codigo_n8n.txt', 'w') as f: f.write(codigo)
    else: print("\n❌ No se encontró código"); sys.exit(2)
