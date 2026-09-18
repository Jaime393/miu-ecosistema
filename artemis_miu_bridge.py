# MIU v11.4 Bridge — Flash = router darwiniano, Pro = brainstem 12 nodos
import asyncio
from artemis_client import ArtemisClient

async def miu_flash_task():
    client = ArtemisClient("http://localhost:8000", default_profile="flash")
    result = await client.run(
        "Open Settings, go to Battery, verify battery percentage, check for crash dialogs. "
        "Then open Chrome, go to https://fran-oraculo-miu.jaimepvicente.workers.dev/miu/global and verify phi_global 9158.79"
    )
    print(f"Flash Φ_ruta: {result.succeeded} trace {result.trace_id}")

async def miu_pro_plan():
    client = ArtemisClient("http://localhost:8000", default_profile="pro")
    result = await client.run(
        "Build APK from current miu-ecosistema, install on device, open login screen with test account, "
        "verify no unexpected popups after login, return screenshots final page + Logcat"
    )
    print(f"Pro plan: {result.status}")

if __name__ == "__main__":
    asyncio.run(miu_flash_task())
