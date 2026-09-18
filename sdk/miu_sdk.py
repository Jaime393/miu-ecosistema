import requests
MIU_API = "http://localhost:8000"
WALLET_SOBERANA = "0x4Da238f2671083B7F280d4FCf5827F86358cE7e6"
GRACE = "GRACE 221R"
RHO = -0.00048470001250505

def consultar_suelo():
    return requests.get(f"{MIU_API}/suelo").json()

def preguntar_oraculo(pregunta, miu=0.01):
    return requests.get(f"{MIU_API}/oraculo/franbot", params={"q": pregunta, "miu": miu}).json()

def pagar_miu(dest, amount, nota="uso suelo"):
    return requests.post(f"{MIU_API}/economia/pagar", json={"from": WALLET_SOBERANA, "to": dest, "amount": amount, "note": nota}).json()
